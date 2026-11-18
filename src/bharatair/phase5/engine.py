"""Synthetic-testable Phase 5 fit primitives. Never constructs a test partition."""
from __future__ import annotations
import io, json, random, time, logging
from dataclasses import dataclass
from typing import Any
import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from torch import nn
from torch.utils.data import DataLoader,TensorDataset
from bharatair.features.scaling import TrainOnlyScaler
from bharatair.features.windows import calendar_features
from bharatair.models.classical import make_classical_model
from bharatair.models.neural import NEURAL_CONFIGS,build_neural_model,predict_neural
from bharatair.phase5.runner import HORIZONS,LOOKBACKS,MIN_POOLED_TRAIN,MIN_POOLED_VALIDATION,MIN_TRAIN,MIN_VALIDATION,StationAwareScaler,begin_cuda_telemetry,finish_cuda_telemetry,assert_unseen_station_fold
LOG=logging.getLogger(__name__)

@dataclass
class StationTimeline:
    station_id:str; city:str; timestamps:pd.DatetimeIndex; values:np.ndarray; observed:np.ndarray
    train_end:pd.Timestamp; validation_end:pd.Timestamp; mase_scale:float=1.0


def prepare_timelines(panel:pd.DataFrame,station_meta:pd.DataFrame)->dict[str,StationTimeline]:
    """Hourly arrays use only rows already filtered before each station's test cutoff."""
    timelines={}
    for meta in station_meta.itertuples():
        part=panel[panel.station_id.eq(meta.station_id)].sort_values('collected_at',kind='mergesort')
        if part.empty: continue
        if part.collected_at.duplicated().any(): raise ValueError(f'Duplicate timestamp in {meta.station_id}')
        if part.collected_at.dt.tz is not None: raise ValueError('Expected naive IST')
        start=part.collected_at.iloc[0]; end=pd.Timestamp(meta.city_split_test_start_ist)-pd.Timedelta(hours=1)
        if end<start: continue
        calendar=pd.date_range(start,end,freq='h'); vals=np.full(len(calendar),np.nan,dtype=np.float64)
        offsets=((part.collected_at-start)/pd.Timedelta(hours=1)).astype(int).to_numpy(); valid=offsets<len(calendar)
        vals[offsets[valid]]=part.value.to_numpy(dtype=np.float64)[valid]
        train_end=pd.Timestamp(meta.city_split_validation_start_ist)
        observed=np.isfinite(vals); eligible=np.flatnonzero(observed & (calendar < train_end))
        adjacent=eligible[1:][np.diff(eligible)==1]
        diffs=np.abs(vals[adjacent]-vals[adjacent-1]); mase=float(diffs.mean()) if len(diffs) and diffs.mean()>0 else 1.0
        timelines[str(meta.station_id)]=StationTimeline(str(meta.station_id),str(meta.city),calendar,vals,observed,
            train_end,pd.Timestamp(meta.city_split_test_start_ist),mase)
    return timelines


def build_examples(series:StationTimeline,lookback:int,horizon:int)->dict[str,dict[str,np.ndarray]]:
    """Issue and target share train/validation split; input is causal and gap-free."""
    if lookback not in (24,48,168) or horizon not in (1,6,12,24): raise ValueError('Outside frozen grid')
    rows={'train':[],'validation':[]}; n=len(series.timestamps)
    for issue in range(lookback-1,max(lookback-1,n-horizon)):
        target=issue+horizon; it=series.timestamps[issue]; tt=series.timestamps[target]
        split='train' if it<series.train_end else ('validation' if it<series.validation_end else 'test')
        if split=='test': continue
        if (split=='train' and tt>=series.train_end) or (split=='validation' and tt>=series.validation_end): continue
        if not series.observed[issue-lookback+1:target+1].all(): continue
        rows[split].append((issue,series.values[issue-lookback+1:issue+1],series.values[target]))
    out={}
    for name,items in rows.items():
        idx=np.asarray([r[0] for r in items],dtype=np.int64)
        out[name]={'issue_index':idx,'sequences':np.asarray([r[1] for r in items],dtype=np.float32).reshape(-1,lookback),
            'targets':np.asarray([r[2] for r in items],dtype=np.float32),
            'issue_timestamp':series.timestamps[idx].to_numpy(dtype='datetime64[ns]'),
            'target_timestamp':series.timestamps[idx+horizon].to_numpy(dtype='datetime64[ns]'),
            'calendar':calendar_features(series.timestamps[idx]),'mase_scale':np.full(len(idx),series.mase_scale,dtype=np.float64)}
    return out


def exact_common_validation(index_by_lookback:dict[int,dict[str,np.ndarray]])->pd.DatetimeIndex:
    sets=[pd.DatetimeIndex(index_by_lookback[l]['validation']['issue_timestamp']) for l in (24,48,168)]
    common=sets[0]
    for idx in sets[1:]: common=common.intersection(idx,sort=False)
    return common.sort_values()


def select_issues(examples:dict[str,np.ndarray],issues:pd.DatetimeIndex)->dict[str,np.ndarray]:
    mask=pd.DatetimeIndex(examples['issue_timestamp']).isin(issues)
    return {k:v[mask] for k,v in examples.items()}

class PooledNet(nn.Module):
    """Use the unchanged Phase 3 temporal encoder plus a learned station embedding."""
    def __init__(self,name:str,lookback:int,n_stations:int,embedding_size:int=8):
        super().__init__(); self.base=build_neural_model(name,lookback)
        self.embedding=nn.Embedding(n_stations+1,embedding_size); self.identity=nn.Sequential(nn.Linear(embedding_size,16),nn.ReLU(),nn.Linear(16,1))
        nn.init.zeros_(self.identity[-1].weight); nn.init.zeros_(self.identity[-1].bias)
    def forward(self,x,cal,station_code): return self.base(x,cal)+self.identity(self.embedding(station_code)).squeeze(-1)


def _scale(train_x,train_y,train_ids,val_x,val_y,val_ids,variant):
    if variant=='station_aware':
        scaler=StationAwareScaler.fit(train_x,train_y,train_ids)
        return scaler,scaler.transform_x(train_x,train_ids),scaler.transform_y(train_y,train_ids),scaler.transform_x(val_x,val_ids),scaler.transform_y(val_y,val_ids)
    scaler=TrainOnlyScaler().fit(train_x,train_y)
    return scaler,scaler.transform_x(train_x),scaler.transform_y(train_y),scaler.transform_x(val_x),scaler.transform_y(val_y)


def fit_candidate(model_name:str,lookback:int,horizon:int,train:dict[str,Any],validation:dict[str,Any],*,
                  seed:int,device:str,normalization:str='global',identity:bool=False,unseen_station:str|None=None,
                  candidate_id:str|None=None)->dict[str,Any]:
    """Fit one candidate. All arguments must already be train/validation-only arrays."""
    if not len(train['targets']) or not len(validation['targets']): raise ValueError('Insufficient train or validation examples')
    train_ids=np.asarray(train['station_ids']).astype(str); val_ids=np.asarray(validation['station_ids']).astype(str)
    if unseen_station: assert_unseen_station_fold(train_ids,unseen_station)
    if unseen_station and np.isin(val_ids,train_ids).any():
        if not np.all(val_ids==unseen_station): raise ValueError('C validation cohort contains peer stations')
    family='deep_learning' if model_name in ('lstm','gru','tcn') else 'traditional_ml'
    if family=='traditional_ml' and not identity:
        scaler=None; tx=train['sequences']; ty=train['targets']; vx=validation['sequences']; vy=validation['targets']
    else:
        scaler,tx,ty,vx,vy=_scale(train['sequences'],train['targets'],train_ids,validation['sequences'],validation['targets'],val_ids,normalization)
    telemetry_id=candidate_id or f'{model_name}-L{lookback}-H{horizon}'
    telemetry_state=begin_cuda_telemetry(telemetry_id,device if family=='deep_learning' else 'cpu')
    started=time.perf_counter(); codes={str(s):i+1 for i,s in enumerate(sorted(set(train_ids)))}
    if family=='traditional_ml':
        def tabular(x,cal,ids):
            cats=np.eye(len(codes)+1,dtype=np.float32)[np.array([codes.get(s,0) for s in ids])] if identity else np.empty((len(ids),0),np.float32)
            return np.column_stack([x[:,::-1],cal,cats])
        estimator=make_classical_model(model_name,seed,device=device if len(train['targets'])>=50000 else 'cpu')
        estimator.fit(tabular(tx,train['calendar'],train_ids),ty)
        training_seconds=time.perf_counter()-started; prediction_started=time.perf_counter()
        pred_scaled=estimator.predict(tabular(vx,validation['calendar'],val_ids)); prediction_seconds=time.perf_counter()-prediction_started
        if isinstance(scaler,StationAwareScaler): pred=scaler.inverse_y(pred_scaled,val_ids)
        elif scaler is not None: pred=scaler.inverse_y(pred_scaled)
        else: pred=np.asarray(pred_scaled,dtype=np.float64)
        buff=io.BytesIO(); joblib.dump(estimator,buff,compress=3); checkpoint=buff.getvalue()
        metadata={'feature_station_vocabulary':codes if identity else None,'scaler':scaler.state() if hasattr(scaler,'state') else (vars(scaler) if scaler is not None else None)}
    else:
        config=NEURAL_CONFIGS[model_name]; torch.manual_seed(seed); np.random.seed(seed); random.seed(seed)
        train_codes=np.asarray([codes.get(s,0) for s in train_ids],dtype=np.int64)
        val_codes=np.asarray([codes.get(s,0) for s in val_ids],dtype=np.int64)
        use_identity=identity and unseen_station is None
        is_cuda=(device=='cuda') and torch.cuda.is_available()
        ds=TensorDataset(torch.from_numpy(tx[...,None]),torch.from_numpy(train['calendar']),torch.from_numpy(ty),torch.from_numpy(train_codes))
        loader=DataLoader(ds,batch_size=config['batch_size'],shuffle=True,generator=torch.Generator().manual_seed(seed),num_workers=0,pin_memory=is_cuda)
        model=PooledNet(model_name,lookback,len(codes)) if use_identity else build_neural_model(model_name,lookback)
        model=model.to(device); opt=torch.optim.Adam(model.parameters(),lr=config['learning_rate']); lossfn=nn.MSELoss()
        val_bsz=2048
        def _eval_model(m):
            preds=[]
            m.eval()
            with torch.no_grad():
                for start in range(0,len(vx),val_bsz):
                    end=start+val_bsz
                    sbx=torch.from_numpy(vx[start:end,...,None]).to(device,non_blocking=is_cuda)
                    sbc=torch.from_numpy(validation['calendar'][start:end]).to(device,non_blocking=is_cuda)
                    if use_identity:
                        sbid=torch.from_numpy(val_codes[start:end]).to(device,non_blocking=is_cuda)
                        out=m(sbx,sbc,sbid)
                    else:
                        out=m(sbx,sbc)
                    preds.append(out.cpu())
            return torch.cat(preds,dim=0) if preds else torch.empty(0)
        vy_cpu=torch.as_tensor(vy,dtype=torch.float32)
        best=None; bestloss=float('inf'); best_epoch=0; stale=0; hist=[]; valhist=[]
        for epoch in range(1,int(config['max_epochs'])+1):
            model.train(); loss_sum=0.; n=0
            for bx,bc,by,bid in loader:
                bx,bc,by,bid=bx.to(device,non_blocking=is_cuda),bc.to(device,non_blocking=is_cuda),by.to(device,non_blocking=is_cuda),bid.to(device,non_blocking=is_cuda)
                opt.zero_grad(set_to_none=True); output=model(bx,bc,bid) if use_identity else model(bx,bc)
                loss=lossfn(output,by); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
                loss_sum+=float(loss.detach())*len(by); n+=len(by)
            vout=_eval_model(model); vloss=float(lossfn(vout,vy_cpu))
            hist.append(loss_sum/max(n,1)); valhist.append(vloss)
            if vloss<bestloss-1e-7:
                bestloss=vloss; best_epoch=epoch; stale=0; best={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
            else:
                stale+=1
                if stale>=int(config['patience']): break
        if best is None: raise RuntimeError('No finite validation checkpoint produced')
        model.load_state_dict(best); model.eval()
        training_seconds=time.perf_counter()-started; prediction_started=time.perf_counter()
        raw=_eval_model(model).numpy()
        pred=scaler.inverse_y(raw,val_ids) if isinstance(scaler,StationAwareScaler) else scaler.inverse_y(raw)
        prediction_seconds=time.perf_counter()-prediction_started
        if is_cuda: torch.cuda.empty_cache()
        buff=io.BytesIO(); torch.save({'state_dict':model.state_dict(),'model':model_name,'lookback':lookback,'identity':use_identity,'station_vocabulary':codes if use_identity else None,'scaler':scaler.state() if hasattr(scaler,'state') else vars(scaler)},buff)
        checkpoint=buff.getvalue(); metadata={'identity':use_identity,'best_epoch':best_epoch,'training_loss_history':hist,'validation_loss_history':valhist,'scaler':scaler.state() if hasattr(scaler,'state') else vars(scaler),'station_vocabulary':codes if use_identity else None}
    actual=np.asarray(validation['targets'],dtype=float); pred=np.asarray(pred,dtype=float)
    if not np.isfinite(pred).all(): raise RuntimeError('Candidate generated non-finite validation predictions')
    scales=np.asarray(validation.get('mase_scale',np.ones(len(actual))),dtype=np.float64)
    if len(scales)!=len(actual) or not np.isfinite(scales).all() or (scales<=0).any(): raise ValueError('Invalid training-only MASE scale')
    error=pred-actual
    metrics={'n':len(actual),'mae':float(mean_absolute_error(actual,pred)),'rmse':float(np.sqrt(mean_squared_error(actual,pred))),
             'mase':float(np.mean(np.abs(error)/scales)),'bias':float(np.mean(error)),
             'training_seconds':training_seconds,'prediction_seconds':prediction_seconds,'fit_seconds':training_seconds,
             'cuda_memory_telemetry':finish_cuda_telemetry(telemetry_state,telemetry_id)}
    predictions=pd.DataFrame({'station_id':val_ids,'issue_timestamp':validation['issue_timestamp'],'target_timestamp':validation['target_timestamp'],'actual':actual,'predicted':pred,'mase_scale':scales})
    return {'metrics':metrics,'predictions':predictions,'checkpoint_bytes':checkpoint,'metadata':metadata,'family':family}


def _join_examples(parts:list[tuple[str,dict[str,np.ndarray]]])->dict[str,np.ndarray]:
    if not parts: raise ValueError('No example arrays')
    keys=('sequences','targets','calendar','issue_timestamp','target_timestamp','mase_scale')
    joined={key:np.concatenate([p[key] for _,p in parts],axis=0) for key in keys}
    joined['station_ids']=np.concatenate([np.full(len(p['targets']),sid,dtype=object) for sid,p in parts])
    return joined


def build_candidate_arrays(timelines:dict[str,StationTimeline],lookback:int,horizon:int)->tuple[dict[str,dict[str,dict[str,np.ndarray]]],dict[str,pd.DatetimeIndex]]:
    per_station={}; common={}
    # Exact validation intersection is station-specific across all three lookbacks.
    for sid,series in timelines.items():
        by_lb={lb:{h:build_examples(series,lb,h) for h in HORIZONS} for lb in LOOKBACKS}
        per_station[sid]=by_lb
        for h in HORIZONS:
            sets=[pd.DatetimeIndex(by_lb[lb][h]['validation']['issue_timestamp']) for lb in LOOKBACKS]
            ix=sets[0]
            for other in sets[1:]: ix=ix.intersection(other,sort=False)
            common[f'{sid}|{h}']=ix.sort_values()
    return per_station,common


def _filter_issue_arrays(examples:dict[str,np.ndarray],times:pd.DatetimeIndex)->dict[str,np.ndarray]:
    mask=pd.DatetimeIndex(examples['issue_timestamp']).isin(times)
    return {key:value[mask] for key,value in examples.items()}


def _matched_baseline_metrics(predictions: pd.DataFrame, timelines: dict[str, StationTimeline],
                              candidate_id: str, lookback: int, horizon: int) -> list[dict[str, Any]]:
    """Compare a candidate with baselines only on its exact validation issue/target pairs."""
    rows=[]
    for sid,g in predictions.groupby('station_id',sort=False):
        series=timelines[str(sid)]
        issue_idx=series.timestamps.get_indexer(pd.DatetimeIndex(g.issue_timestamp))
        target_idx=series.timestamps.get_indexer(pd.DatetimeIndex(g.target_timestamp))
        actual=g.actual.to_numpy(dtype=float); model_pred=g.predicted.to_numpy(dtype=float)
        refs={'persistence':issue_idx,'seasonal_naive':issue_idx-24}
        for baseline,ref_idx in refs.items():
            valid=(issue_idx>=0)&(target_idx>=0)&(ref_idx>=0)&(ref_idx<len(series.values))
            positions=np.flatnonzero(valid)
            if len(positions): valid[positions]&=np.isfinite(series.values[ref_idx[positions]])
            if not valid.any(): continue
            y=actual[valid]; mp=model_pred[valid]; bp=series.values[ref_idx[valid]]
            me=mp-y; be=bp-y; n=len(y)
            rows.append({'candidate_id':candidate_id,'station_id':str(sid),'model':g.model.iloc[0],
                'horizon_hours':horizon,'lookback_hours':lookback,'baseline_model':baseline,'n':n,
                'model_mae':float(np.abs(me).mean()),'baseline_mae':float(np.abs(be).mean()),
                'model_rmse':float(np.sqrt(np.mean(me**2))),'baseline_rmse':float(np.sqrt(np.mean(be**2))),
                'model_mase':float(np.mean(np.abs(me)/g.mase_scale.to_numpy(dtype=float)[valid])),
                'baseline_mase':float(np.mean(np.abs(be)/g.mase_scale.to_numpy(dtype=float)[valid])),
                'absolute_mae_improvement':float(np.abs(be).mean()-np.abs(me).mean()),
                'percentage_mae_improvement':float(100*(np.abs(be).mean()-np.abs(me).mean())/np.abs(be).mean()) if np.abs(be).mean() else None,
                'absolute_rmse_improvement':float(np.sqrt(np.mean(be**2))-np.sqrt(np.mean(me**2)))})
    return rows


def _write_experiment_summaries(out, results_df: pd.DataFrame, meta: pd.DataFrame,
                                runtime: dict[str, Any], baseline_comparisons: list[dict[str, Any]]) -> dict[str, str]:
    """Build compact summaries from candidate-level metrics; never concatenate all prediction files."""
    from bharatair.experiments.artifacts import atomic_csv, atomic_json, file_sha256
    metrics_dir=out/'metrics'; metrics_dir.mkdir(exist_ok=True)
    done=results_df[results_df.status.isin(['complete','reused_verified']) & results_df.eligible_for_selection.fillna(False)].copy()
    if 'station_id' not in done.columns: done['station_id']=done.unit_id
    meta_cols=meta[[c for c in ('station_id','city','state','eligibility_tier','operator') if c in meta.columns]].drop_duplicates('station_id').set_index('station_id')
    for col in ('city','state','eligibility_tier','operator'):
        done[col]=done.unit_id.map(meta_cols[col]) if col in meta_cols else None
    family_map={'linear_regression':'traditional_ml','random_forest':'traditional_ml','xgboost':'traditional_ml',
                'lstm':'deep_learning','gru':'deep_learning','tcn':'deep_learning'}
    done['family']=done.model.map(family_map)
    atomic_csv(metrics_dir/'station_level.csv',done)
    reports={}
    def summarize(keys, scope):
        rows=[]
        for key,g in done.groupby(keys,dropna=False):
            vals=key if isinstance(key,tuple) else (key,); row={'scope':scope,**dict(zip(keys,vals))}
            n=g.n.astype(float); denom=float(n.sum())
            row.update({'n_candidates':len(g),'n_stations':int(g.station_id.nunique()),'n_observations':int(denom),
                'median_station_mae':float(g.mae.median()),'median_station_rmse':float(g.rmse.median()),
                'observation_weighted_mae':float(np.average(g.mae,weights=n)),
                'observation_weighted_rmse':float(np.sqrt(np.average(g.rmse.pow(2),weights=n))),
                'observation_weighted_mase':float(np.average(g.mase,weights=n)),
                'observation_weighted_bias':float(np.average(g.bias,weights=n)),
                'training_seconds':float(g.training_seconds.sum()),'prediction_seconds':float(g.prediction_seconds.sum())})
            rows.append(row)
        return pd.DataFrame(rows)
    common=['model','family','horizon_hours','lookback_hours']
    reports['city_tier_summaries']=summarize(['city','eligibility_tier']+common,'city_tier')
    reports['model_family_comparisons']=summarize(['family','horizon_hours','lookback_hours'],'family')
    reports['per_horizon_comparisons']=summarize(['model','family','horizon_hours','lookback_hours'],'horizon')
    reports['per_lookback_comparisons']=summarize(['model','family','lookback_hours','horizon_hours'],'lookback')
    reports['overall_model_comparisons']=summarize(common,'overall')
    for name,frame in reports.items(): atomic_csv(metrics_dir/f'{name}.csv',frame)
    atomic_csv(metrics_dir/'city_tier_overall.csv',reports['city_tier_summaries'])
    baseline=pd.DataFrame(baseline_comparisons)
    if not baseline.empty:
        baseline['city']=baseline.station_id.map(meta_cols.city)
        baseline['eligibility_tier']=baseline.station_id.map(meta_cols.eligibility_tier)
    atomic_csv(metrics_dir/'matched_baseline_comparisons.csv',baseline)
    resource_cols=[c for c in ('candidate_id','status','unit_id','model','lookback_hours','horizon_hours','training_seconds','prediction_seconds','cuda_memory_telemetry') if c in results_df]
    atomic_csv(metrics_dir/'runtime_cuda_memory.csv',results_df[resource_cols])
    hashes={p.stem:file_sha256(p) for p in metrics_dir.glob('*.csv')}
    summary={'run_id':out.name,'status':'validation_complete_test_not_evaluated','runtime':runtime,
        'planned_candidate_count':int(len(results_df)),'completed_candidate_count':int((results_df.status=='complete').sum()),
        'reused_verified_candidate_count':int((results_df.status=='reused_verified').sum()),
        'failed_candidate_count':int((results_df.status=='failed').sum()),
        'ineligible_candidate_count':int((results_df.status.astype(str).str.startswith('skipped')).sum()),
        'structurally_untrainable_count':int(results_df.get('reason',pd.Series(dtype=str)).astype(str).str.contains('zero_training_windows_structurally_untrainable').sum()),
        'below_floor_count':int(results_df.get('reason',pd.Series(dtype=str)).astype(str).str.contains('below_').sum()),
        'eligible_completed_count':int(len(done)),'test_values_loaded':False,'test_windows_materialized':False,
        'test_predictions_created':False,'test_metrics_created':False,'metrics_artifact_sha256':hashes}
    atomic_json(out/'summary.json',summary)
    winners=pd.read_csv(out/'validation_selection.csv') if (out/'validation_selection.csv').is_file() else pd.DataFrame()
    winner_lines='\n'.join(f"| {r.unit_id} | +{int(r.horizon_hours)}h | {r.model} | L{int(r.lookback_hours)} | MAE {r.validation_mae:.3f} |" for r in winners.itertuples())
    (out/'EXPERIMENT_REPORT.md').write_text(
        f"# Phase 5 Experiment A Validation Report\n\nRun: `{out.name}`\n\n"
        f"Completed fits: {summary['completed_candidate_count']}; failures: {summary['failed_candidate_count']}; "
        f"ineligible/skipped: {summary['ineligible_candidate_count']}.\n\n"
        f"Runtime: `{runtime.get('python_executable')}`; PyTorch {runtime.get('torch_version')}; "
        f"CUDA {runtime.get('cuda_version')}; device {runtime.get('gpu_name')}.\n\n"
        "The test gate remains closed. No test PM2.5 values, test windows, test predictions, or test metrics were accessed or produced.\n\n"
        "## Validation-selected station and horizon candidates\n\n"
        "| Station | Horizon | Model | Lookback | Validation MAE |\n|---|---:|---|---:|---:|\n"+winner_lines+
        "\n\nSee `candidate_results.csv`, `candidate_manifest.csv`, and `metrics/` for the complete ledger and summaries.\n",
        encoding='utf-8')
    return hashes


def execute_validation(*,run_id:str,experiment:str,cohort_name:str,panel:pd.DataFrame,
                       station_meta:pd.DataFrame,feasibility:pd.DataFrame,device:str='cuda',resume:bool=False)->dict[str,Any]:
    """Run the complete approved candidate grid for one experiment/cohort; never tests."""
    from datetime import datetime,timezone
    from bharatair.experiments.artifacts import atomic_bytes,atomic_csv,atomic_json,commit_candidate,file_sha256,fingerprint,validate_manifest,verify_completed_candidate
    from bharatair.phase5.runner import TestDataAccessError,make_candidate_manifest,runtime_metadata
    from bharatair.experiments.artifacts import validate_run_id
    from bharatair.config import PROJECT_ROOT
    run_id=validate_run_id(run_id)
    import os,random
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.cuda.manual_seed_all(42) if torch.cuda.is_available() else None
    torch.use_deterministic_algorithms(True,warn_only=True); torch.set_num_threads(min(4,os.cpu_count() or 1))
    if torch.cuda.is_available(): torch.backends.cudnn.benchmark = True
    if experiment not in ('A','B','C') or cohort_name not in ('primary','pune'): raise ValueError('Invalid experiment/cohort')
    meta=station_meta.copy(); meta=meta[meta.cohort.eq('primary_seven_city_a_b' if cohort_name=='primary' else 'pune_tier_b_sensitivity')]
    required_source={'station_id','collected_at','value'}
    if not required_source.issubset(panel.columns): raise ValueError(f'Missing source fields: {required_source-set(panel.columns)}')
    cutoff_by_station=meta.set_index('station_id').city_split_test_start_ist.map(pd.Timestamp).to_dict()
    limits=panel.station_id.map(cutoff_by_station)
    if limits.isna().any(): raise ValueError('Input panel contains a station outside the frozen cohort')
    if (panel.collected_at.to_numpy() >= limits.to_numpy()).any():
        raise TestDataAccessError('Refusing a panel with timestamps at/after a station test cutoff; use the filtered Parquet loader')
    timelines=prepare_timelines(panel,meta)
    if experiment=='A':
        examples={}; common={}
        for sid,series in timelines.items():
            _,station_common=build_candidate_arrays({sid:series},24,1); common.update(station_common)
    else:
        examples,common=build_candidate_arrays(timelines,24,1)
    current_station_cache=None
    all_defs=make_candidate_manifest(station_meta,feasibility)
    defs=all_defs[(all_defs.experiment==experiment)&(all_defs.cohort==cohort_name)].copy()
    config={'models':list(('linear_regression','random_forest','xgboost','lstm','gru','tcn')),'lookbacks':[24,48,168],'horizons':[1,6,12,24],
            'seed':42,'device':device,'validation_only':True,'minimums':{'station_train':5000,'station_validation':1000,'pooled_train':20000,'pooled_validation':2500}}
    data_fp=fingerprint({'rows':len(panel),'stations':sorted(panel.station_id.unique().tolist()),'values_digest':pd.util.hash_pandas_object(panel[['station_id','collected_at','value']],index=False).values.tobytes().hex()})
    splits=meta[['station_id','city_split_validation_start_ist','city_split_test_start_ist']].drop_duplicates().to_dict('records')
    split_fp=fingerprint(splits); prep_fp=fingerprint({'gap_policy':'reject any missing hourly observation in input-through-target','history':'causal through issue time','scaling':'training only'})
    conf_fp=fingerprint(config); out=PROJECT_ROOT/'runs'/run_id
    if out.exists() and not resume: raise FileExistsError(out)
    if not out.exists(): out.mkdir(parents=True,exist_ok=False)
    for sub in ('candidates','failures','logs','ledger'): (out/sub).mkdir(exist_ok=True)
    for handler in list(LOG.handlers):
        if getattr(handler,'_phase5_managed',False):
            LOG.removeHandler(handler); handler.close()
    file_handler=logging.FileHandler(out/'logs'/'experiment.log',mode='a',encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    file_handler._phase5_managed=True
    LOG.addHandler(file_handler)
    manifest={'run_id':run_id,'experiment':experiment,'cohort':cohort_name,'status':'validation_in_progress','config':config,'config_fingerprint':conf_fp,
              'data_fingerprint':data_fp,'split_fingerprint':split_fp,'split_boundaries':splits,'preprocessing_fingerprint':prep_fp,'test_values_loaded':False,
              'test_windows_materialized':False,'test_predictions_created':False,'test_metrics_created':False,'runtime':runtime_metadata(device,42),
              'planned_candidate_count':len(defs),'executed_fit_count':0,'created_at_utc':datetime.now(timezone.utc).isoformat()}
    manifest_path=out/'manifest.json'
    if resume:
        old=json.loads(manifest_path.read_text(encoding='utf-8'))
        if old.get('status')=='validation_complete_test_not_evaluated': raise ValueError('Resume refused: validation run is already complete')
        validate_manifest(old,manifest)
        manifest['created_at_utc']=old['created_at_utc']
    elif manifest_path.exists(): raise FileExistsError('Run manifest already exists')
    atomic_json(manifest_path,manifest)
    atomic_csv(out/'candidate_manifest.csv',defs)
    candidate_rows=[]; completed=0; failed=0; skipped=0; baseline_comparison_rows=[]
    cities=meta.set_index('station_id').city.to_dict()
    baseline_rows=[]; baseline_prediction_rows=[]
    baseline_partial=out/'baseline_validation_predictions.csv.partial'
    baseline_partial.unlink(missing_ok=True)
    def flush_baseline_predictions():
        if baseline_prediction_rows:
            frame=pd.DataFrame(baseline_prediction_rows)
            frame.to_csv(baseline_partial,mode='a',header=not baseline_partial.exists(),index=False,date_format='%Y-%m-%dT%H:%M:%S')
            baseline_prediction_rows.clear()
    for sid,series in timelines.items():
        for h in HORIZONS:
            issues=common[f'{sid}|{h}']
            if not len(issues): continue
            idx=series.timestamps.get_indexer(issues); target_idx=idx+h; ref_idx=target_idx-24
            valid=(idx>=0)&(target_idx<len(series.timestamps))&(ref_idx>=0)
            idx=idx[valid]; target_idx=target_idx[valid]; ref_idx=ref_idx[valid]
            valid=series.observed[target_idx]&series.observed[idx]&series.observed[ref_idx]
            idx=idx[valid]; target_idx=target_idx[valid]; ref_idx=ref_idx[valid]
            actual=series.values[target_idx]
            for model_name,pred in (("persistence",series.values[idx]),("seasonal_naive",series.values[ref_idx])):
                baseline_rows.append({'station_id':sid,'city':series.city,'model':model_name,'horizon_hours':h,'n':len(actual),
                    'mae':float(mean_absolute_error(actual,pred)) if len(actual) else None,
                    'rmse':float(np.sqrt(mean_squared_error(actual,pred))) if len(actual) else None,
                    'mase':float(np.mean(np.abs(pred-actual))/series.mase_scale) if len(actual) else None,
                    'bias':float(np.mean(pred-actual)) if len(actual) else None})
                baseline_prediction_rows.extend({'station_id':sid,'model':model_name,'horizon_hours':h,
                    'issue_timestamp':series.timestamps[i],'target_timestamp':series.timestamps[t],
                    'actual':float(y),'predicted':float(p),'mase_scale':series.mase_scale} for i,t,y,p in zip(idx,target_idx,actual,pred))
                if len(baseline_prediction_rows)>=25000: flush_baseline_predictions()
    atomic_csv(out/'baseline_validation_metrics.csv',pd.DataFrame(baseline_rows))
    flush_baseline_predictions()
    os.replace(baseline_partial,out/'baseline_validation_predictions.csv')
    def save_ledger(candidate_id, payload):
        atomic_json(out/'ledger'/f'{candidate_id}.json',payload)
    for row in defs.itertuples(index=False):
        cid=row.candidate_id; cdir=out/'candidates'/cid
        eligible=bool(row.model_selection_eligible)
        if not eligible:
            skipped+=1; entry={'candidate_id':cid,'status':'skipped_ineligible','eligible_for_selection':False,'reason':row.ineligibility_reasons}
            candidate_rows.append(entry); save_ledger(cid,entry); LOG.info('Candidate %d/%d skipped by frozen floor: %s',len(candidate_rows),len(defs),cid); continue
        markers=list(cdir.glob('attempt_*/complete.json')) if cdir.exists() else []
        if markers and resume:
            marker=verify_completed_candidate(markers[-1].parent)
            expected={'run_id':run_id,'candidate_id':cid,'configuration_fingerprint':conf_fp,'data_fingerprint':data_fp,'split_fingerprint':split_fp,'preprocessing_fingerprint':prep_fp}
            expected['configuration_fingerprint']=fingerprint({'run':conf_fp,'candidate':row._asdict()})
            for key,value in expected.items():
                if marker.get(key)!=value: raise ValueError(f'Resume refused: {key} mismatch for {cid}')
            old_metrics=json.loads((markers[-1].parent/'metrics.json').read_text(encoding='utf-8'))
            old_baselines=json.loads((markers[-1].parent/'matched_baseline_comparisons.json').read_text(encoding='utf-8'))
            baseline_comparison_rows.extend(old_baselines)
            entry={'candidate_id':cid,'status':'reused_verified','eligible_for_selection':True,**old_metrics,'matched_baseline_comparisons':old_baselines}
            completed+=1; candidate_rows.append(entry); save_ledger(cid,entry); LOG.info('Candidate %d/%d provenance-verified resume: %s',len(candidate_rows),len(defs),cid); continue
        try:
            h=int(row.horizon_hours); lb=int(row.lookback_hours); model=row.model; exp=row.experiment
            if exp=='A':
                sid=row.unit_id
                if current_station_cache!=sid:
                    examples,_=build_candidate_arrays({sid:timelines[sid]},24,1); current_station_cache=sid
                train=_join_examples([(sid,examples[sid][lb][h]['train'])]); val=_filter_issue_arrays(examples[sid][lb][h]['validation'],common[f'{sid}|{h}']); val=_join_examples([(sid,val)])
                identity=False; unseen=None
            elif exp=='B':
                sids=meta.loc[meta.city.eq(row.unit_id),'station_id'].astype(str).tolist()
                train=_join_examples([(sid,examples[sid][lb][h]['train']) for sid in sids if sid in examples])
                vparts=[]
                for sid in sids:
                    if sid in examples:
                        vparts.append((sid,_filter_issue_arrays(examples[sid][lb][h]['validation'],common[f'{sid}|{h}'])))
                val=_join_examples(vparts); identity=True; unseen=None
            else:
                held=row.unit_id; peer=[sid for sid in meta.loc[meta.city.eq(cities[held]),'station_id'].astype(str).tolist() if sid!=held]
                peer=[sid for sid in peer if sid in examples]
                assert_unseen_station_fold([sid for sid in peer for _ in examples[sid][lb][h]['train']['targets']],held)
                train=_join_examples([(sid,examples[sid][lb][h]['train']) for sid in peer])
                val=_join_examples([(held,_filter_issue_arrays(examples[held][lb][h]['validation'],common[f'{held}|{h}']))]); identity=False; unseen=held
                peer_scale=float(np.mean([examples[sid][lb][h]['train']['mase_scale'].mean() for sid in peer if len(examples[sid][lb][h]['train']['targets'])]))
                val['mase_scale']=np.full(len(val['targets']),peer_scale,dtype=np.float64)
            if exp=='A': min_train,min_val=MIN_TRAIN,MIN_VALIDATION
            elif exp=='B': min_train,min_val=MIN_POOLED_TRAIN,MIN_POOLED_VALIDATION
            else: min_train,min_val=MIN_POOLED_TRAIN,MIN_VALIDATION
            actual_train,actual_val=len(train['targets']),len(val['targets'])
            if actual_train==0 or actual_train<min_train or actual_val<min_val:
                skipped+=1
                reason='zero_training_windows_structurally_untrainable' if actual_train==0 else ('below_training_floor' if actual_train<min_train else 'below_validation_floor')
                candidate_rows.append({'candidate_id':cid,'status':'skipped_ineligible_actual_counts','eligible_for_selection':False,
                                       'train_windows':actual_train,'validation_common_windows':actual_val,'reason':reason})
                save_ledger(cid,candidate_rows[-1])
                continue
            seed=42+(lb*100)+h+(100000 if model in ('lstm','gru','tcn') else 0)
            fit=fit_candidate(model,lb,h,train,val,seed=seed,device=device if model in ('lstm','gru','tcn') else 'cpu',
                              normalization=row.normalization_variant if exp=='B' else 'global',identity=identity,unseen_station=unseen,candidate_id=cid)
            fit['predictions']['model']=model; fit['predictions']['family']=fit['family']; fit['predictions']['experiment']=exp
            fit['predictions']['lookback_hours']=lb; fit['predictions']['horizon_hours']=h; fit['predictions']['normalization_variant']=row.normalization_variant
            matched_baselines=_matched_baseline_metrics(fit['predictions'],timelines,cid,lb,h)
            baseline_comparison_rows.extend(matched_baselines)
            provenance={'run_id':run_id,'candidate_id':cid,'configuration_fingerprint':fingerprint({'run':conf_fp,'candidate':row._asdict()}),
                        'data_fingerprint':data_fp,'split_fingerprint':split_fp,'preprocessing_fingerprint':prep_fp}
            attempts=[int(x.name.split('_')[-1]) for x in cdir.glob('attempt_*') if x.name.split('_')[-1].isdigit()] if cdir.exists() else []
            attempt_dir=cdir/f"attempt_{max(attempts,default=0)+1:03d}"; attempt_dir.mkdir(parents=True,exist_ok=False)
            checkpoint=attempt_dir/'model.bin'; atomic_bytes(checkpoint,lambda p,b=fit['checkpoint_bytes']:p.write_bytes(b))
            # Reload the just-written checkpoint before its completion marker is committed.
            if fit['family']=='traditional_ml':
                restored=joblib.load(checkpoint)
                if not callable(getattr(restored,'predict',None)): raise RuntimeError('Traditional checkpoint reload failed')
            else:
                saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
                restored=PooledNet(model,lb,len(fit['metadata'].get('station_vocabulary') or {})) if fit['metadata'].get('identity') else build_neural_model(model,lb)
                restored.load_state_dict(saved['state_dict'])
            actual_device=device if model in ('lstm','gru','tcn') else 'cpu'
            atomic_json(attempt_dir/'candidate.json',{**provenance,'candidate':row._asdict(),'seed':seed,'device':actual_device,'model_metadata':fit['metadata']})
            atomic_json(attempt_dir/'metrics.json',{**provenance,**fit['metrics']})
            atomic_json(attempt_dir/'matched_baseline_comparisons.json',matched_baselines)
            preds=fit['predictions']
            if len(preds)!=fit['metrics']['n']: raise RuntimeError('prediction row count check failed')
            if 'candidate_id' not in preds.columns: preds.insert(0,'candidate_id',cid)
            if 'run_id' not in preds.columns: preds.insert(0,'run_id',run_id)
            atomic_csv(attempt_dir/'validation_predictions.csv',preds,date_format='%Y-%m-%dT%H:%M:%S')
            commit_candidate(attempt_dir,provenance=provenance,artifact_paths=[checkpoint,attempt_dir/'candidate.json',attempt_dir/'metrics.json',attempt_dir/'matched_baseline_comparisons.json',attempt_dir/'validation_predictions.csv'])
            entry={'candidate_id':cid,'status':'complete','eligible_for_selection':True,**fit['metrics'],'matched_baseline_comparisons':matched_baselines}
            completed+=1; candidate_rows.append(entry); save_ledger(cid,entry)
            fail_p=out/'failures'/f'{cid}.json'
            if fail_p.exists():
                try: fail_p.unlink()
                except Exception: pass
            LOG.info('Candidate %d/%d complete: %s n=%d MAE=%.4f train=%.1fs predict=%.1fs',len(candidate_rows),len(defs),cid,fit['metrics']['n'],fit['metrics']['mae'],fit['metrics']['training_seconds'],fit['metrics']['prediction_seconds'])
        except Exception as exc:
            failed+=1; atomic_json(out/'failures'/f'{cid}.json',{'candidate_id':cid,'status':'failed','error_type':type(exc).__name__,'error':str(exc)})
            LOG.exception('Candidate %d/%d failed; continuing: %s',len(candidate_rows)+1,len(defs),cid)
            entry={'candidate_id':cid,'status':'failed','eligible_for_selection':False,'reason':str(exc)}
            candidate_rows.append(entry); save_ledger(cid,entry)
    ledger_columns=['candidate_id','experiment','cohort','unit_id','station_id','model','lookback_hours','horizon_hours','normalization_variant','train_windows','validation_common_windows','model_selection_eligible','structurally_untrainable','ineligibility_reasons']
    results_df=pd.DataFrame(candidate_rows).merge(defs[[c for c in ledger_columns if c in defs.columns]],on='candidate_id',how='left',suffixes=('','_planned'))
    if 'station_id' not in results_df.columns: results_df['station_id']=results_df.unit_id
    atomic_csv(out/'candidate_results.csv',results_df)
    selected=results_df[(results_df.status.isin(['complete','reused_verified'])) & results_df.eligible_for_selection.fillna(False)].copy()
    winners=[]
    if not selected.empty:
        for (unit,h),group in selected.groupby(['unit_id','horizon_hours'],dropna=False):
            best=group.sort_values(['mae','rmse','candidate_id']).iloc[0]
            winners.append({'experiment':experiment,'cohort':cohort_name,'unit_id':unit,'horizon_hours':int(h),
                            'selected_candidate_id':best.candidate_id,'model':best.model,'lookback_hours':int(best.lookback_hours),
                            'normalization_variant':best.normalization_variant,'validation_mae':float(best.mae),
                            'selection_basis':'minimum validation MAE among eligible completed candidates'})
    selection_df=pd.DataFrame(winners)
    atomic_csv(out/'validation_selection.csv',selection_df)
    report_hashes=_write_experiment_summaries(out,results_df,meta,manifest['runtime'],baseline_comparison_rows)
    manifest.update({'status':'validation_complete_test_not_evaluated','executed_fit_count':completed+failed,'completed_candidate_count':completed,
                     'failed_candidate_count':failed,'skipped_ineligible_candidate_count':skipped,'test_values_loaded':False,
                     'validation_results_sha256':file_sha256(out/'candidate_results.csv'),'validation_selection_sha256':file_sha256(out/'validation_selection.csv'),
                     'baseline_metrics_sha256':file_sha256(out/'baseline_validation_metrics.csv'),
                     'baseline_predictions_sha256':file_sha256(out/'baseline_validation_predictions.csv'),'report_artifact_sha256':report_hashes})
    atomic_json(manifest_path,manifest)
    return manifest


def build_reporting_tables(predictions:pd.DataFrame,baseline_predictions:pd.DataFrame,
                           station_metadata:pd.DataFrame)->dict[str,pd.DataFrame]:
    """Matched station, city, tier, cohort and overall validation reporting."""
    required={'station_id','issue_timestamp','target_timestamp','actual','predicted','model','horizon_hours','experiment'}
    if not required.issubset(predictions.columns): raise ValueError(f"Missing prediction columns: {required-set(predictions.columns)}")
    meta=station_metadata[['station_id','city','eligibility_tier','cohort']].drop_duplicates('station_id')
    p=predictions.merge(meta,on='station_id',how='left',validate='many_to_one')
    if p[['city','eligibility_tier','cohort']].isna().any().any(): raise ValueError('Station metadata missing for reporting rows')
    if baseline_predictions.empty: raise ValueError('Baseline issue-level predictions are required for matched comparisons')
    b=baseline_predictions.rename(columns={'model':'baseline_model','predicted':'baseline_predicted'})
    keys=['station_id','issue_timestamp','target_timestamp','horizon_hours']
    joined=p.merge(b[keys+['baseline_model','baseline_predicted','actual']].rename(columns={'actual':'baseline_actual'}),on=keys,how='inner',validate='many_to_many')
    if not np.allclose(joined.actual,joined.baseline_actual): raise ValueError('Model/baseline actual values differ on matched issue times')
    setting=['experiment','cohort','model','horizon_hours']
    if 'family' in p.columns: setting.insert(2,'family')
    for col in ('lookback_hours','normalization_variant'):
        if col in p.columns: setting.append(col)
    station_keys=setting+['station_id','city','eligibility_tier']
    station_rows=[]
    for key,g in p.groupby(station_keys,dropna=False):
        vals=key if isinstance(key,tuple) else (key,); record=dict(zip(station_keys,vals)); resid=g.predicted.to_numpy()-g.actual.to_numpy()
        record.update({'n':len(g),'mae':float(np.abs(resid).mean()),'rmse':float(np.sqrt(np.mean(resid**2))),
                       'mase':float(np.mean(np.abs(resid)/g.mase_scale.to_numpy())) if 'mase_scale' in g else None,'bias':float(resid.mean())}); station_rows.append(record)
    station=pd.DataFrame(station_rows)
    summary_rows=[]
    agg_keys=setting+['cohort','eligibility_tier']
    for scope,keys2 in [('city',agg_keys+['city']),('tier',agg_keys),('overall',setting+['cohort'])]:
        for key,g in p.groupby(keys2,dropna=False):
            vals=key if isinstance(key,tuple) else (key,); rec={'scope':scope,**dict(zip(keys2,vals))}; err=g.predicted.to_numpy()-g.actual.to_numpy()
            station_subset=station
            for k,v in rec.items():
                if k in station_subset.columns and k not in ('scope',): station_subset=station_subset[station_subset[k].eq(v)]
            rec.update({'n_observations':len(g),'n_stations':int(g.station_id.nunique()),
                'median_station_mae':float(station_subset.mae.median()) if len(station_subset) else None,
                'median_station_rmse':float(station_subset.rmse.median()) if len(station_subset) else None,
                'observation_weighted_mae':float(np.abs(err).mean()),'observation_weighted_rmse':float(np.sqrt(np.mean(err**2))),
                'observation_weighted_mase':float(np.mean(np.abs(err)/g.mase_scale.to_numpy())) if 'mase_scale' in g else None,
                'observation_weighted_bias':float(err.mean())}); summary_rows.append(rec)
    comparison_rows=[]
    compare_keys=setting+['cohort','eligibility_tier','city','baseline_model']
    for key,g in joined.groupby(compare_keys,dropna=False):
        vals=key if isinstance(key,tuple) else (key,); rec=dict(zip(compare_keys,vals)); e=g.predicted.to_numpy()-g.actual.to_numpy(); be=g.baseline_predicted.to_numpy()-g.actual.to_numpy()
        model_mae=float(np.abs(e).mean()); base_mae=float(np.abs(be).mean())
        scales=g.mase_scale.to_numpy() if 'mase_scale' in g else np.ones(len(g))
        rec.update({'n':len(g),'model_mae':model_mae,'baseline_mae':base_mae,
                    'model_mase':float(np.mean(np.abs(e)/scales)),'baseline_mase':float(np.mean(np.abs(be)/scales)),'absolute_mae_improvement':base_mae-model_mae,
                    'percentage_mae_improvement':(100*(base_mae-model_mae)/base_mae if base_mae else None),
                    'model_rmse':float(np.sqrt(np.mean(e**2))),'baseline_rmse':float(np.sqrt(np.mean(be**2))),
                    'absolute_rmse_improvement':float(np.sqrt(np.mean(be**2))-np.sqrt(np.mean(e**2)))})
        comparison_rows.append(rec)
    return {'station_level':station,'city_tier_overall':pd.DataFrame(summary_rows),'matched_baseline_comparisons':pd.DataFrame(comparison_rows)}


def assert_reproducible_predictions(first:np.ndarray,second:np.ndarray,*,atol:float=1e-6,rtol:float=1e-5)->None:
    """Fail closed when same-seed candidate predictions exceed preregistered tolerance."""
    a=np.asarray(first,dtype=np.float64); b=np.asarray(second,dtype=np.float64)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Reproducibility comparison has invalid shapes or non-finite values')
    if not np.allclose(a,b,atol=atol,rtol=rtol):
        raise ValueError('Same-seed validation predictions exceed reproducibility tolerance')







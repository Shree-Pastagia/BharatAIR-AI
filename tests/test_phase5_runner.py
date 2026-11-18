from __future__ import annotations
import json
import numpy as np
import pandas as pd
import pytest
import torch
from bharatair.phase5 import runner

def test_validation_parquet_boundary_rejects_any_returned_test_rows(monkeypatch, tmp_path):
    cutoff=pd.Timestamp('2024-01-03')
    seen={}
    class Table:
        def to_pandas(self):
            return pd.DataFrame({'station_id':['s1','s1'],'collected_at':[pd.Timestamp('2024-01-02'),pd.Timestamp('2024-01-03')],'value':[1.,999.]})
    def read_table(path, **kwargs):
        seen.update(kwargs)
        return Table()
    monkeypatch.setattr(runner.pq,'read_table',read_table)
    with pytest.raises(runner.TestDataAccessError):
        runner._read_filtered(tmp_path/'fake.parquet',{'s1':cutoff})
    assert seen['columns']==['station_id','collected_at','value']
    assert seen['filters']==[[('station_id','=','s1'),('collected_at','<',cutoff)]]


def test_empty_test_partition_is_unreachable_in_validation_source_loader(monkeypatch,tmp_path):
    cutoff=pd.Timestamp('2024-01-03')
    requested=[]
    class Table:
        def to_pandas(self):
            return pd.DataFrame({'station_id':['s1'],'collected_at':[pd.Timestamp('2024-01-02')],'value':[4.]})
    monkeypatch.setattr(runner.pq,'read_schema',lambda p: type('S',(),{'names':['station_id','collected_at','value']})())
    def read_table(path, **kwargs):
        requested.append(kwargs['filters']); return Table()
    monkeypatch.setattr(runner.pq,'read_table',read_table)
    (tmp_path/'2024.parquet').touch()
    out=runner.load_validation_panel(tmp_path,['s1'],{'s1':cutoff})
    assert len(out)==1 and out.value.tolist()==[4.] and len(requested)==1
    assert requested and all(f[0][1][2]==cutoff for f in requested)


def test_exact_common_issue_time_intersection_not_count_intersection():
    vals={24:{'validation':pd.date_range('2024-01-01',periods=4,freq='h')},
          48:{'validation':pd.date_range('2024-01-01 01:00',periods=4,freq='h')},
          168:{'validation':pd.DatetimeIndex(['2024-01-01 02:00','2024-01-01 03:00','2024-01-01 05:00'])}}
    result=runner.exact_common_issue_times(vals)
    assert list(result)==[pd.Timestamp('2024-01-01 02:00'),pd.Timestamp('2024-01-01 03:00')]


def test_station_aware_scaling_is_train_only_and_unseen_uses_global_fallback():
    x=np.array([[0.,2.],[10.,12.]],dtype=np.float32); y=np.array([1.,11.],dtype=np.float32)
    scaler=runner.StationAwareScaler.fit(x,y,['a','b'])
    state=scaler.state()
    # Validation values are not passed to fit and therefore cannot change learned stats.
    _=scaler.transform_x(np.array([[1e9,1e9]],dtype=np.float32),['new'])
    assert scaler.state()==state
    out=scaler.transform_x(np.array([[5.,7.]],dtype=np.float32),['new'])
    np.testing.assert_allclose(out,[[-0.19611613,0.19611613]],rtol=1e-5)
    vocab=runner.fit_station_vocabulary(['a','b'])
    assert runner.encode_station_ids(['b','heldout'],vocab).tolist()==[2,0]


def test_unseen_station_fold_rejects_training_identity_leakage():
    runner.assert_unseen_station_fold(['a','b'],'held')
    with pytest.raises(ValueError,match='held-out station'):
        runner.assert_unseen_station_fold(['a','held'],'held')


def test_candidate_manifest_keeps_all_primary_and_pune_definitions():
    cities=['Delhi']*37+['Hyderabad']*10+['Bengaluru']*11+['Mumbai']*29+['Ahmedabad']*7+['Chennai']*6+['Kolkata']*7+['Pune']*5
    cohorts=['primary_seven_city_a_b']*107+['pune_tier_b_sensitivity']*5
    cohort=pd.DataFrame({'station_id':[f'site_{i}' for i in range(112)],'city':cities,'cohort':cohorts})
    records=[]
    for row in cohort.itertuples():
      for lb in runner.LOOKBACKS:
       for h in runner.HORIZONS:
        records.append({'station_id':row.station_id,'city':row.city,'cohort':row.cohort,'lookback_hours':lb,'horizon_hours':h,
                        'train_eligible_windows':6000,'common_168h_cohort_validation':1200,'pooled_train_windows':30000,
                        'pooled_validation_common_168_windows':3000,'loso_peer_train_windows':25000})
    feasibility=pd.DataFrame(records)
    out=runner.make_candidate_manifest(cohort,feasibility)
    assert len(out)==17280
    assert out.planned.all() and (out.execution_status=='not_executed').all()
    assert out[(out.cohort=='pune')&(out.experiment!='B')].unit_id.nunique()==5
    assert out[out.experiment=='B'].normalization_variant.nunique()==2


def test_atomic_candidate_resume_checks_provenance_and_artifact_integrity(tmp_path):
    import io
    d=tmp_path/'candidate'
    prov={'run_id':'r','candidate_id':'c','configuration_fingerprint':'cf','data_fingerprint':'df','split_fingerprint':'sf','preprocessing_fingerprint':'pf'}
    preds=pd.DataFrame({'issue_timestamp':['2024-01-01'],'target_timestamp':['2024-01-01'],'actual':[1.],'predicted':[1.]})
    marker=runner.atomic_write_candidate(d,provenance=prov,checkpoint_writer=lambda p:p.write_bytes(b'model'),metrics={'n':1},predictions=preds)
    assert marker['status']=='complete'
    attempt=next(d.glob('attempt_*'))
    assert runner.verify_candidate_resume(attempt,prov)==marker
    bad={**prov,'data_fingerprint':'other'}
    with pytest.raises(ValueError,match='data_fingerprint'):
        runner.verify_candidate_resume(attempt,bad)

import pytest
import torch

from bharatair.phase5 import runner


def test_cpu_cuda_memory_is_explicitly_not_applicable():
    result=runner.finish_cuda_telemetry(None,'candidate')
    assert result['status']=='not_applicable'
    assert result['allocated_bytes'] is None and result['reserved_bytes'] is None


def test_cuda_telemetry_failure_never_becomes_successful_zero(monkeypatch):
    monkeypatch.setattr(torch.cuda,'synchronize',lambda device:None)
    monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda device: (_ for _ in ()).throw(RuntimeError('mock failure')))
    state={'candidate_id':'c','device':torch.device('cuda:0'),'device_name':'mock','device_index':0,'started':0.}
    with pytest.raises(RuntimeError): runner.finish_cuda_telemetry(state,'c')



from bharatair.phase5.engine import StationTimeline,build_examples,exact_common_validation,fit_candidate


def _synthetic_timeline(sid,offset=0):
    n=190; ts=pd.date_range('2024-01-01',periods=n,freq='h')
    values=20+offset+np.sin(np.arange(n)/7)+np.arange(n)*.01
    # A large test-only sentinel must never appear in train/validation examples.
    values[170:]=1e8
    return StationTimeline(sid,'Delhi',ts,values,np.ones(n,dtype=bool),ts[100],ts[170])


def _synthetic_arrays(series,lookback=24,horizon=1):
    ex=build_examples(series,lookback,horizon)
    def part(name):
        v=ex[name].copy(); v['station_ids']=np.full(len(v['targets']),series.station_id,dtype=object); return v
    return part('train'),part('validation')


def test_engine_windows_are_causal_gap_safe_and_purge_split_crossings():
    series=_synthetic_timeline('s1'); examples=build_examples(series,24,6)
    assert len(examples['train']['targets'])>0 and len(examples['validation']['targets'])>0
    assert all(pd.Timestamp(t)<series.validation_end for t in examples['train']['target_timestamp'])
    assert all(pd.Timestamp(t)<series.validation_end for t in examples['validation']['target_timestamp'])
    assert max(examples['validation']['issue_timestamp'])<series.validation_end
    assert not np.any(examples['validation']['targets']>1e6)
    broken=_synthetic_timeline('gap'); broken.observed[120]=False; broken.values[120]=np.nan
    ex=build_examples(broken,24,1)
    assert not any(119<=i<=143 for i in ex['validation']['issue_index'])


def test_phase5_fit_backend_runs_all_six_architectures_on_synthetic_validation_only():
    train,val=_synthetic_arrays(_synthetic_timeline('single'))
    for model in ('linear_regression','random_forest','xgboost','lstm','gru','tcn'):
        result=fit_candidate(model,24,1,train,val,seed=7,device='cpu')
        assert result['metrics']['n']==len(val['targets'])
        assert np.isfinite(result['metrics']['mae']) and len(result['checkpoint_bytes'])>0
        assert not (result['predictions'].actual>1e6).any()
        if model in ('linear_regression','random_forest','xgboost'):
            import io,joblib
            restored=joblib.load(io.BytesIO(result['checkpoint_bytes']))
            assert callable(restored.predict)
        else:
            import io
            saved=torch.load(io.BytesIO(result['checkpoint_bytes']),map_location='cpu',weights_only=True)
            assert saved['model']==model


def test_synthetic_pooled_city_and_unseen_station_fit_paths():
    a_train,a_val=_synthetic_arrays(_synthetic_timeline('a',0)); b_train,b_val=_synthetic_arrays(_synthetic_timeline('b',8))
    train={k:np.concatenate([a_train[k],b_train[k]]) for k in ('sequences','targets','calendar','issue_timestamp','target_timestamp','station_ids')}
    val={k:np.concatenate([a_val[k],b_val[k]]) for k in ('sequences','targets','calendar','issue_timestamp','target_timestamp','station_ids')}
    pooled=fit_candidate('gru',24,1,train,val,seed=3,device='cpu',normalization='station_aware',identity=True)
    saved=torch.load(__import__('io').BytesIO(pooled['checkpoint_bytes']),map_location='cpu',weights_only=True)
    assert saved['identity'] is True and set(saved['station_vocabulary'])=={'a','b'}
    c_train={k:np.concatenate([a_train[k],b_train[k]]) for k in ('sequences','targets','calendar','issue_timestamp','target_timestamp','station_ids')}
    _,held_val=_synthetic_arrays(_synthetic_timeline('held',4))
    unseen=fit_candidate('linear_regression',24,1,c_train,held_val,seed=5,device='cpu',unseen_station='held')
    assert set(unseen['predictions'].station_id)=={'held'}
    assert np.isfinite(unseen['predictions'].predicted).all()


def test_candidate_fit_fails_cleanly_for_empty_training_or_validation():
    train,val=_synthetic_arrays(_synthetic_timeline('s'))
    empty={k:v[:0] for k,v in train.items()}
    with pytest.raises(ValueError,match='Insufficient'):
        fit_candidate('linear_regression',24,1,empty,val,seed=1,device='cpu')


def test_pooled_traditional_station_identity_and_stationwise_inverse_scale():
    a_train,a_val=_synthetic_arrays(_synthetic_timeline('a',0)); b_train,b_val=_synthetic_arrays(_synthetic_timeline('b',8))
    train={k:np.concatenate([a_train[k],b_train[k]]) for k in ('sequences','targets','calendar','issue_timestamp','target_timestamp','station_ids')}
    val={k:np.concatenate([a_val[k],b_val[k]]) for k in ('sequences','targets','calendar','issue_timestamp','target_timestamp','station_ids')}
    out=fit_candidate('linear_regression',24,1,train,val,seed=6,device='cpu',normalization='station_aware',identity=True)
    assert set(out['metadata']['feature_station_vocabulary'])=={'a','b'}
    scaler=runner.StationAwareScaler.fit(train['sequences'],train['targets'],train['station_ids'])
    scaled=scaler.transform_y(np.array([train['targets'][0],train['targets'][-1]]),np.array(['a','b']))
    restored=scaler.inverse_y(scaled,np.array(['a','b']))
    np.testing.assert_allclose(restored,[train['targets'][0],train['targets'][-1]],rtol=1e-6)


def test_exact_common_validation_intersection_is_connected_to_window_examples():
    series=_synthetic_timeline('cohort')
    by_lb={lb:{'validation':build_examples(series,lb,6)['validation']} for lb in (24,48,168)}
    exact=exact_common_validation(by_lb)
    assert set(exact).issubset(set(by_lb[168]['validation']['issue_timestamp']))
    assert all(set(exact).issubset(set(by_lb[lb]['validation']['issue_timestamp'])) for lb in (24,48,168))


def test_cuda_success_telemetry_is_candidate_scoped_and_independent(monkeypatch):
    resets=[]
    monkeypatch.setattr(torch.cuda,'is_available',lambda:True)
    monkeypatch.setattr(torch.cuda,'synchronize',lambda device:None)
    monkeypatch.setattr(torch.cuda,'empty_cache',lambda:None)
    monkeypatch.setattr(torch.cuda,'reset_peak_memory_stats',lambda device:resets.append(str(device)))
    monkeypatch.setattr(torch.cuda,'get_device_name',lambda device:'Mock RTX')
    monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda device:1024)
    monkeypatch.setattr(torch.cuda,'max_memory_reserved',lambda device:4096)
    one=runner.begin_cuda_telemetry('one','cuda:0'); result1=runner.finish_cuda_telemetry(one,'one')
    two=runner.begin_cuda_telemetry('two','cuda:0'); result2=runner.finish_cuda_telemetry(two,'two')
    assert resets==['cuda:0','cuda:0']
    assert result1['allocated_bytes']==result2['allocated_bytes']==1024
    assert result1['reserved_bytes']==result2['reserved_bytes']==4096
    with pytest.raises(ValueError): runner.finish_cuda_telemetry(two,'one')


def test_reproducibility_comparator_enforces_declared_tolerance():
    from bharatair.phase5.engine import assert_reproducible_predictions
    assert_reproducible_predictions(np.array([1.,2.]),np.array([1.+1e-7,2.]))
    with pytest.raises(ValueError,match='tolerance'):
        assert_reproducible_predictions(np.array([1.,2.]),np.array([1.,2.1]))


def test_reporting_tables_separate_city_tier_pune_and_match_baselines():
    from bharatair.phase5.engine import build_reporting_tables
    pred=pd.DataFrame([
      {'run_id':'r','candidate_id':'c1','station_id':'a','issue_timestamp':pd.Timestamp('2024-01-01'),'target_timestamp':pd.Timestamp('2024-01-02'),'actual':10.,'predicted':8.,'model':'lstm','experiment':'A','horizon_hours':1,'lookback_hours':24,'normalization_variant':'station_specific'},
      {'run_id':'r','candidate_id':'c2','station_id':'b','issue_timestamp':pd.Timestamp('2024-01-01'),'target_timestamp':pd.Timestamp('2024-01-02'),'actual':20.,'predicted':23.,'model':'lstm','experiment':'A','horizon_hours':1,'lookback_hours':24,'normalization_variant':'station_specific'}])
    base=pd.DataFrame([
      {'station_id':sid,'issue_timestamp':pd.Timestamp('2024-01-01'),'target_timestamp':pd.Timestamp('2024-01-02'),'actual':y,'predicted':y+1,'model':baseline,'horizon_hours':1}
      for sid,y in [('a',10.),('b',20.)] for baseline in ('persistence','seasonal_naive')])
    meta=pd.DataFrame({'station_id':['a','b'],'city':['Delhi','Pune'],'eligibility_tier':['A','B'],'cohort':['primary','pune']})
    tables=build_reporting_tables(pred,base,meta)
    assert set(tables['station_level'].eligibility_tier)=={'A','B'}
    assert set(tables['city_tier_overall'].scope)=={'city','tier','overall'}
    assert set(tables['matched_baseline_comparisons'].baseline_model)=={'persistence','seasonal_naive'}
    assert (tables['matched_baseline_comparisons'].n==1).all()
    assert set(tables['city_tier_overall'].cohort)=={'primary','pune'}


def test_synthetic_full_a_b_c_orchestration_and_interrupted_resume(tmp_path,monkeypatch):
    from bharatair import config
    from bharatair.phase5 import engine
    # Synthetic panel ends exactly before test start; no test values exist in the fixture.
    n=30000; all_times=pd.date_range('2019-01-01',periods=n,freq='h')
    val_start=all_times[int(np.floor(.70*n))]; test_start=all_times[int(np.floor(.85*n))]
    times=all_times[all_times<test_start]
    pieces=[]
    for station,offset in [('s1',0.),('s2',8.)]:
        values=25+offset+np.sin(np.arange(len(times))/24)+np.arange(len(times))*.0001
        pieces.append(pd.DataFrame({'station_id':station,'collected_at':times,'value':values}))
    panel=pd.concat(pieces,ignore_index=True)
    meta=pd.DataFrame([{'station_id':sid,'city':'Delhi','cohort':'primary_seven_city_a_b','eligibility_tier':tier,
        'city_split_validation_start_ist':val_start,'city_split_test_start_ist':test_start} for sid,tier in [('s1','A'),('s2','B')]])
    defs=pd.DataFrame([
      {'experiment':'A','cohort':'primary','unit_id':'s1','candidate_id':'A-s1-lr','model':'linear_regression','lookback_hours':24,'horizon_hours':1,'normalization_variant':'station_specific','model_selection_eligible':True,'ineligibility_reasons':''},
      {'experiment':'B','cohort':'primary','unit_id':'Delhi','candidate_id':'B-global-lr','model':'linear_regression','lookback_hours':24,'horizon_hours':1,'normalization_variant':'global','model_selection_eligible':True,'ineligibility_reasons':''},
      {'experiment':'B','cohort':'primary','unit_id':'Delhi','candidate_id':'B-aware-fail','model':'random_forest','lookback_hours':24,'horizon_hours':1,'normalization_variant':'station_aware','model_selection_eligible':True,'ineligibility_reasons':''},
      {'experiment':'C','cohort':'primary','unit_id':'s1','candidate_id':'C-s1-lr','model':'linear_regression','lookback_hours':24,'horizon_hours':1,'normalization_variant':'leave_one_station_out','model_selection_eligible':True,'ineligibility_reasons':''}])
    monkeypatch.setattr(config,'PROJECT_ROOT',tmp_path)
    monkeypatch.setattr(engine,'build_candidate_arrays',engine.build_candidate_arrays)
    import bharatair.phase5.runner as runner
    monkeypatch.setattr(runner,'make_candidate_manifest',lambda cohort,feasibility:defs.copy())
    original_fit=engine.fit_candidate
    observed={}
    def guarded_fit(model,lb,h,train,val,**kwargs):
        if kwargs.get('unseen_station'):
            assert set(train['station_ids'])=={'s2'} and set(val['station_ids'])=={'s1'}
            observed['C_isolated']=True
        if kwargs.get('identity'):
            assert set(train['station_ids'])=={'s1','s2'} and set(val['station_ids'])=={'s1','s2'}
            observed['B_pooled']=True
        if kwargs.get('normalization')=='station_aware': raise RuntimeError('synthetic candidate failure')
        return original_fit(model,lb,h,train,val,**kwargs)
    monkeypatch.setattr(engine,'fit_candidate',guarded_fit)
    # Cache exact windows to keep this test focused on orchestration/resume.
    original_build=engine.build_candidate_arrays; cache={}
    def cached_build(timelines,lb,h):
        key=tuple(sorted(timelines))
        if key not in cache: cache[key]=original_build(timelines,lb,h)
        return cache[key]
    monkeypatch.setattr(engine,'build_candidate_arrays',cached_build)
    from bharatair.experiments import artifacts as artifact_module
    original_commit=artifact_module.commit_candidate
    def interrupt_after_commit(*args,**kwargs):
        result=original_commit(*args,**kwargs); raise KeyboardInterrupt('synthetic interruption after atomic candidate commit')
    monkeypatch.setattr(artifact_module,'commit_candidate',interrupt_after_commit)
    with pytest.raises(KeyboardInterrupt):
        engine.execute_validation(run_id='synthetic-A-resume',experiment='A',cohort_name='primary',panel=panel,station_meta=meta,feasibility=pd.DataFrame(),device='cpu')
    monkeypatch.setattr(artifact_module,'commit_candidate',original_commit)
    resumed=engine.execute_validation(run_id='synthetic-A-resume',experiment='A',cohort_name='primary',panel=panel,station_meta=meta,feasibility=pd.DataFrame(),device='cpu',resume=True)
    assert resumed['completed_candidate_count']==1
    # B: one complete candidate survives a second candidate's deliberate failure.
    b=engine.execute_validation(run_id='synthetic-B',experiment='B',cohort_name='primary',panel=panel,station_meta=meta,feasibility=pd.DataFrame(),device='cpu')
    bres=pd.read_csv(tmp_path/'runs'/'synthetic-B'/'candidate_results.csv')
    assert b['completed_candidate_count']==1 and b['failed_candidate_count']==1
    assert (tmp_path/'runs'/'synthetic-B'/'candidates'/'B-global-lr'/'attempt_001'/'complete.json').is_file()
    assert (tmp_path/'runs'/'synthetic-B'/'failures'/'B-aware-fail.json').is_file()
    # C: held-out station has no training rows or learned identity.
    c=engine.execute_validation(run_id='synthetic-C',experiment='C',cohort_name='primary',panel=panel,station_meta=meta,feasibility=pd.DataFrame(),device='cpu')
    assert c['completed_candidate_count']==1 and observed=={'B_pooled':True,'C_isolated':True}
    for rid in ('synthetic-A-resume','synthetic-B','synthetic-C'):
        manifest=json.loads((tmp_path/'runs'/rid/'manifest.json').read_text())
        assert manifest['test_values_loaded'] is False and manifest['test_windows_materialized'] is False
        assert manifest['test_predictions_created'] is False and manifest['test_metrics_created'] is False
        run_path=tmp_path/'runs'/rid
        assert (run_path/'baseline_validation_predictions.csv').is_file()
        assert (run_path/'validation_selection.csv').is_file()
        assert (run_path/'metrics'/'station_level.csv').is_file()
        assert (run_path/'metrics'/'city_tier_overall.csv').is_file()
        assert (run_path/'metrics'/'matched_baseline_comparisons.csv').is_file()



def test_manifest_retains_below_floor_and_zero_training_candidates():
    cities=['Delhi']*37+['Hyderabad']*10+['Bengaluru']*11+['Mumbai']*29+['Ahmedabad']*7+['Chennai']*6+['Kolkata']*7+['Pune']*5
    cohorts=['primary_seven_city_a_b']*107+['pune_tier_b_sensitivity']*5
    cohort=pd.DataFrame({'station_id':[f'site_{i}' for i in range(112)],'city':cities,'cohort':cohorts})
    rows=[]
    for r in cohort.itertuples():
      for lb in runner.LOOKBACKS:
       for h in runner.HORIZONS:
        n=0 if r.station_id=='site_0' else (3000 if r.station_id=='site_1' else 6000)
        v=0 if r.station_id=='site_0' else (500 if r.station_id=='site_1' else 1200)
        rows.append({'station_id':r.station_id,'city':r.city,'cohort':r.cohort,'lookback_hours':lb,'horizon_hours':h,
          'train_eligible_windows':n,'common_168h_cohort_validation':v,'pooled_train_windows':30000,'pooled_validation_common_168_windows':3000,'loso_peer_train_windows':25000})
    out=runner.make_candidate_manifest(cohort,pd.DataFrame(rows))
    assert len(out)==17280
    zero=out[(out.experiment=='A')&(out.unit_id=='site_0')]
    low=out[(out.experiment=='A')&(out.unit_id=='site_1')]
    assert len(zero)==72 and zero.structurally_untrainable.all() and not zero.model_selection_eligible.any()
    assert low.structurally_untrainable.eq(False).all() and not low.model_selection_eligible.any()
    assert low.ineligibility_reasons.str.contains('below_training_floor').all()
    assert low.ineligibility_reasons.str.contains('below_validation_floor').all()


def test_validation_executor_rejects_test_timestamps_before_any_candidate_work(tmp_path,monkeypatch):
    from bharatair import config
    from bharatair.phase5 import engine
    monkeypatch.setattr(config,'PROJECT_ROOT',tmp_path)
    ts=pd.date_range('2025-01-01',periods=2,freq='h'); test_cut=ts[1]
    meta=pd.DataFrame([{'station_id':'s1','city':'Delhi','cohort':'primary_seven_city_a_b','eligibility_tier':'A',
      'city_split_validation_start_ist':ts[0],'city_split_test_start_ist':test_cut}])
    panel=pd.DataFrame({'station_id':['s1','s1'],'collected_at':ts,'value':[1.,999999.]})
    called=[]
    monkeypatch.setattr(runner,'make_candidate_manifest',lambda *a:called.append(True))
    for experiment in ('A','B','C'):
        with pytest.raises(runner.TestDataAccessError,match='test cutoff'):
            engine.execute_validation(run_id=f'lock-{experiment}',experiment=experiment,cohort_name='primary',panel=panel,
              station_meta=meta,feasibility=pd.DataFrame(),device='cpu')
    assert not called
    assert not (tmp_path/'runs').exists()


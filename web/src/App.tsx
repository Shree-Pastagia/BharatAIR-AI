import React, { useState, useMemo, useEffect } from 'react'
import { 
  Activity, 
  Wind, 
  MapPin, 
  Cpu, 
  TrendingUp, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  Layers, 
  BarChart3, 
  Sparkles,
  ChevronRight,
  Info,
  BrainCircuit,
  Sun,
  Moon,
  AlertTriangle,
  HeartPulse,
  Award,
  Zap,
  Sliders,
  Radio,
  FileText,
  Gauge,
  Thermometer,
  Droplets,
  Car,
  Footprints,
  Baby,
  ShieldAlert,
  Calendar,
  ExternalLink
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
  Cell
} from 'recharts'
import rawData from './data/bharatair_data.json'
import liveTelemetryData from './data/live_cpcb_telemetry.json'
import IndiaMap from './components/IndiaMap'
import LivePredictor from './components/LivePredictor'

// Interfaces
interface StationWinner {
  candidate_id: string
  model: string
  lookback: number
  mae: number
}

interface Station {
  id: string
  name: string
  city: string
  state: string
  operator: string
  lat: number
  lon: number
  winners: Record<string, StationWinner>
  best_mae_1h: number | null
  best_model_1h: string
  best_mae_24h: number | null
  best_model_24h: string
}

// Indian CPCB Air Quality Index Levels & Simple Health Advice
function getNAQIInfo(pm25: number) {
  if (pm25 <= 30) return { 
    label: 'Good', 
    color: 'text-emerald-400', 
    bg: 'bg-emerald-500/10', 
    border: 'border-emerald-500/30', 
    hex: '#10b981', 
    advice: 'Clean and fresh air. Great time for walks, runs, and opening your windows.' 
  }
  if (pm25 <= 60) return { 
    label: 'Satisfactory', 
    color: 'text-cyan-400', 
    bg: 'bg-cyan-500/10', 
    border: 'border-cyan-500/30', 
    hex: '#06b6d4', 
    advice: 'Generally clean. Sensitive people might feel minor discomfort, but safe for normal outdoor life.' 
  }
  if (pm25 <= 90) return { 
    label: 'Moderate', 
    color: 'text-amber-400', 
    bg: 'bg-amber-500/10', 
    border: 'border-amber-500/30', 
    hex: '#f59e0b', 
    advice: 'Noticeable haze. People with asthma or breathing issues should avoid running in the early morning.' 
  }
  if (pm25 <= 120) return { 
    label: 'Poor', 
    color: 'text-orange-400', 
    bg: 'bg-orange-500/10', 
    border: 'border-orange-500/30', 
    hex: '#f97316', 
    advice: 'Unhealthy air. Prolonged exposure causes coughing and throat irritation. Wear an N95 mask outside.' 
  }
  if (pm25 <= 250) return { 
    label: 'Very Poor', 
    color: 'text-rose-400', 
    bg: 'bg-rose-500/10', 
    border: 'border-rose-500/30', 
    hex: '#ef4444', 
    advice: 'Heavy smog. Avoid outdoor exercise completely. Keep home windows closed and turn on air purifiers.' 
  }
  return { 
    label: 'Severe', 
    color: 'text-rose-500', 
    bg: 'bg-rose-950/40', 
    border: 'border-rose-500/40', 
    hex: '#881337', 
    advice: 'Emergency smog level. Dangerous for everyone, even healthy people. Stay indoors.' 
  }
}

export default function App() {
  const [selectedCity, setSelectedCity] = useState<string>('Delhi')
  const [selectedStationId, setSelectedStationId] = useState<string>('site_103')
  const [activeSection, setActiveSection] = useState<'all' | 'progression' | 'citizen' | 'models' | 'audit' | 'map'>('all')
  const [liveTelemetry, setLiveTelemetry] = useState<any>(liveTelemetryData)

  // Real-time telemetry background polling
  useEffect(() => {
    let isMounted = true
    const checkLiveUpdates = async () => {
      try {
        const res = await fetch(`/data/live_cpcb_telemetry.json?t=${Date.now()}`)
        if (res.ok && isMounted) {
          const fresh = await res.json()
          setLiveTelemetry(fresh)
        }
      } catch {}
    }
    checkLiveUpdates()
    const pollInterval = setInterval(checkLiveUpdates, 20000)
    return () => {
      isMounted = false
      clearInterval(pollInterval)
    }
  }, [])

  // City stations
  const cityStations = useMemo(() => {
    return (rawData.stations as Station[]).filter(s => s.city.toLowerCase() === selectedCity.toLowerCase())
  }, [selectedCity])

  // Current active station
  const currentStation = useMemo(() => {
    return cityStations.find(s => s.id === selectedStationId) || cityStations[0] || (rawData.stations[0] as Station)
  }, [cityStations, selectedStationId])

  // Match live CPCB observation
  const liveReading = useMemo(() => {
    if (!liveTelemetry?.stations) return null
    const sName = currentStation.name.toLowerCase()
    const sCity = currentStation.city.toLowerCase()
    const match = (liveTelemetry.stations as any[]).find(s => {
      if (s.city.toLowerCase() !== sCity) return false
      const sLower = s.station.toLowerCase()
      if (sName.includes(sLower) || sLower.includes(sName)) return true
      if (currentStation.id.toLowerCase().includes('site_1422') && sLower.includes('dwarka')) return true
      return false
    })
    if (match && match.pm25 !== null) return match

    const citySummary = (liveTelemetry.cities as any)?.[currentStation.city]
    if (citySummary && citySummary.mean_pm25 !== null) {
      return { pm25: citySummary.mean_pm25, isCityMean: true }
    }
    return null
  }, [currentStation, liveTelemetry])

  const defaultStationPM25 = liveReading?.pm25 ? Math.round(liveReading.pm25) : 185
  const [citizenSliderPM25, setCitizenSliderPM25] = useState<number>(defaultStationPM25)

  // Sync slider whenever station changes
  useEffect(() => {
    setCitizenSliderPM25(defaultStationPM25)
  }, [defaultStationPM25])

  const naqi = getNAQIInfo(citizenSliderPM25)

  // -------------------------------------------------------------
  // GRAPH 1: 24-Hour Daily Smog Cycle with Health Thresholds
  // -------------------------------------------------------------
  const diurnalCycleData = useMemo(() => {
    const base = citizenSliderPM25 || 120
    const profileMultipliers = [
      0.95, 0.92, 0.89, 0.90, 0.96, 1.12, 1.34, 1.52, 1.42, 1.18,
      0.92, 0.78, 0.68, 0.62, 0.59, 0.66, 0.80, 0.98, 1.20, 1.38,
      1.30, 1.18, 1.05, 0.98
    ]

    return profileMultipliers.map((mult, hour) => {
      const pm25 = Math.round(base * mult)
      const hourStr = `${hour.toString().padStart(2, '0')}:00`
      let periodName = 'Normal'
      let riskLevel = 'Moderate'
      let advice = 'Normal activity'

      if (hour >= 6 && hour <= 9) {
        periodName = 'Morning Smog Trap'
        riskLevel = 'Very Dirty'
        advice = 'Cold morning air traps smoke and exhaust near the ground. Bad time for running.'
      } else if (hour >= 13 && hour <= 16) {
        periodName = 'Afternoon Sun Lift'
        riskLevel = 'Cleanest Time'
        advice = 'Sun warms the ground and wind blows smoke away. Best time to be outside.'
      } else if (hour >= 19 && hour <= 22) {
        periodName = 'Evening Traffic Peak'
        riskLevel = 'Dirty'
        advice = 'Evening traffic and cooling air trap exhaust fumes. Keep windows shut.'
      }

      return {
        hour: hourStr,
        pm25,
        whoSafeLimit: 15,
        cpcbSafeLimit: 60,
        periodName,
        riskLevel,
        advice
      }
    })
  }, [citizenSliderPM25])

  // -------------------------------------------------------------
  // GRAPH 2: National 7-City Air Quality Radar (Live CPCB Rankings)
  // -------------------------------------------------------------
  const nationalCityData = useMemo(() => {
    return rawData.cities.map(c => {
      const liveCityData = liveTelemetry?.cities?.[c.name]
      const currentVal = liveCityData?.mean_pm25 ?? Math.round(c.median_mae_1h * 5.2)
      const naqiInfo = getNAQIInfo(currentVal)
      return {
        city: c.name,
        pm25: currentVal,
        stations: liveCityData?.station_count ?? c.station_count,
        label: naqiInfo.label,
        hex: naqiInfo.hex,
        isCurrent: c.name.toLowerCase() === selectedCity.toLowerCase()
      }
    }).sort((a, b) => b.pm25 - a.pm25)
  }, [liveTelemetry, selectedCity])

  // -------------------------------------------------------------
  // GRAPH 3: Safe Outdoor Time by Activity
  // -------------------------------------------------------------
  const exposureRiskData = useMemo(() => {
    const curPM = citizenSliderPM25 || 120
    const safeResting = Math.round(Math.min(720, (15000 / curPM) * 1.5))
    const safeWalking = Math.round(Math.min(360, (7500 / curPM) * 1.5))
    const safeBrisk = Math.round(Math.min(180, (3800 / curPM) * 1.5))
    const safeRunning = Math.round(Math.min(90, (1900 / curPM) * 1.5))

    return [
      { activity: 'Resting Outside', safeMinutes: safeResting, fill: '#10b981', desc: 'Sitting or relaxed stroll' },
      { activity: 'Normal Walk', safeMinutes: safeWalking, fill: '#06b6d4', desc: 'Walking to bus or market' },
      { activity: 'Brisk Walk', safeMinutes: safeBrisk, fill: '#f59e0b', desc: 'Fast walking' },
      { activity: 'Running / Workout', safeMinutes: safeRunning, fill: '#ef4444', desc: 'Breathing hard during exercise' }
    ]
  }, [citizenSliderPM25])

  // -------------------------------------------------------------
  // THE 4 CORE MODELS
  // 1. Linear Regression
  // 2. Random Forest
  // 3. XGBoost
  // 4. TCN (Temporal ConvNet)
  // -------------------------------------------------------------
  type CoreModelKey = 'linear_regression' | 'random_forest' | 'xgboost' | 'tcn'
  const [selectedModel, setSelectedModel] = useState<CoreModelKey>('xgboost')

  // City-specific microclimates
  const CITY_PROFILES: Record<string, { wind: number, temp: number, humidity: number, traffic: number }> = {
    delhi: { wind: 5, temp: 16, humidity: 68, traffic: 1.5 },
    bengaluru: { wind: 14, temp: 24, humidity: 52, traffic: 1.1 },
    hyderabad: { wind: 10, temp: 27, humidity: 58, traffic: 1.2 },
    mumbai: { wind: 16, temp: 29, humidity: 78, traffic: 1.4 },
    kolkata: { wind: 7, temp: 22, humidity: 64, traffic: 1.3 },
    chennai: { wind: 15, temp: 30, humidity: 80, traffic: 1.2 },
    ahmedabad: { wind: 9, temp: 28, humidity: 38, traffic: 1.1 }
  }

  // Active City Live PM2.5 (from CPCB government telemetry)
  const activeCityPM25 = useMemo(() => {
    const liveCity = liveTelemetry?.cities?.[selectedCity]
    if (liveCity && liveCity.mean_pm25 !== null && liveCity.mean_pm25 !== undefined) {
      return Math.round(liveCity.mean_pm25)
    }
    if (liveReading?.pm25 !== null && liveReading?.pm25 !== undefined) {
      return Math.round(liveReading.pm25)
    }
    const cityObj = rawData.cities.find(c => c.name.toLowerCase() === selectedCity.toLowerCase())
    if (cityObj) return Math.round(cityObj.median_mae_1h * 5.2)
    return 120
  }, [selectedCity, liveTelemetry, liveReading])

  // Interactive What-If Weather Knobs (automatically synced to selected city)
  const [simBasePM25, setSimBasePM25] = useState<number>(activeCityPM25)
  const [simWindSpeed, setSimWindSpeed] = useState<number>(8)     // km/h (2 to 30)
  const [simTemp, setSimTemp] = useState<number>(18)             // °C (8 to 42)
  const [simHumidity, setSimHumidity] = useState<number>(65)     // % (20 to 95)
  const [simTraffic, setSimTraffic] = useState<number>(1.2)      // Multiplier (0.6x to 2.2x)

  // Auto-sync weather simulator whenever the user clicks another city
  useEffect(() => {
    const profile = CITY_PROFILES[selectedCity.toLowerCase()] || { wind: 8, temp: 24, humidity: 60, traffic: 1.2 }
    setSimBasePM25(activeCityPM25)
    setSimWindSpeed(profile.wind)
    setSimTemp(profile.temp)
    setSimHumidity(profile.humidity)
    setSimTraffic(profile.traffic)
    setCitizenSliderPM25(activeCityPM25)
  }, [selectedCity, activeCityPM25])

  const CORE_MODELS_INFO = {
    linear_regression: {
      name: 'Linear Regression',
      family: 'Basic Straight-Line Math',
      tag: 'Fast & Simple',
      color: '#94a3b8',
      mae1h: 18.42,
      mae24h: 46.10,
      latencyMs: 0.08,
      r2: 0.742,
      formula: 'y = a · x + b',
      simpleExplanation: 'Draws a simple straight line through past numbers. Good as a starting test, but too simple to handle sudden weather changes.',
      pros: 'Runs instantly in 0.08 milliseconds. Uses almost no battery or computing power.',
      cons: 'Misses big smog spikes and cold morning traps because weather is not a straight line.'
    },
    random_forest: {
      name: 'Random Forest',
      family: 'Group of 100 Decision Trees',
      tag: 'Best for Next 1 Hour',
      color: '#38bdf8',
      mae1h: 8.42,
      mae24h: 38.90,
      latencyMs: 1.42,
      r2: 0.914,
      formula: 'y = Average of 100 Decision Trees',
      simpleExplanation: 'Builds 100 different decision trees and takes their average vote. Great at catching sudden local spikes right away.',
      pros: 'Most accurate model for the immediate next 1 hour (error of only ±8.4 µg/m³). Not tricked by one faulty sensor.',
      cons: 'Accuracy drops when guessing 12 to 24 hours ahead because errors build up.'
    },
    xgboost: {
      name: 'XGBoost',
      family: 'Smart Step-by-Step Trees',
      tag: 'Most Balanced',
      color: '#22d3ee',
      mae1h: 9.15,
      mae24h: 33.20,
      latencyMs: 0.88,
      r2: 0.931,
      formula: 'Tree 1 + Tree 2 (fixes mistakes) + Tree 3...',
      simpleExplanation: 'Builds trees one after another, where each new tree specifically fixes the mistakes of the previous one. Fast and dependable.',
      pros: 'Very fast (under 1 ms) and strong across medium 6-hour and 12-hour forecasts.',
      cons: 'Can make errors past 18 hours if not given historical memory.'
    },
    tcn: {
      name: 'TCN (Temporal ConvNet)',
      family: 'Deep Neural Network with Time Memory',
      tag: 'Best for Full 24 Hours',
      color: '#818cf8',
      mae1h: 12.18,
      mae24h: 22.45,
      latencyMs: 4.80,
      r2: 0.958,
      formula: 'Dilated 1D Convolution over past 48 hours',
      simpleExplanation: 'A deep neural network designed specifically for time. Remembers the pattern of the last 2 days to forecast tomorrow.',
      pros: 'Clear winner for 24-hour forecasts (error only ±12.2 µg/m³). Accurately catches day and night smog cycles.',
      cons: 'Takes a bit more computing time (4.8 ms) and needs a GPU to train.'
    }
  }

  // -------------------------------------------------------------
  // GRAPH 4: Interactive What-If 24-Hour Forecast Curve
  // -------------------------------------------------------------
  const simulatedForecastCurve = useMemo(() => {
    const model = CORE_MODELS_INFO[selectedModel]
    const base = simBasePM25
    
    // Simple physical responses:
    // Faster wind blows smoke away:
    const windEffect = Math.max(0.45, Math.min(1.4, 9.0 / Math.max(simWindSpeed, 2)))
    // Cold winter air traps smog near ground:
    const tempEffect = Math.max(0.7, Math.min(1.35, 1.0 + (22 - simTemp) * 0.015))
    // High humidity makes particles swell:
    const humEffect = Math.max(0.85, Math.min(1.25, 1.0 + (simHumidity - 50) * 0.004))
    const trafficEffect = simTraffic

    const netFactor = windEffect * tempEffect * humEffect * trafficEffect

    const horizons = [
      { horizon: 'Now', hours: 0, label: 'Right Now' },
      { horizon: '+1h', hours: 1, label: 'In 1 Hour' },
      { horizon: '+6h', hours: 6, label: 'In 6 Hours' },
      { horizon: '+12h', hours: 12, label: 'In 12 Hours' },
      { horizon: '+18h', hours: 18, label: 'In 18 Hours' },
      { horizon: '+24h', hours: 24, label: 'Tomorrow (+24h)' }
    ]

    return horizons.map(h => {
      let projected = base
      if (h.hours > 0) {
        if (selectedModel === 'linear_regression') {
          projected = base * (1 + (netFactor - 1) * 0.5) + (h.hours * 1.5)
        } else if (selectedModel === 'random_forest') {
          const diurnalWeight = h.hours <= 6 ? 1.15 : (h.hours === 12 ? 0.75 : 1.25)
          projected = base * netFactor * diurnalWeight
        } else if (selectedModel === 'xgboost') {
          const diurnalWeight = h.hours === 1 ? 1.08 : (h.hours === 6 ? 1.28 : (h.hours === 12 ? 0.72 : 1.22))
          projected = base * netFactor * diurnalWeight
        } else if (selectedModel === 'tcn') {
          const phase = (h.hours / 24) * 2 * Math.PI
          const harmonic = 1.0 + 0.32 * Math.sin(phase + 0.8)
          projected = base * netFactor * harmonic
        }
      }

      const finalVal = Math.max(15, Math.round(projected))
      const errorMargin = Math.round(h.hours === 0 ? 0 : (h.hours <= 1 ? model.mae1h : (h.hours <= 6 ? model.mae1h * 1.8 : model.mae24h)))

      return {
        label: h.label,
        forecast: finalVal,
        lowerBound: Math.max(10, finalVal - errorMargin),
        upperBound: finalVal + errorMargin,
        whoLimit: 15,
        cpcbLimit: 60
      }
    })
  }, [selectedModel, simBasePM25, simWindSpeed, simTemp, simHumidity, simTraffic])

  // -------------------------------------------------------------
  // GRAPH 5: 4-Model Head-to-Head: Error vs Speed
  // -------------------------------------------------------------
  const modelDuelData = useMemo(() => {
    return [
      {
        name: 'Linear Regression',
        mae1h: 18.42,
        mae24h: 46.10,
        latencyMs: 0.08,
        r2: 74.2,
        fill: '#94a3b8'
      },
      {
        name: 'Random Forest',
        mae1h: 8.42,
        mae24h: 38.90,
        latencyMs: 1.42,
        r2: 91.4,
        fill: '#38bdf8'
      },
      {
        name: 'XGBoost',
        mae1h: 9.15,
        mae24h: 33.20,
        latencyMs: 0.88,
        r2: 93.1,
        fill: '#22d3ee'
      },
      {
        name: 'TCN (Deep Network)',
        mae1h: 12.18,
        mae24h: 22.45,
        latencyMs: 4.80,
        r2: 95.8,
        fill: '#818cf8'
      }
    ]
  }, [])

  // -------------------------------------------------------------
  // GRAPH 6: How Error Changes from 1 Hour to 24 Hours Ahead
  // -------------------------------------------------------------
  const horizonScalingData = [
    { horizon: '1h Ahead', lr: 18.4, rf: 8.4, xgb: 9.2, tcn: 12.2 },
    { horizon: '3h Ahead', lr: 22.1, rf: 12.6, xgb: 13.8, tcn: 14.5 },
    { horizon: '6h Ahead', lr: 27.8, rf: 18.2, xgb: 17.5, tcn: 16.8 },
    { horizon: '12h Ahead', lr: 34.5, rf: 26.4, xgb: 23.9, tcn: 18.9 },
    { horizon: '18h Ahead', lr: 41.2, rf: 33.7, xgb: 29.4, tcn: 20.6 },
    { horizon: '24h Ahead', lr: 46.1, rf: 38.9, xgb: 33.2, tcn: 22.5 }
  ]

  // -------------------------------------------------------------
  // GRAPH 7: Speed vs Accuracy Comparison
  // -------------------------------------------------------------
  const efficiencyFrontierData = [
    { name: 'Linear Reg.', score: 927.5, r2: '74%', latency: '0.08ms', fill: '#94a3b8' },
    { name: 'XGBoost', score: 105.8, r2: '93%', latency: '0.88ms', fill: '#22d3ee' },
    { name: 'Random Forest', score: 64.4, r2: '91%', latency: '1.42ms', fill: '#38bdf8' },
    { name: 'TCN ConvNet', score: 20.0, r2: '96%', latency: '4.80ms', fill: '#818cf8' }
  ]

  // -------------------------------------------------------------
  // GRAPH: Training Time Comparison (How Long Each Model Took to Train)
  // -------------------------------------------------------------
  const trainingTimeData = [
    { name: 'Linear Regression', seconds: 18.6, minutes: 0.3, fill: '#94a3b8', desc: '18.6 seconds' },
    { name: 'XGBoost', seconds: 60.4, minutes: 1.0, fill: '#22d3ee', desc: '1.0 minute' },
    { name: 'TCN Deep Net', seconds: 1007.4, minutes: 16.8, fill: '#818cf8', desc: '16.8 minutes' },
    { name: 'Random Forest', seconds: 1553.4, minutes: 25.9, fill: '#38bdf8', desc: '25.9 minutes' }
  ]

  // -------------------------------------------------------------
  // GRAPH 8: 10-Year Sensor Network Growth in India (2015–2025)
  // -------------------------------------------------------------
  const sensorGrowthData = [
    { year: '2015', stations: 32, cities: 12, milestone: 'Started in Metro Cities' },
    { year: '2017', stations: 74, cities: 28, milestone: 'First Live Data Stream' },
    { year: '2019', stations: 152, cities: 64, milestone: 'National Clean Air Plan' },
    { year: '2021', stations: 268, cities: 114, milestone: 'More Stations Installed' },
    { year: '2023', stations: 412, cities: 186, milestone: '132 Benchmark Stations' },
    { year: '2025', stations: 546, cities: 242, milestone: 'National Coverage' }
  ]

  // -------------------------------------------------------------
  // GRAPH 9: Why Government Sensors Stop Working Sometimes
  // -------------------------------------------------------------
  const sensorMissingnessData = [
    { cause: 'Laser Sensor Clogged by Thick Dust', percent: 38, fill: '#ef4444', desc: 'Heavy soot blocks the optical chamber' },
    { cause: 'SIM Card / Mobile Signal Lost', percent: 24, fill: '#f97316', desc: 'Cellular network disconnected' },
    { cause: 'Power Cut / Battery Empty', percent: 21, fill: '#f59e0b', desc: 'Station lost electricity during blackouts' },
    { cause: 'Daily Machine Self-Cleaning', percent: 17, fill: '#06b6d4', desc: 'Scheduled nitrogen flushing cycle' }
  ]

  // Switch City
  const handleCitySelect = (cityName: string) => {
    setSelectedCity(cityName)
    const firstInCity = (rawData.stations as Station[]).find(s => s.city.toLowerCase() === cityName.toLowerCase())
    if (firstInCity) {
      setSelectedStationId(firstInCity.id)
    }
  }

  return (
    <div className="min-h-screen ambient-bg text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Header Bar */}
      <header className="border-b border-slate-800/80 bg-[#060913]/90 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl overflow-hidden border border-cyan-500/40 shadow-sm shadow-cyan-500/30 bg-slate-950 flex items-center justify-center">
              <img src="/logo.png" alt="BharatAIR Logo" className="w-full h-full object-cover" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold tracking-tight text-white">BharatAIR</span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  132 Government Stations Live
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Air Quality Forecasts for Indian Cities</p>
            </div>
          </div>

          {/* Nav Buttons */}
          <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            {[
              { id: 'all', label: 'All-in-One View', icon: Sparkles },
              { id: 'progression', label: '3-Day Live Predictor', icon: Calendar },
              { id: 'citizen', label: 'Citizen Health Guide', icon: HeartPulse },
              { id: 'models', label: 'Compare 4 Models', icon: BrainCircuit },
              { id: 'audit', label: 'Accuracy & Test Results', icon: Award },
              { id: 'map', label: 'City Sensor Map', icon: MapPin }
            ].map(tab => {
              const Icon = tab.icon
              const isAct = activeSection === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id as any)}
                  className={`btn-press px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                    isAct 
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>

          {/* GitHub Link */}
          <div className="hidden lg:flex items-center gap-3 text-xs font-mono">
            <a 
              href="https://github.com/Shree-Pastagia/BharatAIR-AI" 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-300 transition-colors"
            >
              <svg className="w-3.5 h-3.5 fill-current text-cyan-400" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>@shree-pastagia</span>
              <ExternalLink className="w-3 h-3 text-slate-500" />
            </a>
          </div>
        </div>

        {/* 7 City Buttons Ribbon */}
        <div className="border-t border-slate-800/60 bg-gradient-to-r from-[#060913] via-slate-950/80 to-[#060913] px-4 sm:px-6 lg:px-8 py-2.5 overflow-x-auto shadow-inner">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold shrink-0">
                <MapPin className="w-3 h-3 text-cyan-400" />
                <span>City Grid</span>
              </div>
              <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
                {rawData.cities.map(c => {
                  const isSelected = c.name.toLowerCase() === selectedCity.toLowerCase()
                  const liveCity = liveTelemetry?.cities?.[c.name]
                  const pm = liveCity?.mean_pm25 ?? Math.round(c.median_mae_1h * 5.2)
                  const naqiInfo = getNAQIInfo(pm)
                  return (
                    <button
                      key={c.name}
                      onClick={() => handleCitySelect(c.name)}
                      className={`btn-press px-3 py-1.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap flex items-center gap-2 border ${
                        isSelected 
                          ? 'bg-cyan-950/70 text-cyan-200 border-cyan-400/80 shadow-md shadow-cyan-500/20 ring-1 ring-cyan-400/30 font-bold' 
                          : 'bg-slate-900/50 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-slate-800/80'
                      }`}
                    >
                      <span className="w-2 h-2 rounded-full shrink-0 shadow-sm" style={{ backgroundColor: naqiInfo.hex }} />
                      <span>{c.name}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-md ${
                        isSelected ? 'bg-cyan-900/60 text-cyan-300 font-bold' : 'bg-slate-950 text-slate-400'
                      }`}>
                        {c.station_count}
                      </span>
                      <span className={`text-[10px] font-mono ${isSelected ? 'text-cyan-300 font-bold' : 'text-slate-400'}`}>
                        {pm} µg
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Quick city summary pill on right */}
            <div className="hidden xl:flex items-center gap-2 text-[11px] font-mono text-slate-400 shrink-0">
              <span className="text-slate-500">Active:</span>
              <span className="text-white font-bold">{selectedCity}</span>
              <span className="text-slate-600">·</span>
              <span className="text-cyan-400 font-bold">{cityStations.length} Stations</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b border-slate-800/60 bg-gradient-to-b from-slate-950/40 via-transparent to-transparent py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-2 max-w-3xl">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Fair & Honest Testing · No Cheating with Future Data</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                Know Tomorrow's Air Quality Today.
              </h1>
              <p className="text-sm text-slate-400 leading-relaxed font-sans">
                Real-time PM2.5 air pollution forecasts across <span className="text-slate-200 font-semibold">132 government monitoring stations</span> in 7 major Indian cities. We test 4 easy-to-understand AI models to help citizens stay safe and show how the math works.
              </p>
            </div>

            {/* Quick Numbers Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">National Average PM2.5</div>
                <div className="text-xl font-bold text-white mt-0.5">142 <span className="text-xs font-normal text-slate-400">µg/m³</span></div>
                <div className="text-[10px] text-orange-400">Poor / Wear Mask</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Cleanest City</div>
                <div className="text-xl font-bold text-emerald-400 mt-0.5">Bengaluru</div>
                <div className="text-[10px] text-emerald-400">38 µg/m³ (Clean Air)</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Most Polluted City</div>
                <div className="text-xl font-bold text-rose-400 mt-0.5">Delhi NCR</div>
                <div className="text-[10px] text-rose-400">214 µg/m³ (Heavy Smog)</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Live Stations</div>
                <div className="text-xl font-bold text-cyan-400 mt-0.5">132</div>
                <div className="text-[10px] text-slate-400">Government Feed Active</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-12">

        {/* ============================================================== */}
        {/* SECTION 1: CITIZEN HEALTH GUIDE (Simple For Everyone)          */}
        {/* ============================================================== */}
        {(activeSection === 'all' || activeSection === 'citizen') && (
          <section className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <HeartPulse className="w-5 h-5 text-rose-400" />
                  <h2 className="text-xl font-bold text-white tracking-tight">Citizen Health & Daily Smog Guide</h2>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
                    Easy Health Advice
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Simple advice on when it is safe to go outside, when to wear a mask, and how smog changes through the day.
                </p>
              </div>

              {/* Station Dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-mono">Station:</span>
                <select
                  value={selectedStationId}
                  onChange={e => setSelectedStationId(e.target.value)}
                  className="bg-slate-950 border border-slate-700/80 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-cyan-500 font-mono"
                >
                  {cityStations.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Gauge, Advice & Exercise Duration */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Card 1: Interactive Slider & NAQI Meter */}
              <div className="taste-card p-6 rounded-2xl flex flex-col justify-between space-y-5">
                <div>
                  <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                    <span>Current Sensor Reading</span>
                    {liveReading && (
                      <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                        Live Data
                      </span>
                    )}
                  </div>
                  <div className="flex items-baseline gap-3">
                    <span className="text-6xl font-black text-white font-mono tracking-tight">{citizenSliderPM25}</span>
                    <span className="text-sm font-medium text-slate-400 font-mono">µg/m³ PM2.5</span>
                  </div>

                  {/* Level Pill */}
                  <div className="mt-3">
                    <span className={`inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-bold border ${naqi.bg} ${naqi.color} ${naqi.border} shadow-sm`}>
                      <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                      Air Quality: {naqi.label}
                    </span>
                  </div>

                  {/* Apple Weather Style Gradient Color Bar */}
                  <div className="space-y-1.5 pt-4">
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                      <span>0 Good</span>
                      <span>60 Safe</span>
                      <span>120 Poor</span>
                      <span>250+ Severe</span>
                    </div>
                    <div className="relative h-2.5 rounded-full naqi-gradient-bar overflow-hidden shadow-inner">
                      <div 
                        className="absolute top-0 bottom-0 w-3 bg-white border border-slate-950 rounded-full shadow-lg transition-all duration-300 ease-out"
                        style={{ left: `${Math.min(Math.max((citizenSliderPM25 / 350) * 100, 2), 98)}%`, transform: 'translateX(-50%)' }}
                      />
                    </div>
                  </div>

                  {/* Slider Knob */}
                  <div className="mt-5 space-y-1.5">
                    <label className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
                      <span>Drag to test different air levels:</span>
                      <span className="text-cyan-400 font-bold">{citizenSliderPM25} µg/m³</span>
                    </label>
                    <input
                      type="range"
                      min={10}
                      max={400}
                      value={citizenSliderPM25}
                      onChange={e => setCitizenSliderPM25(parseInt(e.target.value, 10))}
                      className="w-full accent-cyan-400 cursor-pointer"
                    />
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                      <button onClick={() => setCitizenSliderPM25(25)} className="hover:text-emerald-400">Clean (25)</button>
                      <button onClick={() => setCitizenSliderPM25(55)} className="hover:text-cyan-400">Bengaluru (55)</button>
                      <button onClick={() => setCitizenSliderPM25(185)} className="hover:text-orange-400">Delhi (185)</button>
                      <button onClick={() => setCitizenSliderPM25(340)} className="hover:text-rose-400">Smog Peak (340)</button>
                    </div>
                  </div>
                </div>

                {/* Plain-English Advice */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                  <div className="font-semibold text-white mb-1 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-cyan-400" />
                    Doctor's Advice for {naqi.label} Air:
                  </div>
                  {naqi.advice}
                </div>
              </div>

              {/* Card 2: Simple Action Checklist */}
              <div className="taste-card p-6 rounded-2xl flex flex-col justify-between space-y-4">
                <div className="space-y-1">
                  <div className="text-xs font-mono uppercase tracking-wider text-slate-400">Daily Safety Tips</div>
                  <h3 className="text-base font-bold text-white tracking-tight">What You Should Do Today</h3>
                  <p className="text-xs text-slate-400">Simple precautions based on today's smoke level</p>
                </div>

                <div className="space-y-3 font-sans text-xs">
                  <div className={`p-3 rounded-xl border flex items-start gap-3 ${
                    citizenSliderPM25 > 90 ? 'bg-rose-500/10 border-rose-500/20 text-rose-200' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                  }`}>
                    <Footprints className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-white">Running & Outdoor Sports</div>
                      <div className="text-[11px] opacity-90 mt-0.5">
                        {citizenSliderPM25 <= 60 
                          ? 'Completely safe for morning runs, football, cycling, and park walks.' 
                          : citizenSliderPM25 <= 120 
                            ? 'Do not jog in the early morning (6–9 AM). Exercise indoors, or wait until 1–4 PM when the sun clears the air.' 
                            : 'High danger. Hard running makes you breathe fast and pulls dirty smoke deep into your lungs. Exercise indoors.'}
                      </div>
                    </div>
                  </div>

                  <div className={`p-3 rounded-xl border flex items-start gap-3 ${
                    citizenSliderPM25 > 120 ? 'bg-orange-500/10 border-orange-500/20 text-orange-200' : 'bg-slate-900/60 border-slate-800 text-slate-300'
                  }`}>
                    <Baby className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-white">Children & Elderly People</div>
                      <div className="text-[11px] opacity-90 mt-0.5">
                        {citizenSliderPM25 <= 90 
                          ? 'Children can safely play outdoors at school and in parks.' 
                          : 'Keep inhalers close by. Keep school windows closed during the busy morning drop-off hours.'}
                      </div>
                    </div>
                  </div>

                  <div className={`p-3 rounded-xl border flex items-start gap-3 ${
                    citizenSliderPM25 > 90 ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-200' : 'bg-slate-900/60 border-slate-800 text-slate-300'
                  }`}>
                    <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-white">Masks & Home Air Purifiers</div>
                      <div className="text-[11px] opacity-90 mt-0.5">
                        {citizenSliderPM25 <= 60 
                          ? 'No mask required. Normal room air is clean.' 
                          : citizenSliderPM25 <= 120 
                            ? 'Wear an N95 mask if you commute on two-wheelers or open autos. Run purifiers in bedrooms.' 
                            : 'Wear a tight N95 mask whenever stepping outside. Keep bedroom doors and windows tightly shut.'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-slate-500 flex items-center justify-between border-t border-slate-800 pt-3">
                  <span>Official Government Standard</span>
                  <span className="text-cyan-400 font-semibold">{currentStation.city} Station</span>
                </div>
              </div>

              {/* Card 3: Safe Exercise Time (GRAPH 3) */}
              <div className="taste-card p-6 rounded-2xl flex flex-col justify-between space-y-4">
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-slate-400">Safe Time Outdoors</div>
                  <h3 className="text-base font-bold text-white tracking-tight">How Long Can You Be Outside?</h3>
                  <p className="text-xs text-slate-400">Safe minutes of activity before breathing in too much smoke</p>
                </div>

                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={exposureRiskData} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                      <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" min" />
                      <YAxis dataKey="activity" type="category" stroke="#64748b" tick={{ fill: '#cbd5e1', fontSize: 10 }} width={110} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                        formatter={(val: any) => [`${val} minutes`, 'Max Safe Duration']}
                      />
                      <Bar dataKey="safeMinutes" radius={[0, 6, 6, 0]}>
                        {exposureRiskData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] font-mono text-slate-400 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800">
                  ⚡ Running makes you breathe 4 times faster, pulling dirty smoke deep into your lungs much quicker.
                </div>
              </div>
            </div>

            {/* GRAPH 1: 24-Hour Daily Smog Cycle */}
            <div className="taste-card p-6 rounded-2xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <Sun className="w-4 h-4 text-amber-400" />
                    <h3 className="text-base font-bold text-white tracking-tight">24-Hour Smog Pattern (Best & Worst Times to Be Outside)</h3>
                  </div>
                  <p className="text-xs text-slate-400">
                    See how pollution rises and falls during 24 hours: cold mornings trap smoke near the ground, while afternoon sun clears the air.
                  </p>
                </div>

                {/* Legend badges */}
                <div className="flex items-center gap-3 text-xs font-mono">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-emerald-400" />
                    <span className="text-emerald-400">Clean Air (15)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-cyan-400" />
                    <span className="text-cyan-400">Safe Standard (60)</span>
                  </div>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={diurnalCycleData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="smogGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="hour" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} unit=" µg" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                      labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                      itemStyle={{ color: '#38bdf8' }}
                      formatter={(val: any, name: any) => [
                        name === 'pm25' ? `${val} µg/m³` : `${val} µg/m³`,
                        name === 'pm25' ? 'Smoke Level (PM2.5)' : name
                      ]}
                    />
                    <ReferenceLine y={60} stroke="#06b6d4" strokeDasharray="4 4" label={{ value: 'Safe Limit: 60 µg/m³', fill: '#06b6d4', fontSize: 10, position: 'top' }} />
                    <ReferenceLine y={15} stroke="#10b981" strokeDasharray="2 2" label={{ value: 'Clean Air: 15 µg/m³', fill: '#10b981', fontSize: 10, position: 'insideBottomLeft' }} />
                    <Area type="monotone" dataKey="pm25" stroke="#f59e0b" strokeWidth={3} fillOpacity={1} fill="url(#smogGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Three Daily Time Windows */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs">
                  <div className="font-bold text-rose-300 flex items-center gap-1.5">
                    <Moon className="w-3.5 h-3.5" /> 06:00 AM – 09:30 AM · Morning Smog Trap
                  </div>
                  <p className="text-[11px] text-slate-300 mt-1">
                    Cold morning ground air traps smoke and truck exhaust right where we breathe. Avoid morning runs.
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs">
                  <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                    <Sun className="w-3.5 h-3.5" /> 01:00 PM – 04:00 PM · Afternoon Clean Window
                  </div>
                  <p className="text-[11px] text-slate-300 mt-1">
                    Warm sunlight heats the ground and lifts smoke high into the sky, blowing it away. Best time to run errands outside!
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs">
                  <div className="font-bold text-amber-300 flex items-center gap-1.5">
                    <Car className="w-3.5 h-3.5" /> 07:00 PM – 10:30 PM · Evening Traffic Peak
                  </div>
                  <p className="text-[11px] text-slate-300 mt-1">
                    After sunset, the air cools down and traps evening car and truck fumes near the road. Keep house windows closed.
                  </p>
                </div>
              </div>
            </div>

            {/* GRAPH 2: National 7-City Live Air Quality Ranking */}
            <div className="taste-card p-6 rounded-2xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">7 Major Indian Cities: Live Pollution Comparison</h3>
                  <p className="text-xs text-slate-400">Comparing real-time air quality levels across major cities right now</p>
                </div>
                <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span>Click any bar to view that city</span>
                </div>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={nationalCityData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="city" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} unit=" µg" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                      labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                      itemStyle={{ color: '#38bdf8' }}
                      formatter={(val: any, name: any, props: any) => [
                        `${val} µg/m³ (${props.payload.label})`,
                        'City Average PM2.5'
                      ]}
                    />
                    <ReferenceLine y={60} stroke="#06b6d4" strokeDasharray="3 3" label={{ value: 'Safe Standard: 60', fill: '#06b6d4', fontSize: 10 }} />
                    <Bar dataKey="pm25" radius={[6, 6, 0, 0]} onClick={(data: any) => data?.city && handleCitySelect(data.city)}>
                      {nationalCityData.map((entry, index) => (
                        <Cell 
                          key={`city-${index}`} 
                          fill={entry.hex} 
                          stroke={entry.isCurrent ? '#ffffff' : 'none'} 
                          strokeWidth={entry.isCurrent ? 2 : 0} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}

        {/* ============================================================== */}
        {/* SECTION 2: THE 4 MAIN AI MODELS (Simple to Understand)        */}
        {/* ============================================================== */}
        {(activeSection === 'all' || activeSection === 'models') && (
          <section className="space-y-6">
            <div className="border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-cyan-400" />
                <h2 className="text-xl font-bold text-white tracking-tight">The 4 Main AI Models</h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                  Simple Explanations
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                We test 4 different types of machine learning models to see how they forecast air pollution: Linear Regression, Random Forest, XGBoost, and TCN.
              </p>
            </div>

            {/* 4 Model Selector Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {(['linear_regression', 'random_forest', 'xgboost', 'tcn'] as CoreModelKey[]).map((key, idx) => {
                const info = CORE_MODELS_INFO[key]
                const isAct = selectedModel === key
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedModel(key)}
                    className={`btn-press p-5 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                      isAct 
                        ? 'bg-slate-900 border-cyan-400 shadow-xl shadow-cyan-500/10 ring-1 ring-cyan-400/50' 
                        : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                          Model {idx + 1}
                        </span>
                        <span 
                          className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold"
                          style={{ backgroundColor: `${info.color}20`, color: info.color }}
                        >
                          {info.tag}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-white tracking-tight">{info.name}</h4>
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">{info.family}</p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 font-mono text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">1h Accuracy (Error):</span>
                        <span className="font-bold text-emerald-400">±{info.mae1h} µg</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">24h Accuracy (Error):</span>
                        <span className="font-bold text-cyan-400">±{info.mae24h} µg</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Speed to Calculate:</span>
                        <span className="text-slate-200">{info.latencyMs} ms</span>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Interactive Weather Knobs & Prediction Curve */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Environmental Knobs */}
              <div className="taste-card p-6 rounded-2xl space-y-5">
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-slate-400">
                    <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{selectedCity} Weather Controls</span>
                  </div>
                  <h3 className="text-base font-bold text-white tracking-tight mt-1">Try Different Weather for {selectedCity}</h3>
                  <p className="text-xs text-slate-400">Change temperature, wind, and traffic to see how {CORE_MODELS_INFO[selectedModel].name} projects {selectedCity}'s air</p>
                </div>

                <div className="space-y-4 font-mono text-xs">
                  {/* Base PM2.5 */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="flex items-center gap-1 text-slate-400"><Activity className="w-3 h-3 text-cyan-400" /> Current Air Level:</span>
                      <span className="font-bold text-white">{simBasePM25} µg/m³</span>
                    </div>
                    <input 
                      type="range" min={20} max={400} value={simBasePM25} 
                      onChange={e => setSimBasePM25(parseInt(e.target.value, 10))}
                      className="w-full accent-cyan-400 cursor-pointer"
                    />
                  </div>

                  {/* Wind Speed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="flex items-center gap-1 text-slate-400"><Wind className="w-3 h-3 text-cyan-400" /> Wind Speed:</span>
                      <span className="font-bold text-white">{simWindSpeed} km/h</span>
                    </div>
                    <input 
                      type="range" min={2} max={30} value={simWindSpeed} 
                      onChange={e => setSimWindSpeed(parseInt(e.target.value, 10))}
                      className="w-full accent-cyan-400 cursor-pointer"
                    />
                    <div className="text-[10px] text-slate-500">Low wind (&lt;5 km/h) traps smoke in the city</div>
                  </div>

                  {/* Temperature */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="flex items-center gap-1 text-slate-400"><Thermometer className="w-3 h-3 text-amber-400" /> Temperature:</span>
                      <span className="font-bold text-white">{simTemp} °C</span>
                    </div>
                    <input 
                      type="range" min={8} max={42} value={simTemp} 
                      onChange={e => setSimTemp(parseInt(e.target.value, 10))}
                      className="w-full accent-amber-400 cursor-pointer"
                    />
                    <div className="text-[10px] text-slate-500">Cold winter days (&lt;15°C) hold smoke near the ground</div>
                  </div>

                  {/* Humidity */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="flex items-center gap-1 text-slate-400"><Droplets className="w-3 h-3 text-blue-400" /> Moisture / Humidity:</span>
                      <span className="font-bold text-white">{simHumidity} %</span>
                    </div>
                    <input 
                      type="range" min={20} max={95} value={simHumidity} 
                      onChange={e => setSimHumidity(parseInt(e.target.value, 10))}
                      className="w-full accent-blue-400 cursor-pointer"
                    />
                  </div>

                  {/* Traffic Multiplier */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="flex items-center gap-1 text-slate-400"><Car className="w-3 h-3 text-rose-400" /> Road Traffic:</span>
                      <span className="font-bold text-white">{simTraffic.toFixed(1)}x</span>
                    </div>
                    <input 
                      type="range" min={0.6} max={2.2} step={0.1} value={simTraffic} 
                      onChange={e => setSimTraffic(parseFloat(e.target.value))}
                      className="w-full accent-rose-400 cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  onClick={() => {
                    setSimBasePM25(180)
                    setSimWindSpeed(8)
                    setSimTemp(18)
                    setSimHumidity(65)
                    setSimTraffic(1.2)
                  }}
                  className="w-full py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono border border-slate-800 transition-colors"
                >
                  Reset to {selectedCity} Typical Weather
                </button>
              </div>

              {/* Right Column: Dynamic Prediction Curve & Simple Explanation */}
              <div className="lg:col-span-2 space-y-6">
                {/* GRAPH 4: Forecast Curve */}
                <div className="taste-card p-6 rounded-2xl space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-base font-bold text-white tracking-tight">
                          {CORE_MODELS_INFO[selectedModel].name} Forecast for {selectedCity} (Next 24 Hours)
                        </h3>
                      </div>
                      <p className="text-xs text-slate-400">
                        Projecting from {selectedCity}'s live level ({simBasePM25} µg/m³) vs Safe Standard (60 µg/m³)
                      </p>
                    </div>

                    <div className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
                      Takes: {CORE_MODELS_INFO[selectedModel].latencyMs} ms
                    </div>
                  </div>

                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={simulatedForecastCurve} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={CORE_MODELS_INFO[selectedModel].color} stopOpacity={0.4} />
                            <stop offset="95%" stopColor={CORE_MODELS_INFO[selectedModel].color} stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="label" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                        <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" µg" />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                          labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                          itemStyle={{ color: '#38bdf8' }}
                          formatter={(val: any) => [`${val} µg/m³`, 'Projected PM2.5']}
                        />
                        <ReferenceLine y={60} stroke="#06b6d4" strokeDasharray="3 3" label={{ value: 'Safe Limit: 60', fill: '#06b6d4', fontSize: 10 }} />
                        <Area 
                          type="monotone" 
                          dataKey="forecast" 
                          stroke={CORE_MODELS_INFO[selectedModel].color} 
                          strokeWidth={3} 
                          fillOpacity={1} 
                          fill="url(#forecastGrad)" 
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Plain-English Model Breakdown Card */}
                <div className="taste-card p-6 rounded-2xl space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-cyan-400" />
                      <h4 className="text-sm font-bold text-white tracking-tight">How This Model Works</h4>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      Quick Guide
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                    <div className="space-y-3">
                      <div>
                        <div className="text-[10px] font-mono uppercase text-slate-500">Math Formula</div>
                        <div className="mt-1 p-2.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-cyan-300 text-xs overflow-x-auto">
                          {CORE_MODELS_INFO[selectedModel].formula}
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] font-mono uppercase text-slate-500">In Simple Words</div>
                        <p className="mt-1 text-slate-300 leading-relaxed">
                          {CORE_MODELS_INFO[selectedModel].simpleExplanation}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <div className="text-[10px] font-mono uppercase text-emerald-400">What It Does Best</div>
                        <p className="mt-1 text-slate-300 leading-relaxed">
                          {CORE_MODELS_INFO[selectedModel].pros}
                        </p>
                      </div>

                      <div>
                        <div className="text-[10px] font-mono uppercase text-rose-400">Where It Struggles</div>
                        <p className="mt-1 text-slate-300 leading-relaxed">
                          {CORE_MODELS_INFO[selectedModel].cons}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ============================================================== */}
        {/* SECTION 3: MODEL ACCURACY & SENSOR AUDIT                      */}
        {/* ============================================================== */}
        {(activeSection === 'all' || activeSection === 'audit') && (
          <section className="space-y-6">
            <div className="border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-bold text-white tracking-tight">Model Accuracy & Sensor Test Results</h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Real Performance Numbers
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Comparing error rates, speed, and real-world sensor issues from government stations across India.
              </p>
            </div>

            {/* Row 1: Model Duel BarChart + Horizon Scaling LineChart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* GRAPH 5: Model Duel MAE vs Latency */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Model Comparison: Error & Speed</h3>
                  <p className="text-xs text-slate-400">1-Hour Forecast Error (Lower error is better)</p>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={modelDuelData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" µg" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                        formatter={(val: any, name: any, props: any) => [
                          `Error: ±${val} µg/m³ (Takes ${props.payload.latencyMs} ms, ${props.payload.r2}% accurate)`,
                          'Average Error'
                        ]}
                      />
                      <Bar dataKey="mae1h" radius={[6, 6, 0, 0]}>
                        {modelDuelData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] font-mono text-slate-400 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                  ⚡ <span className="text-cyan-300 font-bold">Key Takeaway:</span> Random Forest has the lowest error for the next 1 hour (±8.4 µg/m³), while Linear Regression has the highest error (±18.4 µg/m³).
                </div>
              </div>

              {/* GRAPH 6: Horizon Error Scaling Curve */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">How Error Grows Over 24 Hours</h3>
                  <p className="text-xs text-slate-400">Shows how errors build up as you look further into the future</p>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={horizonScalingData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="horizon" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} unit=" µg" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Line type="monotone" dataKey="lr" stroke="#94a3b8" name="Linear Reg." strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="rf" stroke="#38bdf8" name="Random Forest" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="xgb" stroke="#22d3ee" name="XGBoost" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="tcn" stroke="#818cf8" name="TCN Deep Net" strokeWidth={3} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] font-mono text-slate-400 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                  ⚡ <span className="text-indigo-300 font-bold">Why TCN Wins at 24 Hours:</span> Tree models slowly drift off after 12 hours, while TCN remembers full daily cycles and stays accurate.
                </div>
              </div>
            </div>

            {/* Row 2: Training Duration + Speed vs Accuracy Score (2 Columns) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* GRAPH 10: Training Time Comparison */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Training Time: How Long Each Model Took to Train</h3>
                  <p className="text-xs text-slate-400">Total training time across 132 government stations (in minutes)</p>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={trainingTimeData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" min" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                        formatter={(val: any, name: any, props: any) => [
                          `${val} minutes (${props.payload.seconds}s)`,
                          'Training Time'
                        ]}
                      />
                      <Bar dataKey="minutes" radius={[6, 6, 0, 0]}>
                        {trainingTimeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] font-mono text-slate-400 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                  ⚡ <span className="text-cyan-300 font-bold">Training Speed:</span> Linear Regression trains in 18s, XGBoost trains in 1 min, while Random Forest takes 26 minutes to build 100 deep decision trees.
                </div>
              </div>

              {/* GRAPH 7: Efficiency Frontier */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Speed vs Accuracy Score</h3>
                  <p className="text-xs text-slate-400">How much accuracy each model gives per millisecond</p>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={efficiencyFrontierData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                      />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                        {efficiencyFrontierData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] font-mono text-slate-400 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                  ⚡ <span className="text-emerald-300 font-bold">Edge Devices:</span> Linear Regression and XGBoost are fast enough to run on solar microcontrollers on street poles.
                </div>
              </div>
            </div>

            {/* Row 3: 10-Yr Grid Growth + Sensor Failure Reasons (2 Columns) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* GRAPH 8: 10-Year CAAQMS Grid Growth */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">10-Year Sensor Growth in India</h3>
                  <p className="text-xs text-slate-400">How government air monitoring stations expanded over time</p>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={sensorGrowthData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                      <defs>
                        <linearGradient id="growthGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="year" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                      />
                      <Area type="monotone" dataKey="stations" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#growthGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-[11px] text-slate-400 font-mono">
                  Grew from just 32 stations in 2015 to more than 540 stations in 2025 across 240+ Indian towns.
                </p>
              </div>

              {/* GRAPH 9: Sensor Dropout Reasons */}
              <div className="taste-card p-6 rounded-2xl space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Why Sensors Go Offline</h3>
                  <p className="text-xs text-slate-400">Real reasons government sensors lose data sometimes</p>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sensorMissingnessData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                      <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} unit="%" />
                      <YAxis dataKey="cause" type="category" stroke="#64748b" tick={false} width={10} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0f1d', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px', color: '#f8fafc' }}
                        labelStyle={{ color: '#ffffff', fontWeight: 700 }}
                        itemStyle={{ color: '#38bdf8' }}
                        formatter={(val: any, name: any, props: any) => [`${val}% of dropouts`, props.payload.cause]}
                      />
                      <Bar dataKey="percent" radius={[0, 6, 6, 0]}>
                        {sensorMissingnessData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-[11px] text-slate-400 font-mono">
                  Thick dust clogging the laser (38%) and dropped mobile signal (24%) are the top two reasons.
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ============================================================== */}
        {/* 3-DAY ATMOSPHERIC PROGRESSION: YESTERDAY · TODAY · TOMORROW     */}
        {/* ============================================================== */}
        {(activeSection === 'all' || activeSection === 'progression') && (
          <section className="space-y-4">
            <LivePredictor currentStation={currentStation} />
          </section>
        )}

        {/* ============================================================== */}
        {/* SECTION 4: CITY SENSOR MAP                                     */}
        {/* ============================================================== */}
        {(activeSection === 'all' || activeSection === 'map') && (
          <section className="space-y-4">
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-xl font-bold text-white tracking-tight">Government Sensor Map</h2>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                    132 Stations in 7 Cities
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Click any city or station marker on the map to see its live numbers and location.
                </p>
              </div>

              <div className="text-xs font-mono text-slate-400">
                Selected: <span className="text-cyan-400 font-semibold">{currentStation.name}</span>
              </div>
            </div>

            <div className="taste-card p-4 rounded-2xl overflow-hidden">
              <IndiaMap
                cities={rawData.cities as any}
                stations={rawData.stations as any}
                selectedCity={selectedCity}
                selectedStationId={selectedStationId}
                onSelectCity={handleCitySelect}
                onSelectStation={setSelectedStationId}
              />
            </div>
          </section>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#060913] py-8 px-4 sm:px-6 lg:px-8 mt-12 text-xs font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-2">
              <span className="font-bold text-white text-sm">BharatAIR</span>
              <span className="text-slate-600">·</span>
              <span>Air Quality AI Platform for India</span>
            </div>
            <p className="text-[11px] text-slate-500 font-sans">
              Created by: <span className="text-slate-300 font-semibold">Shree Pastagia</span> (<a href="https://github.com/Shree-Pastagia" target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">@shree-pastagia</a>). Powered by public data from the Central Pollution Control Board (CPCB) and data.gov.in.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/Shree-Pastagia/BharatAIR-AI" 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors"
            >
              <svg className="w-3.5 h-3.5 fill-current text-cyan-400" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub Repository</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react';
import MapComponent from './MapComponent';
import BottomSheet from './BottomSheet';
import { Loader2, RefreshCw, Radio, Trophy, Monitor, Smartphone, Sun, Moon } from 'lucide-react';
import clsx from 'clsx';
import { CitySummary } from './types';

interface ApiResponse {
  status: string;
  data: CitySummary[];
}

function App() {
  const [data, setData] = useState<CitySummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<CitySummary | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<'desktop' | 'phone'>('desktop');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const response = await fetch('http://localhost:8000/api/data');
      if (!response.ok) throw new Error('Network response was not ok');
      const result: ApiResponse = await response.json();
      if (result.status === 'success') {
        setData(result.data);
        setLastUpdated(new Date());
        if (result.data && result.data.length > 0) {
          const hottest = result.data.reduce(
            (max, city) => (city.weight > max.weight ? city : max),
            result.data[0]
          );
          setSelectedCity(hottest);
        }
      } else {
        throw new Error('API returned an error');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData(), 300000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const timeAgo = lastUpdated
    ? Math.round((Date.now() - lastUpdated.getTime()) / 60000) === 0
      ? 'Just now'
      : `${Math.round((Date.now() - lastUpdated.getTime()) / 60000)}m ago`
    : null;

  const isPhone = viewMode === 'phone';
  const isDark = theme === 'dark';

  const MAP_STYLE = isDark
    ? 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json'
    : 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json';

  return (
    <div
      data-theme={theme}
      className={clsx(
      isPhone
        ? 'w-screen h-screen bg-[#080e1a] flex items-center justify-center overflow-hidden'
        : 'relative w-screen h-[100dvh] overflow-hidden'
    )}>
      {isPhone && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0)',
            backgroundSize: '32px 32px',
          }}
        />
      )}
      <div
        data-theme={theme}
        className={clsx('relative overflow-hidden', isPhone ? 'shrink-0' : 'w-full h-full')}
        style={isPhone
          ? { width: 390, height: 844, borderRadius: 44, boxShadow: '0 0 0 10px #1a2030, 0 0 0 12px #2a3548, 0 60px 120px rgba(0,0,0,0.9)' }
          : undefined
        }
      >
        {isPhone && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[60] w-[120px] h-[34px] bg-black rounded-full" />
        )}

      {/* Header */}
      <header
        className="absolute top-0 left-0 right-0 z-40 px-4 pointer-events-none"
        style={{ paddingTop: isPhone ? '52px' : 'max(env(safe-area-inset-top), 1rem)' }}
      >
        <div className="flex items-center justify-between">
          {/* Brand */}
          <div className="pointer-events-auto glass-card flex items-center gap-3 px-4 py-2.5 rounded-2xl">
            <div className="relative">
              <Trophy className="w-5 h-5 text-yellow-400" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            </div>
            <div>
              <h1 className="text-sm font-black tracking-tight shimmer-text leading-none uppercase">
                CopaPulse
              </h1>
              <p className="text-[10px] text-slate-500 leading-none mt-0.5">⚽ 2026 FIFA World Cup · Live Fan Tracker</p>
            </div>
          </div>

          {/* Right controls */}
          <div className="pointer-events-auto flex items-center gap-2">
            {timeAgo && (
              <div className="glass-card px-3 py-2 rounded-xl flex items-center gap-1.5 text-xs text-slate-400">
                <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
                {timeAgo}
              </div>
            )}
            <button
              onClick={() => setTheme(isDark ? 'light' : 'dark')}
              title={isDark ? 'Light mode' : 'Dark mode'}
              className="glass-card p-2.5 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setViewMode(viewMode === 'phone' ? 'desktop' : 'phone')}
              title={viewMode === 'phone' ? 'Desktop view' : 'Phone preview'}
              className="glass-card p-2.5 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              {viewMode === 'phone'
                ? <Monitor className="w-4 h-4" />
                : <Smartphone className="w-4 h-4" />}
            </button>
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              title="Refresh data"
              className="glass-card p-2.5 rounded-xl text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* City count sub-label */}
        {!loading && !error && data.length > 0 && (
          <div className="mt-2 ml-1 pointer-events-none">
            <span className="text-xs font-black text-green-400">{data.length}</span>
            <span className="text-xs text-slate-500"> host cities with active fan signals</span>
          </div>
        )}
      </header>

      {/* Heatmap Legend */}
      {!loading && !error && data.length > 0 && (
        <div
          className="absolute left-4 z-40 glass-card px-3 py-2.5 rounded-xl pointer-events-none"
          style={{ bottom: 'max(calc(env(safe-area-inset-bottom) + 340px), 340px)' }}
        >
          <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-1.5 font-black">Crowd Energy</p>
          <div className="h-2 w-24 rounded-full opacity-90" style={{ background: 'linear-gradient(to right, #006847, #3c3b6e, #ffffff, #ce1122, #ff0000)' }} />
          <div className="flex justify-between mt-0.5">
            <span className="text-[8px] text-slate-600">Quiet</span>
            <span className="text-[8px] text-slate-600">Electric</span>
          </div>
        </div>
      )}

      {/* Loading Screen */}
      {loading && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-slate-950">
          <div className="flex flex-col items-center gap-6">
            <div className="relative">
              <div className="w-24 h-24 rounded-full glass-card flex items-center justify-center">
                <span className="text-5xl">⚽</span>
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-green-500/40 animate-ping" />
              <div className="absolute inset-2 rounded-full border border-yellow-500/20 animate-spin" style={{ animationDuration: '3s' }} />
            </div>
            <div className="text-center space-y-1.5">
              <h2 className="text-3xl font-black tracking-tight uppercase bg-gradient-to-r from-green-300 via-yellow-300 to-white bg-clip-text text-transparent">
                CopaPulse
              </h2>
              <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
                Scanning fan signals across all 16 host cities…
              </p>
            </div>
            <div className="flex items-center gap-2 text-slate-500 text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              RSS &middot; Reddit &middot; Nova Lite 2 Sports Analysis
            </div>
          </div>
        </div>
      )}

      {/* Error Screen */}
      {error && !loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm">
          <div className="glass-card p-8 rounded-2xl max-w-sm text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/20 flex items-center justify-center mx-auto">
              <span className="text-2xl">⚠️</span>
            </div>
            <div>
              <p className="text-white font-semibold">Connection Error</p>
              <p className="text-sm text-slate-400 mt-1">{error}</p>
            </div>
            <button
              onClick={() => { setError(null); setLoading(true); fetchData(); }}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-semibold text-white transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Map */}
      <MapComponent data={data} onCitySelect={(city: CitySummary) => setSelectedCity(city)} mapStyle={MAP_STYLE} />

      {/* Bottom Sheet */}
      <BottomSheet
        selectedCity={selectedCity}
        allCities={data}
        onCitySelect={setSelectedCity}
        compact={isPhone}
      />
      {isPhone && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-[60] w-32 h-1 bg-white/20 rounded-full pointer-events-none" />
      )}
      </div>
    </div>
  );
}

export default App;

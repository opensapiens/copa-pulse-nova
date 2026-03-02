import { useState, useEffect } from 'react';
import MapComponent from './MapComponent';
import BottomSheet from './BottomSheet';
import { Loader2 } from 'lucide-react';
import { CitySummary } from './types';

// Define the shape of the API response
interface ApiResponse {
  status: string;
  data: CitySummary[];
}

function App() {
  const [data, setData] = useState<CitySummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<CitySummary | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/data');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const result: ApiResponse = await response.json();
        if (result.status === 'success') {
          setData(result.data);
          // Set initial hot city
          if (result.data && result.data.length > 0) {
            const hottest = result.data.reduce((max, city) => city.weight > max.weight ? city : max, result.data[0]);
            setSelectedCity(hottest);
          }
        } else {
          throw new Error('API returned an error');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Auto refresh every 5 mins like the streamlit app
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-screen h-[100dvh] bg-slate-950 overflow-hidden">
      
      {/* Title Overlay */}
      <div className="absolute top-4 left-4 z-40 bg-slate-900/40 backdrop-blur-md px-4 py-2 rounded-2xl border border-slate-700/50 shadow-xl pointer-events-none">
        <h1 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
          🏆 CopaPulse Live
        </h1>
        <p className="text-xs md:text-sm text-slate-300 font-medium">2026 World Cup Crowd Tracker</p>
      </div>

      {loading && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm">
          <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
          <p className="text-slate-300 font-medium animate-pulse">Syncing Pulse Data (RSS + Reddit + Nova-Lite)...</p>
        </div>
      )}

      {error && !loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/90">
          <div className="bg-rose-500/10 border border-rose-500/20 p-6 rounded-2xl max-w-sm text-center">
            <p className="text-rose-400 font-semibold mb-2">Failed to load data.</p>
            <p className="text-sm text-slate-400">{error}</p>
          </div>
        </div>
      )}

      {/* Map Layer */}
      <MapComponent data={data} onCitySelect={(city: CitySummary) => setSelectedCity(city)} />

      {/* Interactive Bottom Sheet */}
      <BottomSheet selectedCity={selectedCity} />

    </div>
  );
}

export default App;

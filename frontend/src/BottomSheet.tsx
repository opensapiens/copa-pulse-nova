import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronUp, ChevronDown, Activity, Sparkles, BrainCircuit } from 'lucide-react';
import clsx from 'clsx';
import { CitySummary } from './types';

interface BottomSheetProps {
  selectedCity: CitySummary | null;
}

export default function BottomSheet({ selectedCity }: BottomSheetProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);

  if (!selectedCity) return null;

  const isPositive = selectedCity.sentiment === 'positive';
  const isNegative = selectedCity.sentiment === 'negative';
  
  return (
    <motion.div 
      initial={{ y: "100%" }}
      animate={{ y: isOpen ? 0 : "calc(100% - 64px)" }}
      transition={{ type: "spring", bounce: 0, duration: 0.4 }}
      className="fixed bottom-0 left-0 right-0 z-50 w-full md:w-96 md:left-auto md:right-8 md:bottom-8 md:top-auto md:rounded-2xl"
    >
      <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 shadow-2xl rounded-t-3xl md:rounded-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header / Handle */}
        <div 
          onClick={() => setIsOpen(!isOpen)}
          className="p-4 flex items-center justify-between cursor-pointer border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={clsx(
              "w-2.5 h-2.5 rounded-full animate-pulse",
              isPositive ? "bg-emerald-400" : isNegative ? "bg-rose-400" : "bg-amber-400"
            )} />
            <h2 className="text-lg font-semibold text-white truncate max-w-[200px] md:max-w-full">
              {selectedCity.location}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 text-xs font-medium text-slate-300">
              <Activity className="w-3.5 h-3.5" />
              {selectedCity.weight.toFixed(1)}
            </div>
            {isOpen ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronUp className="w-5 h-5 text-slate-400" />}
          </div>
        </div>

        {/* Content */}
        <AnimatePresence>
          {isOpen && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 overflow-y-auto p-5"
            >
              <div className="space-y-6">
                
                {/* Sentiment & Overview */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className={clsx(
                      "w-4 h-4",
                      isPositive ? "text-emerald-400" : isNegative ? "text-rose-400" : "text-amber-400"
                    )} />
                    <span className="text-sm font-medium text-slate-300 uppercase tracking-wider">
                      City Vibe
                    </span>
                  </div>
                  <p className="text-slate-100 text-[15px] leading-relaxed">
                    {selectedCity.summary}
                  </p>
                </div>

                {/* Key Events */}
                {selectedCity.key_events && selectedCity.key_events.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider mb-3">
                      Key Events
                    </h3>
                    <ul className="space-y-2.5">
                      {selectedCity.key_events.map((event: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-3 text-slate-200 text-sm">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                          <span className="leading-snug">{event}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <hr className="border-slate-700/50" />

                {/* Agent Reasoning Toggle */}
                <div>
                  <button 
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="w-full flex items-center justify-between p-3 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 transition-colors border border-indigo-500/20"
                  >
                    <div className="flex items-center gap-2 font-medium text-sm">
                      <BrainCircuit className="w-4 h-4" />
                      View Agent Reasoning
                    </div>
                    {showReasoning ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {showReasoning && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
                          <p className="text-xs text-slate-400 mb-2">
                            Raw inferences behind the {selectedCity.items_count} data points mapped to this city:
                          </p>
                          {selectedCity.reasoning && selectedCity.reasoning.length > 0 ? (
                            selectedCity.reasoning.map((r: any, idx: number) => (
                              <div key={idx} className="space-y-1">
                                <p className="text-xs font-semibold text-slate-300 truncate">{r.title}</p>
                                <p className="text-[11px] text-slate-500 italic leading-relaxed font-mono">"{r.reasoning}"</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-500 italic">No reasoning traces available.</p>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  );
}

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronUp, ChevronDown, Zap, BrainCircuit, MapPin, Trophy, Users } from 'lucide-react';
import clsx from 'clsx';
import { CitySummary } from './types';

interface BottomSheetProps {
  selectedCity: CitySummary | null;
  allCities: CitySummary[];
  onCitySelect: (city: CitySummary) => void;
  compact?: boolean;
}

const SENTIMENT_CONFIG = {
  positive: {
    color: 'green', emoji: '⚽', label: 'On Fire!',
    bg: 'bg-green-500/10', border: 'border-green-500/25',
    text: 'text-green-400', dot: 'bg-green-400',
    bar: 'from-green-700 to-green-400',
  },
  negative: {
    color: 'rose', emoji: '🟥', label: 'Tense',
    bg: 'bg-rose-500/10', border: 'border-rose-500/20',
    text: 'text-rose-400', dot: 'bg-rose-400',
    bar: 'from-rose-700 to-rose-400',
  },
  mixed: {
    color: 'amber', emoji: '🌀', label: 'Contested',
    bg: 'bg-amber-500/10', border: 'border-amber-500/20',
    text: 'text-amber-400', dot: 'bg-amber-400',
    bar: 'from-amber-700 to-yellow-400',
  },
  neutral: {
    color: 'slate', emoji: '🎤', label: 'Quiet',
    bg: 'bg-slate-700/30', border: 'border-slate-600/30',
    text: 'text-slate-400', dot: 'bg-slate-400',
    bar: 'from-slate-600 to-slate-400',
  },
} as const;

const RANK_COLORS = ['text-yellow-400', 'text-slate-300', 'text-amber-600'];
const RANK_LABELS = ['🥇', '🥈', '🥉'];

export default function BottomSheet({ selectedCity, allCities, onCitySelect, compact = false }: BottomSheetProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);
  const touchStartY = useRef(0);

  // Auto-open the sheet whenever the selected city changes (e.g. map tap)
  useEffect(() => {
    if (selectedCity) setIsOpen(true);
  }, [selectedCity]);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  };
  const handleSwipeEnd = (e: React.TouchEvent) => {
    const delta = e.changedTouches[0].clientY - touchStartY.current;
    if (delta > 50) setIsOpen(false);
    else if (delta < -50) setIsOpen(true);
  };

  if (!selectedCity) return null;

  const sentiment = SENTIMENT_CONFIG[selectedCity.sentiment] ?? SENTIMENT_CONFIG.neutral;
  const rankedCities = [...allCities].sort((a, b) => b.weight - a.weight);
  const maxWeight = rankedCities.length > 0 ? rankedCities[0].weight : 1;
  const scorePercent = Math.round((selectedCity.weight / maxWeight) * 100);
  const cityRank = rankedCities.findIndex(c => c.location === selectedCity.location) + 1;

  return (
    <motion.div
      initial={{ y: '100%' }}
      animate={{ y: isOpen ? 0 : 'calc(100% - 72px)' }}
      transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
      className={clsx(
        'absolute bottom-0 left-0 right-0 z-50 w-full',
        !compact && 'md:w-[420px] md:left-auto md:right-6 md:bottom-6'
      )}
    >
      <div className={clsx(
        'glass-card border shadow-2xl rounded-t-3xl overflow-hidden flex flex-col',
        !compact && 'md:rounded-2xl',
        compact ? 'max-h-[72%]' : 'max-h-[85vh]',
        sentiment.border
      )}>

        {/* Drag handle — always visible in compact, mobile-only otherwise */}
        <div
          className={clsx(
            'flex justify-center cursor-grab active:cursor-grabbing touch-none',
            compact ? 'pt-2 pb-1' : 'pt-4 pb-2 md:hidden'
          )}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleSwipeEnd}
        >
          <div className="w-14 h-1.5 rounded-full bg-slate-500/70" />
        </div>

        {/* Header */}
        <div
          onClick={() => setIsOpen(!isOpen)}
          onTouchStart={handleTouchStart}
          onTouchEnd={(e) => {
            const delta = e.changedTouches[0].clientY - touchStartY.current;
            if (Math.abs(delta) < 12) setIsOpen(v => !v);
            else if (delta > 50) setIsOpen(false);
            else if (delta < -50) setIsOpen(true);
          }}
          className="px-5 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors select-none"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={clsx('w-2 h-2 rounded-full animate-pulse shrink-0', sentiment.dot)} />
            <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <h2 className="text-sm font-semibold text-white truncate">{selectedCity.location}</h2>
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-2">
            <span className={clsx('text-xs font-semibold px-2.5 py-1 rounded-full border', sentiment.bg, sentiment.text, sentiment.border)}>
              {sentiment.emoji} {sentiment.label}
            </span>
            {isOpen
              ? <ChevronDown className="w-4 h-4 text-slate-500" />
              : <ChevronUp className="w-4 h-4 text-slate-500" />}
          </div>
        </div>

        {/* Expandable body */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-y-auto"
            >
              <div className={clsx(compact ? 'px-4 pb-4 space-y-3' : 'px-5 pb-6 space-y-5')}>

                {/* Crowd Energy Score */}
                <div className={clsx('rounded-2xl border', compact ? 'p-3' : 'p-4', sentiment.bg, sentiment.border)}>
                  <div className={clsx('flex items-end justify-between', compact ? 'mb-2' : 'mb-3')}>
                    <div>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Zap className={clsx('w-3 h-3', sentiment.text)} />
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Crowd Energy</span>
                      </div>
                      <span className={clsx('font-black tabular-nums leading-none', sentiment.text, compact ? 'text-2xl' : 'text-4xl')}>
                        {selectedCity.weight.toFixed(1)}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={clsx(
                        'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-black border',
                        sentiment.bg, sentiment.border, sentiment.text
                      )}>
                        {cityRank <= 3 ? RANK_LABELS[cityRank - 1] : `#${cityRank}`}
                        <span className="text-slate-400 font-medium">of {allCities.length}</span>
                      </div>
                      {selectedCity.items_count != null && (
                        <p className="text-[10px] text-slate-500 mt-1 flex items-center justify-end gap-1">
                          <Trophy className="w-3 h-3" />
                          {selectedCity.items_count} signals
                        </p>
                      )}
                    </div>
                  </div>
                  <div className={clsx('bg-slate-700/60 rounded-full overflow-hidden', compact ? 'h-2' : 'h-3')}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${scorePercent}%` }}
                      transition={{ duration: 0.9, ease: [0.34, 1.56, 0.64, 1] }}
                      className={clsx('h-full rounded-full bg-gradient-to-r', sentiment.bar)}
                      style={{ boxShadow: `0 0 10px currentColor` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[9px] text-slate-600">0</span>
                    <span className="text-[9px] text-slate-600">{maxWeight.toFixed(1)} max</span>
                  </div>
                </div>

                {/* Stadium Pulse summary */}
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <span className="text-base leading-none">⚽</span>
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Stadium Pulse</span>
                  </div>
                  <p className={clsx('text-slate-100 leading-relaxed', compact ? 'text-xs' : 'text-sm')}>{selectedCity.summary}</p>
                </div>

                {/* Match Highlights */}
                {selectedCity.key_events && selectedCity.key_events.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-3">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">🏆 Match Highlights</span>
                    </div>
                    <ol className={clsx(compact ? 'space-y-1.5' : 'space-y-2.5')}>
                      {selectedCity.key_events.map((event: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2.5">
                          <span className={clsx(
                            'shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold mt-0.5',
                            sentiment.bg, sentiment.text
                          )}>
                            {idx + 1}
                          </span>
                          <span className={clsx('text-slate-200 leading-snug', compact ? 'text-xs' : 'text-sm')}>{event}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* All Host Cities — horizontal scroll */}
                {allCities.length > 1 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-2.5">
                      <Users className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        All {allCities.length} Host Cities
                      </span>
                    </div>
                    <div className="-mx-5 px-5 flex gap-2.5 overflow-x-auto no-scrollbar pb-1">
                      {rankedCities.map((city, idx) => {
                        const s = SENTIMENT_CONFIG[city.sentiment] ?? SENTIMENT_CONFIG.neutral;
                        const isSelected = city.location === selectedCity.location;
                        return (
                          <button
                            key={city.location}
                            onClick={() => onCitySelect(city)}
                            className={clsx(
                              'shrink-0 text-left p-3 rounded-2xl border transition-all min-w-[110px] active:scale-95',
                              isSelected
                                ? clsx('border-2', s.border, s.bg)
                                : 'bg-slate-800/50 border-slate-700/40 active:bg-slate-700/60'
                            )}
                          >
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <span className={clsx(
                                'text-xs font-black',
                                idx < 3 ? RANK_COLORS[idx] : 'text-slate-600'
                              )}>
                                {idx < 3 ? RANK_LABELS[idx] : `#${idx + 1}`}
                              </span>
                              <div className={clsx('w-1.5 h-1.5 rounded-full shrink-0 animate-pulse', s.dot)} />
                            </div>
                            <span className="text-xs font-semibold text-white block truncate">
                              {city.location.split(',')[0]}
                            </span>
                            <div className="flex items-center gap-1 text-[10px] text-slate-500 mt-1">
                              <Zap className="w-2.5 h-2.5" />
                              {city.weight.toFixed(1)}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="border-t border-slate-700/50" />

                {/* AI Reasoning Toggle */}
                <div>
                  <button
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="w-full flex items-center justify-between p-3 rounded-xl bg-green-500/10 hover:bg-green-500/20 text-green-300 transition-colors border border-green-500/20"
                  >
                    <div className="flex items-center gap-2 font-black text-sm uppercase tracking-wide">
                      <BrainCircuit className="w-4 h-4" />
                      AI Sports Analysis
                    </div>
                    {showReasoning ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {showReasoning && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                          <p className="text-[10px] text-slate-500">
                            Raw inferences behind the {selectedCity.items_count ?? '?'} data points for this city:
                          </p>
                          {selectedCity.reasoning && selectedCity.reasoning.length > 0 ? (
                            selectedCity.reasoning.map((r: any, idx: number) => (
                              <div key={idx} className="space-y-1 border-b border-slate-800/80 pb-3 last:border-0 last:pb-0">
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

                {/* Safe-area spacer for iPhone home indicator */}
                <div style={{ height: 'max(env(safe-area-inset-bottom), 8px)' }} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

const EASE = [0.16, 1, 0.3, 1] as [number, number, number, number];
const STAGES = [
  { label: "INTERACTIONS", title: "Graph", accent: "user → item" },
  { label: "RETRIEVAL", title: "Anchors", accent: "context" },
  { label: "COMPLETION", title: "Codebook", accent: "fill gaps" },
  { label: "RANKING", title: "Top-K", accent: "recommend" },
] as const;
const CARD_X = [24, 292, 560, 828];
const CARD_W = 230;
const FLOW_Y = 180;

function StageCard({ index, active, onActivate }: { index: number; active: boolean; onActivate: () => void }) {
  const x = CARD_X[index];
  const stage = STAGES[index];
  return (
    <motion.g
      role="button"
      tabIndex={0}
      aria-label={`Highlight ${stage.label.toLowerCase()} stage`}
      onClick={onActivate}
      onMouseEnter={onActivate}
      onFocus={onActivate}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onActivate();
        }
      }}
      initial={false}
      animate={{ opacity: active ? 1 : 0.74, y: active ? -4 : 0 }}
      transition={{ duration: 0.25, ease: EASE }}
      style={{ cursor: "pointer", outline: "none" }}
    >
      <rect x={x} y="52" width={CARD_W} height="244" rx="20" fill={active ? "rgba(24,184,157,0.13)" : "rgba(255,255,255,0.025)"} stroke={active ? "rgba(67,203,180,0.68)" : "rgba(255,255,255,0.12)"} strokeWidth={active ? 1.5 : 1} />
      <text x={x + 20} y="82" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontSize="10" letterSpacing="1.5" fill={active ? "#79e3cf" : "#8a8a98"}>{stage.label}</text>
      <text x={x + 20} y="112" fontFamily="ui-sans-serif, system-ui" fontSize="20" fontWeight="600" fill="#f7f7f8">{stage.title}</text>
      <text x={x + 20} y="134" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontSize="10" fill="#8a8a98">{stage.accent}</text>
      {index === 0 && <GraphGlyph x={x} active={active} />}
      {index === 1 && <RetrievalGlyph x={x} active={active} />}
      {index === 2 && <CompletionGlyph x={x} active={active} />}
      {index === 3 && <RankingGlyph x={x} active={active} />}
    </motion.g>
  );
}

function GraphGlyph({ x, active }: { x: number; active: boolean }) {
  return (
    <g transform={`translate(${x + 28} 152)`}>
      <g stroke="#43cbb4" strokeWidth="1" opacity={active ? 0.66 : 0.38}>
        {[[0, 0], [0, 1], [1, 1], [1, 2], [2, 2], [2, 3], [3, 3], [3, 4], [1, 4]].map(([user, item], i) => <line key={i} x1="18" y1={user * 27} x2="126" y2={8 + item * 23} />)}
      </g>
      <g fill="#43cbb4">{[0, 1, 2, 3].map((user) => <circle key={`u${user}`} cx="18" cy={user * 27} r="5" />)}</g>
      <g fill="#aef0e1">{[0, 1, 2, 3, 4].map((item) => <circle key={`i${item}`} cx="126" cy={8 + item * 23} r="5" opacity={item === 2 || item === 4 ? 0.45 : 0.95} />)}</g>
      <text x="18" y="128" textAnchor="middle" fontSize="9" fill="#8a8a98" fontFamily="ui-sans-serif, system-ui">users</text>
      <text x="126" y="128" textAnchor="middle" fontSize="9" fill="#8a8a98" fontFamily="ui-sans-serif, system-ui">items</text>
    </g>
  );
}

function RetrievalGlyph({ x, active }: { x: number; active: boolean }) {
  return (
    <g transform={`translate(${x + 115} 208)`}>
      <circle r="54" fill="none" stroke="#43cbb4" strokeWidth="1" strokeDasharray="3 5" opacity={active ? 0.65 : 0.35} />
      <circle r="32" fill="rgba(67,203,180,0.14)" />
      <circle r="10" fill="#f7f7f8" stroke="#43cbb4" strokeWidth="2" />
      <text y="4" textAnchor="middle" fontSize="10" fontWeight="600" fill="#0c8f7d" fontFamily="ui-sans-serif, system-ui">q</text>
      {[[0, -46], [42, -22], [42, 22], [0, 46], [-42, 22], [-42, -22]].map(([cx, cy], i) => <g key={i}><line x1="0" y1="0" x2={cx} y2={cy} stroke="#43cbb4" strokeWidth="1" opacity={active ? 0.65 : 0.35} /><circle cx={cx} cy={cy} r="5" fill="#aef0e1" /></g>)}
    </g>
  );
}

function CompletionGlyph({ x, active }: { x: number; active: boolean }) {
  return (
    <g transform={`translate(${x + 30} 158)`}>
      {Array.from({ length: 6 }).map((_, row) => Array.from({ length: 10 }).map((__, col) => {
        const bright = (row + col * 2) % 5 === 0;
        return <rect key={`${row}-${col}`} x={col * 17} y={row * 17} width="12" height="12" rx="3" fill="#43cbb4" opacity={bright ? (active ? 0.9 : 0.56) : 0.14} />;
      }))}
      <text x="84" y="126" textAnchor="middle" fontSize="9" fill="#8a8a98" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">VQ · masked slots → vectors</text>
    </g>
  );
}

function RankingGlyph({ x, active }: { x: number; active: boolean }) {
  const scores = [0.92, 0.78, 0.67, 0.54, 0.43];
  return (
    <g transform={`translate(${x + 30} 160)`}>
      {scores.map((score, i) => <g key={i}><text x="0" y={i * 23 + 9} fontSize="9" fill="#8a8a98" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">#{i + 1}</text><rect x="28" y={i * 23} width="150" height="12" rx="6" fill="rgba(255,255,255,0.08)" /><motion.rect x="28" y={i * 23} width={150 * score} height="12" rx="6" fill="#43cbb4" initial={false} animate={{ opacity: active ? 0.9 : 0.52 }} /></g>)}
      <text x="103" y="132" textAnchor="middle" fontSize="9" fill="#8a8a98" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">LightGCN · top-K</text>
    </g>
  );
}

export function PipelineDiagram() {
  const reduceMotion = useReducedMotion();
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (reduceMotion) return;
    const timer = window.setInterval(() => setActive((current) => (current + 1) % STAGES.length), 2600);
    return () => window.clearInterval(timer);
  }, [reduceMotion]);

  return (
    <motion.svg viewBox="0 0 1082 360" aria-labelledby="pipeline-title" className="h-auto w-full" initial={reduceMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: EASE }}>
      <title id="pipeline-title">Interactive morel pipeline: interactions flow through retrieval and modality completion into ranked recommendations</title>
      <defs>
        <linearGradient id="pd-band" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#43cbb4" stopOpacity="0" /><stop offset="50%" stopColor="#43cbb4" stopOpacity="0.36" /><stop offset="100%" stopColor="#aef0e1" stopOpacity="0" /></linearGradient>
        <pattern id="pd-grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(127,127,160,0.08)" strokeWidth="0.5" /></pattern>
        <marker id="pd-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#43cbb4" strokeWidth="1.2" /></marker>
      </defs>
      <rect width="1082" height="360" rx="20" fill="url(#pd-grid)" />
      <rect x="0" y="22" width="1082" height="2" fill="url(#pd-band)" />
      {STAGES.slice(0, -1).map((_, i) => {
        const start = CARD_X[i] + CARD_W + 10;
        const end = CARD_X[i + 1] - 10;
        return <g key={i} aria-hidden="true"><line x1={start} y1={FLOW_Y} x2={end} y2={FLOW_Y} stroke="#31514f" strokeWidth="2" markerEnd="url(#pd-arrow)" /><motion.circle r="4" fill="#aef0e1" initial={{ opacity: 0 }} animate={reduceMotion ? { opacity: 0 } : { opacity: [0, 1, 1, 0], cx: [start, start + 22, end - 22, end], cy: FLOW_Y }} transition={{ duration: 1.4, delay: i * 0.35, repeat: Infinity, repeatDelay: 2.2, ease: "linear" }} /></g>;
      })}
      {STAGES.map((stage, i) => <g key={stage.label} fontFamily="ui-sans-serif, system-ui"><text x={CARD_X[i] + CARD_W / 2} y="36" textAnchor="middle" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontSize="10" letterSpacing="1.5" fill={active === i ? "#79e3cf" : "#8a8a98"}>{String(i + 1).padStart(2, "0")} · {stage.label}</text><StageCard index={i} active={active === i} onActivate={() => setActive(i)} /></g>)}
      <text x="541" y="337" textAnchor="middle" fontSize="10" fill="#8a8a98" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">hover or focus a stage · the data path runs left → right</text>
    </motion.svg>
  );
}

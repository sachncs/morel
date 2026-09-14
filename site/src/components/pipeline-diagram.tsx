import { motion } from "framer-motion";

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
});

export function PipelineDiagram() {
  return (
    <motion.svg
      viewBox="0 0 720 360"
      role="img"
      aria-label="morel pipeline: user-item graph, retrieval, completion, ranking"
      className="h-auto w-full"
      {...fade(0.1)}
    >
      <defs>
        <linearGradient id="pd-edge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7a7eff" />
          <stop offset="100%" stopColor="#c4a8ff" />
        </linearGradient>
        <linearGradient id="pd-band" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.0" />
          <stop offset="50%" stopColor="#7a7eff" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#c4a8ff" stopOpacity="0.0" />
        </linearGradient>
        <radialGradient id="pd-halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#7a7eff" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#7a7eff" stopOpacity="0" />
        </radialGradient>
        <pattern id="pd-grid" width="32" height="32" patternUnits="userSpaceOnUse">
          <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(127,127,160,0.08)" strokeWidth="0.5" />
        </pattern>
      </defs>

      <rect width="720" height="360" fill="url(#pd-grid)" rx="16" />

      {/* Stage labels */}
      <g fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontSize="9" letterSpacing="0.5">
        <text x="40" y="28" fill="#8a8a98" textAnchor="middle">INTERACTIONS</text>
        <text x="220" y="28" fill="#8a8a98" textAnchor="middle">RETRIEVAL</text>
        <text x="430" y="28" fill="#8a8a98" textAnchor="middle">COMPLETION</text>
        <text x="640" y="28" fill="#8a8a98" textAnchor="middle">RANKING</text>
      </g>

      {/* Energy band across the top */}
      <rect x="0" y="14" width="720" height="2" fill="url(#pd-band)" opacity="0.7" />

      {/* === Stage 1: User-item graph === */}
      <g transform="translate(40, 60)">
        {/* Users on left */}
        <g fill="#7a7eff">
          <circle cx="0" cy="20" r="3.4" />
          <circle cx="0" cy="60" r="3.4" />
          <circle cx="0" cy="100" r="3.4" />
          <circle cx="0" cy="140" r="3.4" />
          <circle cx="0" cy="180" r="3.4" />
        </g>
        {/* Items on right */}
        <g fill="#c4a8ff">
          <circle cx="80" cy="30" r="3.4" />
          <circle cx="80" cy="70" r="3.4" />
          <circle cx="80" cy="110" r="3.4" opacity="0.45" />
          <circle cx="80" cy="150" r="3.4" />
          <circle cx="80" cy="190" r="3.4" opacity="0.45" />
        </g>
        {/* Edges */}
        <g stroke="url(#pd-edge)" strokeWidth="0.8" opacity="0.7">
          <line x1="0" y1="20" x2="80" y2="30" />
          <line x1="0" y1="20" x2="80" y2="70" />
          <line x1="0" y1="60" x2="80" y2="30" />
          <line x1="0" y1="60" x2="80" y2="70" />
          <line x1="0" y1="100" x2="80" y2="70" />
          <line x1="0" y1="100" x2="80" y2="110" />
          <line x1="0" y1="100" x2="80" y2="150" />
          <line x1="0" y1="140" x2="80" y2="150" />
          <line x1="0" y1="180" x2="80" y2="150" />
          <line x1="0" y1="180" x2="80" y2="190" />
        </g>
        {/* Arrow */}
        <g stroke="rgba(127,127,160,0.6)" strokeWidth="1.2" fill="none">
          <line x1="92" y1="105" x2="142" y2="105" />
          <path d="M 138 102 L 142 105 L 138 108" />
        </g>
      </g>

      {/* === Stage 2: Retrieval === */}
      <g transform="translate(190, 80)">
        {/* Anchor ring */}
        <circle cx="60" cy="100" r="60" fill="none" stroke="url(#pd-edge)" strokeWidth="1" strokeDasharray="2 4" opacity="0.55" />
        {/* Query node */}
        <circle cx="60" cy="100" r="32" fill="url(#pd-halo)" />
        <circle cx="60" cy="100" r="10" fill="#fff" stroke="url(#pd-edge)" strokeWidth="1.6" />
        <text x="60" y="103" textAnchor="middle" fontSize="9" fontWeight="600" fill="#5d57ff" fontFamily="ui-sans-serif, system-ui">q</text>
        {/* Retrieved nodes */}
        <g fill="#c4a8ff" stroke="#fff" strokeWidth="0.5">
          <circle cx="60" cy="30" r="4" />
          <circle cx="115" cy="100" r="4" />
          <circle cx="60" cy="170" r="4" />
          <circle cx="20" cy="80" r="3.4" />
          <circle cx="20" cy="120" r="3.4" />
          <circle cx="100" cy="80" r="3.4" />
          <circle cx="100" cy="120" r="3.4" />
        </g>
        <g stroke="url(#pd-edge)" strokeWidth="0.9" opacity="0.8">
          <line x1="60" y1="100" x2="60" y2="30" />
          <line x1="60" y1="100" x2="115" y2="100" />
          <line x1="60" y1="100" x2="60" y2="170" />
          <line x1="60" y1="100" x2="20" y2="80" />
          <line x1="60" y1="100" x2="20" y2="120" />
          <line x1="60" y1="100" x2="100" y2="80" />
          <line x1="60" y1="100" x2="100" y2="120" />
        </g>
        {/* Arrow */}
        <g stroke="rgba(127,127,160,0.6)" strokeWidth="1.2" fill="none">
          <line x1="138" y1="100" x2="188" y2="100" />
          <path d="M 184 97 L 188 100 L 184 103" />
        </g>
      </g>

      {/* === Stage 3: Completion (codebook) === */}
      <g transform="translate(400, 80)">
        {/* Codebook grid */}
        <g>
          {Array.from({ length: 8 }).map((_, row) =>
            Array.from({ length: 10 }).map((_, col) => (
              <rect
                key={`${row}-${col}`}
                x={col * 11 + 8}
                y={row * 18 + 12}
                width="8"
                height="14"
                rx="2"
                fill="url(#pd-edge)"
                opacity={(row + col) % 5 === 0 ? 0.85 : 0.18}
              />
            )),
          )}
        </g>
        {/* Pipeline flow into codebook */}
        <g stroke="rgba(127,127,160,0.6)" strokeWidth="1.2" fill="none">
          <line x1="-12" y1="80" x2="6" y2="80" />
          <path d="M 2 77 L 6 80 L 2 83" />
        </g>
        {/* Output to ranking */}
        <g stroke="rgba(127,127,160,0.6)" strokeWidth="1.2" fill="none">
          <line x1="120" y1="80" x2="170" y2="80" />
          <path d="M 166 77 L 170 80 L 166 83" />
        </g>
      </g>

      {/* === Stage 4: Ranking === */}
      <g transform="translate(580, 80)">
        <g stroke="url(#pd-edge)" strokeWidth="1" fill="none">
          <line x1="0" y1="20" x2="100" y2="20" opacity="0.85" />
          <line x1="0" y1="40" x2="100" y2="40" opacity="0.6" />
          <line x1="0" y1="60" x2="100" y2="60" opacity="0.5" />
          <line x1="0" y1="80" x2="100" y2="80" opacity="0.45" />
          <line x1="0" y1="100" x2="100" y2="100" opacity="0.4" />
          <line x1="0" y1="120" x2="100" y2="120" opacity="0.35" />
          <line x1="0" y1="140" x2="100" y2="140" opacity="0.25" />
        </g>
        {/* Score bars on the right */}
        <g>
          {[18, 36, 30, 42, 26, 36, 22, 30, 18, 24].map((h, i) => (
            <rect
              key={i}
              x={104 + i * 4}
              y={70 - h / 2}
              width="2.4"
              height={h}
              fill="url(#pd-edge)"
              opacity={0.4 + i * 0.05}
              rx="1"
            />
          ))}
        </g>
        {/* Top item callout */}
        <g transform="translate(0, -8)">
          <rect x="0" y="-4" width="100" height="14" rx="3" fill="url(#pd-edge)" opacity="0.18" />
          <circle cx="6" cy="3" r="2" fill="#7a7eff" />
          <text x="13" y="6" fontSize="7" fontFamily="ui-sans-serif, system-ui" fill="#5d57ff">
            top-1
          </text>
        </g>
      </g>

      {/* Bottom annotation */}
      <g fontFamily="ui-sans-serif, system-ui, sans-serif" fontSize="10" fill="#8a8a98">
        <text x="360" y="335" textAnchor="middle" letterSpacing="0.3">
          user–item interactions → graph retrieval → modality completion → LightGCN ranking
        </text>
      </g>
    </motion.svg>
  );
}

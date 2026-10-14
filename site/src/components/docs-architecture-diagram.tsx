import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

const stages = [
  { name: "Data", code: "morel.data", description: "Build the sparse graph and mark missing modalities." },
  { name: "Context", code: "retrieve · encode", description: "Find useful neighbours and read their graph context." },
  { name: "Complete", code: "route · codebook", description: "Turn context into the missing feature vectors." },
  { name: "Rank", code: "recommend", description: "Score user–item pairs and return top-K results." },
] as const;

export function DocsArchitectureDiagram() {
  const reduceMotion = useReducedMotion();
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (reduceMotion) return;
    const timer = window.setInterval(() => setActive((current) => (current + 1) % stages.length), 3000);
    return () => window.clearInterval(timer);
  }, [reduceMotion]);

  return (
    <section className="docs-architecture-diagram" aria-label="Interactive morel architecture map">
      <div className="docs-architecture-flow" role="list">
        {stages.map((stage, index) => (
          <div className="docs-architecture-step" role="listitem" key={stage.name}>
            <motion.button
              type="button"
              className={`docs-architecture-card${active === index ? " is-active" : ""}`}
              aria-pressed={active === index}
              onClick={() => setActive(index)}
              onFocus={() => setActive(index)}
              whileHover={reduceMotion ? undefined : { y: -3 }}
            >
              <span className="docs-architecture-number">0{index + 1}</span>
              <strong>{stage.name}</strong>
              <code>{stage.code}</code>
            </motion.button>
            {index < stages.length - 1 && <span className="docs-architecture-arrow" aria-hidden="true">→</span>}
          </div>
        ))}
      </div>
      <motion.p key={active} className="docs-architecture-caption" initial={reduceMotion ? false : { opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}>
        <span>{stages[active].name}</span> — {stages[active].description}
      </motion.p>
    </section>
  );
}

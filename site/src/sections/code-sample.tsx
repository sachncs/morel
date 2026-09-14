import { motion } from "framer-motion";
import { Check, Copy, Terminal } from "lucide-react";
import { useState } from "react";
import { LinkButton } from "../components/button";
import { Section } from "../components/section";
import { CODE_SAMPLE, SITE } from "../lib/content";
import { cn } from "../lib/utils";

const ease = [0.16, 1, 0.3, 1] as [number, number, number, number];

const FILES = [
  { name: "pipeline.py", lang: "python", primary: true },
  { name: "serve.py", lang: "python", primary: false },
];

const SERVE_SNIPPET = `from fastapi import FastAPI
from morel import Config, Pipeline
from morel.serve import ModelLoader

app = FastAPI(title="morel")
loader = ModelLoader(Config.defaults(), "checkpoints/morel.pt")

@app.get("/recommend")
def recommend(user: int, k: int = 10):
    return loader.recommend(user, k=k)`;

function highlight(code: string): { token: string; cls?: string }[] {
  // Naive but high-fidelity Python tokenizer tuned for this snippet.
  const lines = code.split("\n");
  return lines.flatMap((line) => {
    const out: { token: string; cls?: string }[] = [];
    let i = 0;
    while (i < line.length) {
      const ch = line[i];
      // Comments
      if (ch === "#") {
        out.push({ token: line.slice(i), cls: "text-ink-400 dark:text-ink-500 italic" });
        i = line.length;
        continue;
      }
      // Strings
      if (ch === '"' || ch === "'") {
        const quote = ch;
        let j = i + 1;
        while (j < line.length && line[j] !== quote) j++;
        out.push({ token: line.slice(i, j + 1), cls: "text-emerald-600 dark:text-emerald-300" });
        i = j + 1;
        continue;
      }
      // Numbers
      if (/\d/.test(ch)) {
        let j = i;
        while (j < line.length && /[\d.]/.test(line[j])) j++;
        out.push({ token: line.slice(i, j), cls: "text-amber-600 dark:text-amber-300" });
        i = j;
        continue;
      }
      // Identifiers / keywords
      if (/[A-Za-z_]/.test(ch)) {
        let j = i;
        while (j < line.length && /[A-Za-z0-9_]/.test(line[j])) j++;
        const word = line.slice(i, j);
        if (
          /^(from|import|as|def|class|return|if|for|in|with|True|False|None|and|or|not|lambda)$/.test(
            word,
          )
        ) {
          out.push({ token: word, cls: "text-violet-600 dark:text-violet-300" });
        } else if (/^(torch|morel|numpy)$/.test(word) || /^[A-Z][A-Za-z0-9_]*$/.test(word)) {
          out.push({ token: word, cls: "text-sky-600 dark:text-sky-300" });
        } else {
          out.push({ token: word });
        }
        i = j;
        continue;
      }
      out.push({ token: ch });
      i++;
    }
    out.push({ token: "\n" });
    return out;
  });
}

function CodeBlock({ code, filename }: { code: string; filename: string }) {
  const [copied, setCopied] = useState(false);
  const tokens = highlight(code);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="ring-edge overflow-hidden rounded-2xl bg-ink-950 text-ink-100 shadow-card dark:bg-ink-900/80 dark:ring-white/10">
      <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.02] px-4 py-2.5">
        <div className="flex items-center gap-2 text-xs text-ink-400">
          <Terminal className="h-3.5 w-3.5" />
          <span className="font-mono">{filename}</span>
        </div>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy code"
          className={cn(
            "inline-flex h-7 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-medium transition",
            "text-ink-300 hover:bg-white/5 hover:text-white",
          )}
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-emerald-400" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-5 text-[13px] leading-[1.7]">
        <code className="font-mono">
          {tokens.map((t, i) => (
            <span key={i} className={t.cls}>
              {t.token === "\n" ? "\n" : t.token}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}

export function CodeSample() {
  const [active, setActive] = useState<string>(FILES[0].name);
  const file = FILES.find((f) => f.name === active) ?? FILES[0];

  return (
    <Section
      eyebrow="From zero to ranked"
      title={
        <>
          Five lines to a{" "}
          <span className="gradient-text">trained recommender.</span>
        </>
      }
      description="The public API is small by design. Build the graph, attach the corpus, run the pipeline, rank — same surface, same types, same code from notebook to production."
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.8, ease }}
        className="grid gap-8 lg:grid-cols-[1fr_1.2fr] lg:items-start"
      >
        {/* Side panel */}
        <div className="flex flex-col gap-6">
          <ul className="space-y-4">
            {[
              {
                n: "01",
                title: "Build the graph",
                d: "Stream interactions into a CSR matrix. Compute item co-occurrence on demand.",
              },
              {
                n: "02",
                title: "Mask the modalities",
                d: "Bernoulli, structured, or custom masking — pluggable in one call.",
              },
              {
                n: "03",
                title: "Run the pipeline",
                d: "One Pipeline call returns completed embeddings and routing weights.",
              },
              {
                n: "04",
                title: "Rank with LightGCN",
                d: "BPR-trained ranker returns top-K. Same head serves in dev and in prod.",
              },
            ].map((row) => (
              <li key={row.n} className="flex gap-4">
                <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-ink-100 font-mono text-xs text-ink-700 ring-1 ring-ink-200/60 dark:bg-white/5 dark:text-ink-300 dark:ring-white/10">
                  {row.n}
                </span>
                <div>
                  <p className="text-sm font-semibold tracking-tight text-ink-900 dark:text-white">
                    {row.title}
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-600 dark:text-ink-300">
                    {row.d}
                  </p>
                </div>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap gap-3 pt-2">
            <LinkButton
              href={`${SITE.repo}#your-first-run-the-command-line`}
              variant="primary"
              size="md"
            >
              Run the demo
            </LinkButton>
            <LinkButton
              href={SITE.url + "docs/"}
              variant="secondary"
              size="md"
            >
              API reference
            </LinkButton>
          </div>
        </div>

        {/* Code panel */}
        <div className="space-y-3">
          <div className="flex items-center gap-1.5 rounded-full bg-ink-100 p-1 ring-1 ring-ink-200/60 dark:bg-white/5 dark:ring-white/10">
            {FILES.map((f) => (
              <button
                key={f.name}
                type="button"
                onClick={() => setActive(f.name)}
                className={cn(
                  "flex-1 rounded-full px-3 py-1.5 text-xs font-medium transition",
                  active === f.name
                    ? "bg-white text-ink-900 shadow-sm dark:bg-ink-800 dark:text-white"
                    : "text-ink-600 hover:text-ink-900 dark:text-ink-400 dark:hover:text-white",
                )}
              >
                {f.name}
              </button>
            ))}
          </div>
          <CodeBlock
            code={file.name === "serve.py" ? SERVE_SNIPPET : CODE_SAMPLE}
            filename={file.name}
          />
          <p className="px-1 text-xs text-ink-500 dark:text-ink-400">
            Same code runs in a notebook, in a script, and inside the FastAPI server.
          </p>
        </div>
      </motion.div>
    </Section>
  );
}

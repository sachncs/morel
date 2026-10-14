import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";
import { marked } from "marked";

const docsRoot = resolve(process.cwd(), "../docs");

export type DocPage = { slug: string; title: string; section: string; html: string };

async function markdownFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return markdownFiles(path);
    return extname(entry.name) === ".md" ? [path] : [];
  }));
  return files.flat();
}

function pageSlug(path: string): string {
  const name = relative(docsRoot, path).replace(/\\/g, "/").replace(/\.md$/, "");
  return name === "index" ? "" : name.endsWith("/index") ? name.slice(0, -6) : name;
}

function titleFrom(markdown: string, fallback: string): string {
  const heading = markdown.match(/^#\s+(.+)$/m)?.[1]?.trim();
  return heading ?? fallback.replace(/-/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function cleanMarkdown(markdown: string): string {
  return markdown.replace(/^---[\s\S]*?---\s*/m, "");
}

function rewriteLinks(html: string): string {
  return html.replace(/href="((?:\.\.\/)*[^\"]+?)\.md(#[^\"]*)?"/g, (_match, target: string, hash = "") => {
    const cleanTarget = target.replace(/(^|\/)index$/, "").replace(/^\.\.\//, "");
    return `href="/morel/docs/${cleanTarget ? `${cleanTarget}/` : ""}${hash}"`;
  });
}

export async function getDocs(): Promise<DocPage[]> {
  const paths = await markdownFiles(docsRoot);
  const pages = await Promise.all(paths.map(async (path) => {
    const source = await readFile(path, "utf8");
    const slug = pageSlug(path);
    const parts = slug.split("/");
    return {
      slug,
      title: titleFrom(source, parts.at(-1) || "Documentation"),
      section: parts[0] || "home",
      html: rewriteLinks(await marked.parse(cleanMarkdown(source))),
    } satisfies DocPage;
  }));
  return pages.sort((a, b) => a.slug.localeCompare(b.slug));
}

import { createReadStream } from "node:fs";
import { access, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";

const root = resolve("dist");
const prefix = "/morel";
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function safePath(pathname) {
  const relative = pathname.slice(prefix.length).replace(/^\/+/, "") || "index.html";
  const candidate = resolve(root, normalize(relative));
  return candidate.startsWith(`${root}/`) ? candidate : null;
}

const server = createServer(async (request, response) => {
  const pathname = new URL(request.url ?? "/", "http://127.0.0.1").pathname;
  if (!pathname.startsWith(prefix)) {
    response.writeHead(404);
    response.end("Not found");
    return;
  }

  let file = safePath(pathname);
  if (!file) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }
  try {
    await access(file);
    if ((await stat(file)).isDirectory()) file = join(file, "index.html");
  } catch {
    file = join(root, "index.html");
  }

  response.writeHead(200, {
    "Content-Type": contentTypes[extname(file)] ?? "application/octet-stream",
  });
  createReadStream(file).pipe(response);
});

server.listen(4173, "127.0.0.1", () => {
  console.log("Pages preview listening on http://127.0.0.1:4173/morel/");
});

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${path}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("renderiza a página inicial em pt-BR", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /Raízes Abrantes/);
  assert.match(html, /Uma família/);
  assert.match(html, /Top 10 conexões históricas/);
  assert.match(html, /Guilherme, o Conquistador/);
  assert.doesNotMatch(html, /Quem foi a mãe de Joana/);
  assert.match(html, /Explorar a árvore/);
});

test("mantém dados privados fora do grafo compartilhável", async () => {
  const graph = JSON.parse(
    await readFile(new URL("../public/data/tree-graph.json", import.meta.url), "utf8"),
  );
  const root = graph.nodes.find((node) => node.generation === 0);

  assert.ok(root);
  assert.equal(root.private, true);
  assert.equal(root.name, "Pessoa privada");
  assert.match(root.id, /^private-\d+$/);
  assert.ok(graph.nodes.length > 15_000);
  assert.ok(graph.edges.length > 19_000);
});

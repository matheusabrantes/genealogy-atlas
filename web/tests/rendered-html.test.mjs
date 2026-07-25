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
  assert.match(html, /country-flag/);
  for (const flag of [
    "france",
    "portugal",
    "spain",
    "england",
    "netherlands",
    "scotland",
    "germany",
    "italy",
  ]) {
    assert.match(html, new RegExp(`/flags/${flag}\\.svg`));
  }
  assert.match(html, /Ver todos os países e filtrar por geração/);
  assert.match(html, /href="\/lugares"/);
  assert.match(html, /Explorar a árvore/);
});

test("oferece exploração completa de lugares por geração", async () => {
  const response = await render("/lugares");
  assert.equal(response.status, 200);

  const html = await response.text();
  assert.match(html, /Lugares da árvore/);
  assert.match(html, /Pesquisar país ou território/);
  assert.match(html, />Geral</);
  assert.match(html, />G4</);
  assert.match(html, /França/);
  assert.match(html, /Sacro Império Romano-Germânico/);
});

test("publica somente o nome autorizado da pessoa raiz", async () => {
  const graph = JSON.parse(
    await readFile(new URL("../public/data/tree-graph.json", import.meta.url), "utf8"),
  );
  const root = graph.nodes.find((node) => node.generation === 0);

  assert.ok(root);
  assert.equal(root.private, true);
  assert.equal(root.name, "Matheus Abrantes");
  assert.match(root.id, /^private-\d+$/);
  assert.ok(
    graph.nodes
      .filter((node) => node.private && node.generation !== 0)
      .every((node) => node.name === "Pessoa privada"),
  );
  assert.ok(graph.nodes.length > 15_000);
  assert.ok(graph.edges.length > 19_000);
});

test("inclui todos os países conhecidos no explorador compacto", async () => {
  const places = JSON.parse(
    await readFile(new URL("../public/data/tree-places.json", import.meta.url), "utf8"),
  );

  assert.equal(places.countries.length, 22);
  assert.deepEqual(places.generationOptions, [4, 8, 12, 16, 24, 32]);
  assert.ok(
    places.countries.every((country) =>
      country.views.every((view) => view.representatives.length <= 5),
    ),
  );
});

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
  assert.match(html, /Pessoas distintas com pelo menos um evento registrado no país/);
  assert.match(html, /3\.778/);
  assert.doesNotMatch(html, /7\.666/);
  assert.match(html, /Papéis que atravessam a árvore/);
  assert.match(html, /A família dentro da História/);
  assert.match(html, /Familiares e agentes do Santo Ofício/);
  assert.match(html, /Ordem dos Templários/);
  assert.match(html, /Realeza e nobreza/);
  assert.match(html, /3\.007/);
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
  assert.match(html, /Explorar países, papéis e ocupações/);
  assert.match(html, /href="\/lugares"/);
  assert.match(html, /Explorar a árvore/);
});

test("oferece dashboard de países, história e papéis por geração", async () => {
  const response = await render("/lugares");
  assert.equal(response.status, 200);

  const html = await response.text();
  assert.match(html, /Explorar a árvore/);
  assert.match(html, /Pesquisar país, ordem, guerra, ocupação ou pessoa/);
  assert.match(html, />Geral</);
  assert.match(html, />G4</);
  assert.match(html, /França/);
  assert.match(html, /Sacro Império Romano-Germânico/);
  assert.match(html, /Papéis e ocupações/);
  assert.match(html, /Ordens e acontecimentos históricos/);
  assert.match(html, /Inquisição e Santo Ofício/);
  assert.match(html, /Batalha de Aljubarrota/);
  assert.match(html, /Ocupações e títulos específicos/);
  assert.match(html, /Realeza e nobreza/);
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
  assert.equal(places.roleCategories.length, 9);
  assert.ok(places.roleTerms.length > 20);
  assert.equal(places.roleStats.peopleWithRecordedRoles, 4605);
  assert.equal(places.roleStats.peopleClassified, 3423);
  assert.equal(places.historyStats.contexts, 13);
  assert.equal(places.historicalContexts.length, 13);
  assert.equal(
    places.historicalContexts.find((entry) => entry.slug === "inquisition-agents").people,
    9,
  );
  assert.equal(
    places.historicalContexts.find((entry) => entry.slug === "templars").people,
    68,
  );
  assert.ok(
    [
      ...places.roleCategories,
      ...places.roleTerms,
      ...places.historicalContexts,
    ].every((entry) =>
      entry.views.every((view) => view.representatives.length <= 5),
    ),
  );
});

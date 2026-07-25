"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Search, ZoomIn, ZoomOut, Maximize2, LoaderCircle } from "lucide-react";
import "./tree.css";

type TreeNode = {
  id: string;
  name: string;
  generation: number;
  birthYear: number | null;
  deathYear: number | null;
  countries: string[];
  sourceCount: number;
  private: boolean;
};

type TreeData = {
  nodes: TreeNode[];
  edges: { source: string; target: string }[];
};

const generationOptions = [4, 8, 12, 16, 24, 32];

function hash(value: string) {
  let result = 0;
  for (let index = 0; index < value.length; index += 1) {
    result = (result * 31 + value.charCodeAt(index)) | 0;
  }
  return Math.abs(result);
}

function colorForGeneration(generation: number) {
  if (generation <= 3) return "oklch(0.58 0.18 12)";
  if (generation <= 8) return "oklch(0.57 0.12 174)";
  if (generation <= 16) return "oklch(0.58 0.13 246)";
  if (generation <= 24) return "oklch(0.70 0.13 72)";
  return "oklch(0.65 0.06 310)";
}

export default function TreeExplorer() {
  const container = useRef<HTMLDivElement>(null);
  const sigma = useRef<import("sigma").default | null>(null);
  const [data, setData] = useState<TreeData | null>(null);
  const [maxGeneration, setMaxGeneration] = useState(12);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<TreeNode | null>(null);
  const [loading, setLoading] = useState(true);

  const nodeById = useMemo(
    () => new Map(data?.nodes.map((node) => [node.id, node]) ?? []),
    [data],
  );

  useEffect(() => {
    fetch("/data/tree-graph.json")
      .then((response) => response.json())
      .then((tree: TreeData) => setData(tree))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!data || !container.current) return;
    let cancelled = false;

    void Promise.all([import("graphology"), import("sigma")]).then(
      ([graphologyModule, sigmaModule]) => {
        if (cancelled || !container.current) return;
        const Graph = graphologyModule.default;
        const Sigma = sigmaModule.default;
        const graph = new Graph();
        const visible = data.nodes.filter((node) => node.generation <= maxGeneration);
        const visibleIds = new Set(visible.map((node) => node.id));

        visible.forEach((node) => {
          const spread = Math.max(1, Math.pow(node.generation + 1, 1.45));
          const jitter = ((hash(node.id) % 10000) / 10000 - 0.5) * spread;
          graph.addNode(node.id, {
            x: node.generation * 2.4,
            y: jitter,
            size: node.generation === 0 ? 11 : Math.max(2.2, 6.4 - node.generation * 0.15),
            label: node.name,
            color: colorForGeneration(node.generation),
          });
        });

        data.edges.forEach((edge, index) => {
          if (visibleIds.has(edge.source) && visibleIds.has(edge.target)) {
            graph.addEdgeWithKey(`e-${index}`, edge.source, edge.target, {
              color: "oklch(0.78 0.025 174)",
              size: 0.55,
            });
          }
        });

        sigma.current?.kill();
        sigma.current = new Sigma(graph, container.current, {
          allowInvalidContainer: true,
          defaultEdgeType: "line",
          labelColor: { color: "oklch(0.22 0.035 174)" },
          labelFont: "Manrope",
          labelRenderedSizeThreshold: 7,
          renderEdgeLabels: false,
          zIndex: true,
        });

        sigma.current.on("clickNode", ({ node }) => {
          setSelected(nodeById.get(node) ?? null);
        });
      });

    return () => {
      cancelled = true;
      sigma.current?.kill();
      sigma.current = null;
    };
  }, [data, maxGeneration, nodeById]);

  useEffect(() => {
    if (!sigma.current || !data) return;
    const normalized = query.trim().toLocaleLowerCase("pt-BR");
    sigma.current.setSetting("nodeReducer", (node, attributes) => {
      if (!normalized) return attributes;
      const person = nodeById.get(node);
      const match = person?.name.toLocaleLowerCase("pt-BR").includes(normalized);
      return {
        ...attributes,
        color: match ? "oklch(0.58 0.18 12)" : "oklch(0.84 0.01 174)",
        size: match ? Math.max(attributes.size as number, 9) : 1.5,
        zIndex: match ? 2 : 0,
        label: match ? attributes.label : "",
      };
    });
    sigma.current.refresh();
  }, [query, data, nodeById]);

  const zoom = (direction: "in" | "out") => {
    const camera = sigma.current?.getCamera();
    if (!camera) return;
    const ratio = camera.getState().ratio;
    camera.animate(
      { ratio: direction === "in" ? ratio / 1.5 : ratio * 1.5 },
      { duration: 180 },
    );
  };

  return (
    <section className="tree-workspace" aria-label="Explorador da árvore familiar">
      <div className="tree-toolbar">
        <label className="search-field">
          <Search size={17} aria-hidden="true" />
          <span className="sr-only">Pesquisar pessoa</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Pesquisar um nome"
          />
        </label>
        <div className="generation-filter" aria-label="Limite de gerações">
          {generationOptions.map((generation) => (
            <button
              className={maxGeneration === generation ? "active" : ""}
              key={generation}
              onClick={() => setMaxGeneration(generation)}
              type="button"
            >
              G{generation}
            </button>
          ))}
        </div>
        <div className="zoom-controls" aria-label="Controles de zoom">
          <button type="button" onClick={() => zoom("out")} aria-label="Afastar">
            <ZoomOut size={18} />
          </button>
          <button type="button" onClick={() => zoom("in")} aria-label="Aproximar">
            <ZoomIn size={18} />
          </button>
          <button
            type="button"
            onClick={() => sigma.current?.getCamera().animatedReset({ duration: 250 })}
            aria-label="Enquadrar árvore"
          >
            <Maximize2 size={18} />
          </button>
        </div>
      </div>

      <div className="tree-canvas-wrap">
        {loading && (
          <div className="tree-loading">
            <LoaderCircle size={22} aria-hidden="true" />
            Preparando o mapa familiar…
          </div>
        )}
        <div className="tree-canvas" ref={container} />
        <div className="tree-legend" aria-label="Legenda de gerações">
          <span><i className="legend-recent" /> G0–G3</span>
          <span><i className="legend-modern" /> G4–G8</span>
          <span><i className="legend-early" /> G9–G16</span>
          <span><i className="legend-medieval" /> G17+</span>
        </div>
      </div>

      <aside className={`person-panel ${selected ? "open" : ""}`} aria-live="polite">
        {selected ? (
          <>
            <button className="panel-close" type="button" onClick={() => setSelected(null)}>
              Fechar
            </button>
            <span className="panel-generation">G{selected.generation}</span>
            <h2>{selected.name}</h2>
            <p className="panel-dates">
              {selected.birthYear ?? "?"} — {selected.deathYear ?? "?"}
            </p>
            <dl>
              <div><dt>Fontes</dt><dd>{selected.sourceCount}</dd></div>
              <div><dt>Lugares</dt><dd>{selected.countries.join(", ") || "Não informado"}</dd></div>
              <div><dt>FamilySearch</dt><dd>{selected.id}</dd></div>
            </dl>
            {!selected.private && (
              <a
                href={`https://www.familysearch.org/pt/tree/person/details/${selected.id}`}
                target="_blank"
                rel="noreferrer"
              >
                Abrir perfil no FamilySearch
              </a>
            )}
          </>
        ) : (
          <>
            <span className="panel-generation">Como usar</span>
            <h2>Selecione uma pessoa</h2>
            <p>
              Arraste para mover o mapa, use a roda para aproximar e clique em
              qualquer nó para ver seus detalhes.
            </p>
          </>
        )}
      </aside>
    </section>
  );
}

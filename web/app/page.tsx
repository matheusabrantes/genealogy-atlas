import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  Globe2,
  Network,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import summary from "../public/data/tree-summary.json";

export const metadata: Metadata = {
  title: "Raízes Abrantes — nossa história em rede",
  description:
    "Uma leitura visual da família Abrantes: gerações, lugares, pessoas e conexões históricas.",
};

const number = new Intl.NumberFormat("pt-BR");

function GenerationRibbon() {
  const visible = summary.generationCounts.filter(
    ({ generation }) => generation <= 22 && generation % 2 === 0,
  );
  const max = Math.max(...visible.map(({ people }) => people));
  return (
    <div className="generation-ribbon" aria-label="Crescimento da árvore por geração">
      {visible.map(({ generation, people }) => (
        <div className="generation-step" key={generation}>
          <div
            className="generation-bar"
            style={{ "--bar-height": `${Math.max(12, (people / max) * 100)}%` } as React.CSSProperties}
          />
          <span>G{generation}</span>
        </div>
      ))}
    </div>
  );
}

export default function Home() {
  const topCountry = summary.countries[0]?.events ?? 1;
  return (
    <main>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="Raízes Abrantes — início">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>Raízes Abrantes</span>
        </Link>
        <nav aria-label="Navegação principal">
          <a href="#panorama">Panorama</a>
          <a href="#pessoas">Pessoas</a>
          <Link className="nav-action" href="/arvore">
            Abrir árvore
          </Link>
        </nav>
      </header>

      <section className="hero" id="panorama">
        <div className="hero-copy">
          <p className="hero-kicker">
            <Network size={17} aria-hidden="true" />
            Retrato da árvore em 25 de julho de 2026
          </p>
          <h1>Uma família.<br />Milhares de caminhos.</h1>
          <p className="hero-intro">
            Da memória de Icó e do sertão paraibano a conexões que atravessam
            séculos e continentes. Este é um mapa vivo — com fatos,
            hipóteses e perguntas claramente separados.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/arvore">
              Explorar a árvore
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <a className="button button-quiet" href="#pessoas">
              Ver conexões históricas
            </a>
          </div>
        </div>

        <div className="hero-data" aria-label="Principais números da árvore">
          <div className="primary-number">
            <strong>{number.format(summary.people)}</strong>
            <span>pessoas reunidas em uma única árvore</span>
          </div>
          <div className="metric-line">
            <div>
              <strong>G{summary.maxGeneration}</strong>
              <span>geração mais distante alcançada</span>
            </div>
            <div>
              <strong>{number.format(summary.sources)}</strong>
              <span>fontes importadas</span>
            </div>
            <div>
              <strong>{number.format(summary.families)}</strong>
              <span>núcleos familiares</span>
            </div>
          </div>
          <GenerationRibbon />
          <p className="data-caption">
            <ShieldCheck size={16} aria-hidden="true" />
            Nomes de pessoas potencialmente vivas estão ocultos.
          </p>
        </div>
      </section>

      <section className="countries-section" aria-labelledby="countries-title">
        <div className="section-heading">
          <div>
            <Globe2 size={24} aria-hidden="true" />
            <h2 id="countries-title">Lugares que aparecem na árvore</h2>
          </div>
          <p>
            Contagem de eventos registrados — nascimento, batismo, casamento,
            morte ou residência. Não representa nacionalidade.
          </p>
        </div>
        <div className="country-chart">
          {summary.countries.slice(0, 8).map(({ country, events }, index) => (
            <div className="country-row" key={country}>
              <span className="country-rank">{String(index + 1).padStart(2, "0")}</span>
              <span className="country-name">{country}</span>
              <div className="country-track" aria-hidden="true">
                <span style={{ width: `${(events / topCountry) * 100}%` }} />
              </div>
              <strong>{number.format(events)}</strong>
            </div>
          ))}
        </div>
        <p className="source-warning">
          Os grandes volumes europeus vêm sobretudo das ramificações medievais
          registradas na árvore colaborativa do FamilySearch.
        </p>
      </section>

      <section className="people-section" id="pessoas" aria-labelledby="people-title">
        <div className="section-heading people-heading">
          <div>
            <Sparkles size={24} aria-hidden="true" />
            <h2 id="people-title">Top 10 conexões históricas</h2>
          </div>
          <p>
            Pessoas reconhecíveis encontradas nas linhas históricas da árvore
            compartilhada pela família.
          </p>
        </div>
        <div className="people-list">
          {summary.featuredPeople.slice(0, 10).map((person) => (
            <article className="person-row" key={person.id}>
              <div
                className="person-generation"
                aria-label={`Posição ${person.rank}`}
              >
                {String(person.rank).padStart(2, "0")}
              </div>
              <div className="person-copy">
                <h3>{person.label}</h3>
                <p>{person.description}</p>
              </div>
              <div className="person-dates">
                <span>{person.birthYear ?? "?"}—{person.deathYear ?? "?"}</span>
                <span>G{person.generation} · {person.sourceCount} fontes</span>
              </div>
              <span className="status status-review">
                <Network size={15} aria-hidden="true" />
                No FamilySearch
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="graph-callout">
        <div className="graph-orbit" aria-hidden="true">
          {Array.from({ length: 14 }).map((_, index) => (
            <span key={index} style={{ "--i": index } as React.CSSProperties} />
          ))}
        </div>
        <div>
          <h2>A árvore completa está pronta para ser explorada.</h2>
          <p>
            Comece com poucas gerações, pesquise um nome e amplie o mapa quando
            quiser enxergar as ramificações históricas.
          </p>
          <Link className="button button-light" href="/arvore">
            Abrir visualização completa
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
      </section>

      <footer>
        <div className="brand footer-brand">
          <span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>
          <span>Raízes Abrantes</span>
        </div>
        <p>
          Construído a partir de uma fotografia privada da árvore colaborativa
          do FamilySearch e apresentado aqui em uma experiência visual própria.
        </p>
      </footer>
    </main>
  );
}

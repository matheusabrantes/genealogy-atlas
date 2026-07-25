"use client";

import { useMemo, useState } from "react";
import {
  ChevronDown,
  ExternalLink,
  Globe2,
  Landmark,
  Search,
  Sparkles,
  Tags,
} from "lucide-react";
import { countryFlags } from "../country-flags";
import { HistoryIcon } from "../history-icons";
import { RoleIcon } from "../role-icons";
import explorer from "../../public/data/tree-places.json";
import "./places.css";

type Representative = {
  id: string;
  name: string;
  generation: number;
  birthYear: number | null;
  deathYear: number | null;
  sourceCount: number;
  description: string | null;
  featured: boolean;
  private: boolean;
  roleTexts?: string[];
  association?: string;
};

type GenerationView = {
  maxGeneration: number;
  people: number;
  representatives: Representative[];
};

type CountryEntry = {
  country: string;
  people: number;
  views: GenerationView[];
};

type RoleCategory = {
  slug: string;
  label: string;
  description: string;
  people: number;
  views: GenerationView[];
};

type RoleTerm = {
  slug: string;
  label: string;
  category: string;
  categoryLabel: string;
  people: number;
  views: GenerationView[];
};

type HistoricalContext = {
  slug: string;
  label: string;
  kind: string;
  period: string;
  description: string;
  people: number;
  views: GenerationView[];
};

const number = new Intl.NumberFormat("pt-BR");

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLocaleLowerCase("pt-BR");
}

function personDates(person: Representative) {
  if (!person.birthYear && !person.deathYear) return "Datas não informadas";
  return `${person.birthYear ?? "?"} — ${person.deathYear ?? "?"}`;
}

function currentView(views: GenerationView[], maxGeneration: number) {
  return (
    views.find((view) => view.maxGeneration === maxGeneration) ?? views.at(-1)!
  );
}

function matchesQuery(
  query: string,
  fields: Array<string | null | undefined>,
  people: Representative[],
) {
  if (!query) return true;
  return [...fields, ...people.flatMap((person) => [
    person.name,
    person.description,
    ...(person.roleTexts ?? []),
  ])].some((field) => field && normalize(field).includes(query));
}

function PeopleGrid({
  people,
  context,
}: {
  people: Representative[];
  context: string;
}) {
  return (
    <div className="place-details">
      <div className="place-details-heading">
        <div>
          <Sparkles size={18} aria-hidden="true" />
          <h3>Pessoas representativas</h3>
        </div>
        <p>
          Até cinco perfis em {context}: conexões históricas descritas aparecem
          primeiro; depois, entram os que têm mais fontes.
        </p>
      </div>
      <div className="place-people">
        {people.map((person) => (
          <article className="place-person" key={person.id}>
            <div className="place-person-topline">
              <span>G{person.generation}</span>
              <span>
                {person.association ??
                  (person.featured ? "Conexão histórica" : "Mais documentada")}
              </span>
            </div>
            <h4>{person.name}</h4>
            {person.description && <p>{person.description}</p>}
            {person.roleTexts?.length ? (
              <p className="person-role-text">{person.roleTexts.join(" · ")}</p>
            ) : null}
            <div className="place-person-meta">
              <span>{personDates(person)}</span>
              <span>{number.format(person.sourceCount)} fontes</span>
            </div>
            {!person.private && (
              <a
                href={`https://www.familysearch.org/pt/tree/person/details/${person.id}`}
                target="_blank"
                rel="noreferrer"
              >
                Ver no FamilySearch
                <ExternalLink size={14} aria-hidden="true" />
              </a>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

export default function PlacesExplorer() {
  const [maxGeneration, setMaxGeneration] = useState(explorer.maxGeneration);
  const [query, setQuery] = useState("");
  const [openItem, setOpenItem] = useState<string | null>(null);
  const normalizedQuery = normalize(query.trim());

  const countries = useMemo(
    () =>
      (explorer.countries as CountryEntry[])
        .map((entry) => ({
          ...entry,
          current: currentView(entry.views, maxGeneration),
        }))
        .filter(
          (entry) =>
            entry.current.people > 0 &&
            matchesQuery(normalizedQuery, [entry.country], entry.current.representatives),
        ),
    [maxGeneration, normalizedQuery],
  );

  const categories = useMemo(
    () =>
      (explorer.roleCategories as RoleCategory[])
        .map((entry) => ({
          ...entry,
          current: currentView(entry.views, maxGeneration),
        }))
        .filter(
          (entry) =>
            entry.current.people > 0 &&
            matchesQuery(
              normalizedQuery,
              [entry.label, entry.description],
              entry.current.representatives,
            ),
        )
        .sort(
          (left, right) =>
            right.current.people - left.current.people ||
            left.label.localeCompare(right.label, "pt-BR"),
        ),
    [maxGeneration, normalizedQuery],
  );

  const terms = useMemo(
    () =>
      (explorer.roleTerms as RoleTerm[])
        .map((entry) => ({
          ...entry,
          current: currentView(entry.views, maxGeneration),
        }))
        .filter(
          (entry) =>
            entry.current.people > 0 &&
            matchesQuery(
              normalizedQuery,
              [entry.label, entry.categoryLabel],
              entry.current.representatives,
            ),
        )
        .sort(
          (left, right) =>
            right.current.people - left.current.people ||
            left.label.localeCompare(right.label, "pt-BR"),
        ),
    [maxGeneration, normalizedQuery],
  );

  const historicalContexts = useMemo(
    () =>
      (explorer.historicalContexts as HistoricalContext[])
        .map((entry) => ({
          ...entry,
          current: currentView(entry.views, maxGeneration),
        }))
        .filter(
          (entry) =>
            entry.current.people > 0 &&
            matchesQuery(
              normalizedQuery,
              [entry.label, entry.kind, entry.period, entry.description],
              entry.current.representatives,
            ),
        )
        .sort(
          (left, right) =>
            right.current.people - left.current.people ||
            left.label.localeCompare(right.label, "pt-BR"),
        ),
    [maxGeneration, normalizedQuery],
  );

  const topCountry = Math.max(...countries.map((entry) => entry.current.people), 1);
  const topCategory = Math.max(...categories.map((entry) => entry.current.people), 1);

  const toggle = (key: string) => setOpenItem(openItem === key ? null : key);

  return (
    <section className="places-explorer" aria-label="Dashboard de exploração da árvore">
      <div className="places-toolbar">
        <label className="places-search">
          <Search size={18} aria-hidden="true" />
          <span className="sr-only">
            Pesquisar país, acontecimento, ordem, ocupação ou pessoa
          </span>
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setOpenItem(null);
            }}
            placeholder="Pesquisar país, ordem, guerra, ocupação ou pessoa"
            type="search"
          />
        </label>

        <div className="places-generation" aria-label="Filtrar por geração máxima">
          {explorer.generationOptions.map((generation) => (
            <button
              className={generation === maxGeneration ? "active" : ""}
              key={generation}
              onClick={() => {
                setMaxGeneration(generation);
                setOpenItem(null);
              }}
              type="button"
            >
              {generation === explorer.maxGeneration ? "Geral" : `G${generation}`}
            </button>
          ))}
        </div>

        <nav className="explore-jumps" aria-label="Seções do dashboard">
          <a href="#paises">Países</a>
          <a href="#historia">História</a>
          <a href="#papeis">Papéis</a>
          <a href="#ocupacoes">Ocupações</a>
        </nav>
      </div>

      <div className="explore-summary" aria-live="polite">
        <div>
          <strong>{number.format(countries.length)}</strong>
          <span>países e territórios</span>
        </div>
        <div>
          <strong>{number.format(historicalContexts.length)}</strong>
          <span>contextos históricos</span>
        </div>
        <div>
          <strong>{number.format(categories.length)}</strong>
          <span>categorias de papéis</span>
        </div>
        <div>
          <strong>{number.format(terms.length)}</strong>
          <span>ocupações e títulos</span>
        </div>
        <p>
          {maxGeneration === explorer.maxGeneration
            ? "Todas as gerações visíveis"
            : `Recorte até G${maxGeneration}`}
        </p>
      </div>

      <section className="dashboard-section" id="paises" aria-labelledby="countries-heading">
        <div className="dashboard-heading">
          <div>
            <Globe2 size={22} aria-hidden="true" />
            <div>
              <p>Geografia</p>
              <h2 id="countries-heading">Países e territórios</h2>
            </div>
          </div>
          <p>
            Pessoas distintas com pelo menos um evento associado ao lugar.
            Não representa nacionalidade.
          </p>
        </div>

        {countries.length ? (
          <div className="places-list">
            {countries.map((entry, index) => {
              const key = `country:${entry.country}`;
              const isOpen = openItem === key;
              const flag = countryFlags[entry.country];
              return (
                <article className={`place-entry ${isOpen ? "open" : ""}`} key={entry.country}>
                  <button
                    aria-expanded={isOpen}
                    aria-label={`${entry.country}, ${number.format(entry.current.people)} pessoas`}
                    className="place-trigger"
                    onClick={() => toggle(key)}
                    type="button"
                  >
                    <span className="place-position">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="place-identity">
                      {flag ? (
                        <span
                          className="country-flag place-flag"
                          aria-hidden="true"
                          style={{ backgroundImage: `url(${flag})` }}
                        />
                      ) : (
                        <span className="place-symbol" aria-hidden="true">
                          <Globe2 size={18} />
                        </span>
                      )}
                      <span>{entry.country}</span>
                    </span>
                    <span className="entry-track" aria-hidden="true">
                      <i style={{ width: `${(entry.current.people / topCountry) * 100}%` }} />
                    </span>
                    <span className="place-count">
                      <strong>{number.format(entry.current.people)}</strong>
                      <span>pessoas</span>
                    </span>
                    <ChevronDown className="place-chevron" size={20} aria-hidden="true" />
                  </button>
                  {isOpen && (
                    <PeopleGrid
                      people={entry.current.representatives}
                      context={entry.country}
                    />
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="places-empty">
            <Globe2 size={24} aria-hidden="true" />
            <h3>Nenhum país encontrado</h3>
            <p>Tente outro termo ou selecione uma geração mais ampla.</p>
          </div>
        )}
      </section>

      <section
        className="dashboard-section history-section"
        id="historia"
        aria-labelledby="history-heading"
      >
        <div className="dashboard-heading">
          <div>
            <Landmark size={22} aria-hidden="true" />
            <div>
              <p>A família dentro da História</p>
              <h2 id="history-heading">Ordens e acontecimentos históricos</h2>
            </div>
          </div>
          <p>
            Ordens militares, conflitos e instituições mencionados em títulos,
            funções, acontecimentos ou notas associados aos perfis.
          </p>
        </div>

        {historicalContexts.length ? (
          <div className="history-grid">
            {historicalContexts.map((entry, index) => {
              const key = `history:${entry.slug}`;
              const isOpen = openItem === key;
              return (
                <article
                  className={`history-card ${isOpen ? "open" : ""}`}
                  key={entry.slug}
                >
                  <button
                    aria-expanded={isOpen}
                    onClick={() => toggle(key)}
                    type="button"
                  >
                    <span className="place-position">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="history-card-icon">
                      <HistoryIcon context={entry.slug} size={21} />
                    </span>
                    <span className="history-card-copy">
                      <span>
                        <small>{entry.kind}</small>
                        <small>{entry.period}</small>
                      </span>
                      <strong>{entry.label}</strong>
                      <span>{entry.description}</span>
                    </span>
                    <span className="history-card-count">
                      <strong>{number.format(entry.current.people)}</strong>
                      <small>perfis associados</small>
                    </span>
                    <ChevronDown
                      className="place-chevron"
                      size={19}
                      aria-hidden="true"
                    />
                  </button>
                  {isOpen && (
                    <PeopleGrid
                      people={entry.current.representatives}
                      context={entry.label}
                    />
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="places-empty">
            <Landmark size={24} aria-hidden="true" />
            <h3>Nenhum contexto histórico encontrado</h3>
            <p>Tente outro termo ou amplie o recorte de gerações.</p>
          </div>
        )}
      </section>

      <section className="dashboard-section" id="papeis" aria-labelledby="roles-heading">
        <div className="dashboard-heading">
          <div>
            <Tags size={22} aria-hidden="true" />
            <div>
              <p>Contexto social</p>
              <h2 id="roles-heading">Papéis e ocupações</h2>
            </div>
          </div>
          <p>
            Categorias normalizadas a partir de ocupações, títulos e funções
            religiosas registradas no GEDCOM.
          </p>
        </div>

        {categories.length ? (
          <div className="role-grid">
            {categories.map((entry) => {
              const key = `category:${entry.slug}`;
              const isOpen = openItem === key;
              return (
                <article className={`role-card ${isOpen ? "open" : ""}`} key={entry.slug}>
                  <button
                    aria-expanded={isOpen}
                    onClick={() => toggle(key)}
                    type="button"
                  >
                    <span className="role-card-icon">
                      <RoleIcon category={entry.slug} size={20} />
                    </span>
                    <span className="role-card-copy">
                      <strong>{entry.label}</strong>
                      <small>{entry.description}</small>
                    </span>
                    <span className="role-card-count">
                      {number.format(entry.current.people)}
                      <small>pessoas</small>
                    </span>
                    <span className="role-card-track" aria-hidden="true">
                      <i style={{ width: `${(entry.current.people / topCategory) * 100}%` }} />
                    </span>
                    <ChevronDown className="place-chevron" size={19} aria-hidden="true" />
                  </button>
                  {isOpen && (
                    <PeopleGrid
                      people={entry.current.representatives}
                      context={entry.label}
                    />
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="places-empty">
            <Tags size={24} aria-hidden="true" />
            <h3>Nenhum papel encontrado</h3>
            <p>Tente pesquisar outro termo ou ampliar a geração.</p>
          </div>
        )}
      </section>

      <section className="dashboard-section" id="ocupacoes" aria-labelledby="terms-heading">
        <div className="dashboard-heading">
          <div>
            <Sparkles size={22} aria-hidden="true" />
            <div>
              <p>Vocabulário normalizado</p>
              <h2 id="terms-heading">Ocupações e títulos específicos</h2>
            </div>
          </div>
          <p>
            Variações em português, francês, inglês, espanhol e neerlandês
            aparecem reunidas sob um mesmo termo.
          </p>
        </div>

        {terms.length ? (
          <div className="terms-list">
            {terms.map((entry, index) => {
              const key = `term:${entry.slug}`;
              const isOpen = openItem === key;
              return (
                <article className={`term-entry ${isOpen ? "open" : ""}`} key={entry.slug}>
                  <button
                    aria-expanded={isOpen}
                    onClick={() => toggle(key)}
                    type="button"
                  >
                    <span className="place-position">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="term-name">
                      <RoleIcon category={entry.category} size={17} />
                      <span>
                        <strong>{entry.label}</strong>
                        <small>{entry.categoryLabel}</small>
                      </span>
                    </span>
                    <span className="place-count">
                      <strong>{number.format(entry.current.people)}</strong>
                      <span>pessoas</span>
                    </span>
                    <ChevronDown className="place-chevron" size={19} aria-hidden="true" />
                  </button>
                  {isOpen && (
                    <PeopleGrid
                      people={entry.current.representatives}
                      context={entry.label}
                    />
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="places-empty">
            <Sparkles size={24} aria-hidden="true" />
            <h3>Nenhuma ocupação encontrada</h3>
            <p>Tente outro nome, título ou geração.</p>
          </div>
        )}
      </section>

      <p className="places-note">
        Uma pessoa pode aparecer em mais de uma categoria quando acumulou
        títulos, funções ou menções históricas. A classificação preserva nos
        detalhes o trecho original associado ao perfil.
      </p>
    </section>
  );
}

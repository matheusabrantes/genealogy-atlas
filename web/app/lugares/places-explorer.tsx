"use client";

import { useMemo, useState } from "react";
import {
  ChevronDown,
  ExternalLink,
  Globe2,
  Search,
  Sparkles,
} from "lucide-react";
import { countryFlags } from "../country-flags";
import places from "../../public/data/tree-places.json";
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
};

type CountryView = {
  maxGeneration: number;
  people: number;
  representatives: Representative[];
};

type CountryEntry = {
  country: string;
  people: number;
  views: CountryView[];
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

export default function PlacesExplorer() {
  const [maxGeneration, setMaxGeneration] = useState(places.maxGeneration);
  const [query, setQuery] = useState("");
  const [openCountry, setOpenCountry] = useState<string | null>(null);

  const visibleCountries = useMemo(() => {
    const normalized = normalize(query.trim());
    return (places.countries as CountryEntry[])
      .map((entry) => ({
        ...entry,
        current:
          entry.views.find((view) => view.maxGeneration === maxGeneration) ??
          entry.views.at(-1)!,
      }))
      .filter(
        (entry) =>
          entry.current.people > 0 &&
          (!normalized || normalize(entry.country).includes(normalized)),
      );
  }, [maxGeneration, query]);

  const visiblePeople = visibleCountries.reduce(
    (total, country) => total + country.current.people,
    0,
  );

  return (
    <section className="places-explorer" aria-label="Explorador de lugares">
      <div className="places-toolbar">
        <label className="places-search">
          <Search size={18} aria-hidden="true" />
          <span className="sr-only">Pesquisar país ou território</span>
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setOpenCountry(null);
            }}
            placeholder="Pesquisar país ou território"
            type="search"
          />
        </label>

        <div className="places-generation" aria-label="Filtrar por geração máxima">
          {places.generationOptions.map((generation) => (
            <button
              className={generation === maxGeneration ? "active" : ""}
              key={generation}
              onClick={() => {
                setMaxGeneration(generation);
                setOpenCountry(null);
              }}
              type="button"
            >
              {generation === places.maxGeneration ? "Geral" : `G${generation}`}
            </button>
          ))}
        </div>
      </div>

      <div className="places-summary" aria-live="polite">
        <p>
          <strong>{number.format(visibleCountries.length)}</strong>{" "}
          {visibleCountries.length === 1 ? "lugar encontrado" : "lugares encontrados"}
        </p>
        <span>
          {number.format(visiblePeople)} ocorrências de pessoas até{" "}
          {maxGeneration === places.maxGeneration ? "a geração mais distante" : `G${maxGeneration}`}
        </span>
      </div>

      {visibleCountries.length ? (
        <div className="places-list">
          {visibleCountries.map((entry, index) => {
            const isOpen = openCountry === entry.country;
            const panelId = `country-${index}`;
            const flag = countryFlags[entry.country];
            return (
              <article className={`place-entry ${isOpen ? "open" : ""}`} key={entry.country}>
                <button
                  aria-label={`${entry.country}, ${number.format(entry.current.people)} pessoas. ${isOpen ? "Ocultar destaques" : "Mostrar destaques"}`}
                  aria-controls={panelId}
                  aria-expanded={isOpen}
                  className="place-trigger"
                  onClick={() => setOpenCountry(isOpen ? null : entry.country)}
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
                  <span className="place-count">
                    <strong>{number.format(entry.current.people)}</strong>
                    <span>pessoas</span>
                  </span>
                  <ChevronDown className="place-chevron" size={20} aria-hidden="true" />
                </button>

                {isOpen && (
                  <div className="place-details" id={panelId}>
                    <div className="place-details-heading">
                      <div>
                        <Sparkles size={18} aria-hidden="true" />
                        <h2>Pessoas representativas</h2>
                      </div>
                      <p>
                        Até cinco perfis: conexões históricas descritas aparecem
                        primeiro; depois, entram os que têm mais fontes no recorte.
                      </p>
                    </div>
                    <div className="place-people">
                      {entry.current.representatives.map((person) => (
                        <article className="place-person" key={person.id}>
                          <div className="place-person-topline">
                            <span>G{person.generation}</span>
                            <span>
                              {person.featured ? "Conexão histórica" : "Mais documentada"}
                            </span>
                          </div>
                          <h3>{person.name}</h3>
                          {person.description && <p>{person.description}</p>}
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
                )}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="places-empty">
          <Globe2 size={24} aria-hidden="true" />
          <h2>Nenhum lugar encontrado</h2>
          <p>Tente outro nome ou selecione uma geração mais ampla.</p>
        </div>
      )}

      <p className="places-note">
        A contagem mostra pessoas com pelo menos um evento associado ao lugar.
        Não representa nacionalidade, residência permanente ou prova de origem.
      </p>
    </section>
  );
}

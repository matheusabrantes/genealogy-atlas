import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, PanelsTopLeft } from "lucide-react";
import PlacesExplorer from "./places-explorer";

export const metadata: Metadata = {
  title: "Explorar a árvore",
  description:
    "Explore países, papéis, ocupações, títulos e pessoas da árvore familiar por geração.",
};

export default function PlacesPage() {
  return (
    <main className="places-page">
      <header className="places-header">
        <Link className="places-back" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          Voltar ao panorama
        </Link>
        <div className="places-title">
          <span className="places-title-icon" aria-hidden="true">
            <PanelsTopLeft size={21} />
          </span>
          <div>
            <p>Dashboard familiar</p>
            <h1>Explorar a árvore</h1>
          </div>
        </div>
        <p className="places-intro">
          Um único filtro para atravessar países, papéis, ocupações, títulos e
          pessoas ao longo das gerações.
        </p>
      </header>
      <PlacesExplorer />
    </main>
  );
}

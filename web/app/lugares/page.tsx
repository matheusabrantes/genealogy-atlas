import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, MapPinned } from "lucide-react";
import PlacesExplorer from "./places-explorer";

export const metadata: Metadata = {
  title: "Lugares da árvore",
  description:
    "Explore todos os países e territórios da árvore familiar por geração e descubra pessoas representativas de cada lugar.",
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
            <MapPinned size={21} />
          </span>
          <div>
            <p>Atlas familiar</p>
            <h1>Lugares da árvore</h1>
          </div>
        </div>
        <p className="places-intro">
          Veja onde aparecem eventos familiares, avance pelas gerações e abra
          cada lugar para conhecer cinco pessoas de destaque.
        </p>
      </header>
      <PlacesExplorer />
    </main>
  );
}

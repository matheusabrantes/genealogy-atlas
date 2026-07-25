import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import TreeExplorer from "./tree-explorer";

export const metadata: Metadata = {
  title: "Árvore completa",
  description: "Explore as gerações e conexões da família em um grafo interativo.",
};

export default function TreePage() {
  return (
    <main className="tree-page">
      <header className="tree-header">
        <Link className="tree-back" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          Voltar ao panorama
        </Link>
        <div>
          <h1>Árvore completa</h1>
          <p>
            Explore primeiro um recorte e amplie conforme necessário.
            Ramificações antigas podem conter vínculos ainda não auditados.
          </p>
        </div>
        <span className="tree-privacy">
          <ShieldCheck size={16} aria-hidden="true" />
          Pessoas vivas protegidas
        </span>
      </header>
      <TreeExplorer />
    </main>
  );
}

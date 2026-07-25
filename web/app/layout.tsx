import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://kinship-atlas.matheus-abrantes.chatgpt.site"),
  title: {
    default: "Raízes Abrantes",
    template: "%s — Raízes Abrantes",
  },
  description:
    "Uma cartografia visual da família Abrantes, com gerações, lugares, fontes e pesquisas em andamento.",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    title: "Raízes Abrantes",
    description:
      "Uma cartografia visual da família Abrantes, com gerações, lugares, fontes e pesquisas em andamento.",
    url: "https://kinship-atlas.matheus-abrantes.chatgpt.site",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={manrope.variable}>{children}</body>
    </html>
  );
}

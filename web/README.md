# Raízes Abrantes — site

Aplicação local em pt-BR para apresentar os grandes números da árvore, destacar
conexões históricas e explorar visualmente o grafo de ancestrais.

## Rodar localmente

Requer Node.js 22.13 ou mais recente.

```bash
npm install
npm run dev
```

Abra `http://localhost:3000`.

## Atualizar os dados

Na raiz do projeto, execute:

```bash
python -m mygenealogy.analytics \
  data/ARQUIVO_ATUALIZADO.ged \
  --root-fsid ABCD-123 \
  --summary web/public/data/tree-summary.json \
  --graph web/public/data/tree-graph.json
```

O site passa a usar a nova fotografia da árvore no próximo carregamento. O
arquivo GEDCOM permanece privado e ignorado pelo Git; somente a versão derivada
e sanitizada do grafo é usada pela interface.

## Verificação

```bash
npm run build
```

Antes de publicar, revise pessoas vivas e hipóteses genealógicas. O projeto não
deve tratar conexões importadas do FamilySearch como prova documental.

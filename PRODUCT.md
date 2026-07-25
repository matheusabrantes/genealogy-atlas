# Product

## Register

product

## Platform

web

## Users

O usuário principal é uma pessoa pesquisando a própria genealogia, inicialmente um pesquisador brasileiro trabalhando com sua árvore colaborativa do FamilySearch. Durante a pesquisa, precisa navegar por muitas gerações, compreender relações familiares, encontrar inconsistências e decidir quais pessoas e documentos investigar em seguida.

## Product Purpose

O mygenealogy transforma uma extração local do FamilySearch em um espaço visual de investigação. O produto permite explorar pessoas e relações como um grafo, executar verificações genealógicas, identificar lacunas documentais e organizar próximos passos de pesquisa sem alterar automaticamente a árvore compartilhada. Nesta primeira fase, funciona apenas localmente no navegador e mantém credenciais e dados familiares privados fora do repositório.

O sucesso significa conseguir partir de uma pessoa, compreender rapidamente seu ramo familiar, perceber problemas que passariam despercebidos em uma árvore convencional e chegar a uma ação de pesquisa concreta e bem fundamentada.

## Positioning

Uma ferramenta visual de investigação que reúne exploração do grafo, validação cronológica e evidência documental em uma única leitura da árvore familiar.

## Brand Personality

Contemporânea, exploratória e dinâmica. A interface deve transmitir a sensação de uma superfície espacial viva, na qual o usuário se orienta, aproxima, expande e investiga relações com fluidez. O Figma é a principal referência de sensação de navegação: tela ampla, zoom e exploração espacial.

## Anti-references

O produto não deve parecer um software genealógico dos anos 2000. Evitar linguagem visual antiga, pergaminhos, árvores ilustradas, molduras clássicas, ornamentação nostálgica e controles com aparência ultrapassada.

## Design Principles

1. O grafo é o espaço principal de trabalho, não uma ilustração auxiliar.
2. A complexidade aparece progressivamente: começar pelo ramo em foco e expandir sob demanda.
3. Toda sinalização de problema deve levar a uma explicação e a uma próxima ação de pesquisa.
4. A interface deve separar fatos, hipóteses e alertas para não transformar suspeitas automáticas em conclusões genealógicas.
5. Privacidade e reversibilidade vêm antes da conveniência: importação local e leitura primeiro, escrita externa somente quando deliberadamente autorizada.

## Generation Model

O grafo usa a pessoa inicial como `G0`. Pais, tios e tias ficam em `G1`; avós e irmãos dos avós em `G2`; bisavós em `G3`; trisavós em `G4`, continuando a numeração para trás. Cônjuges compartilham a camada geracional.

Cada pessoa conectada à linhagem principal deve expor `generation: 0..n` e um rótulo visual `G0..Gn`. Pessoas ainda pertencentes apenas à rede FAN — familiares colaterais candidatos, associados ou vizinhos — não recebem uma geração definitiva até que a relação seja demonstrada.

O rótulo geracional não substitui o nível de evidência. Cada vínculo deve ser exibido separadamente como `documentado`, `provável`, `possível`, `não provado` ou `descartado`.

## Accessibility & Inclusion

Aplicar boas práticas gerais de acessibilidade, incluindo contraste legível, foco visível, navegação por teclado, textos alternativos quando aplicáveis e redução de movimento conforme a preferência do sistema. Alertas e estados importantes não devem depender exclusivamente de cor.

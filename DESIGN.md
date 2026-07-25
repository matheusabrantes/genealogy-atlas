# Design System — Raízes Abrantes

## Direção

Uma cartografia familiar contemporânea: precisa como um atlas, viva como uma rede e acolhedora o suficiente para ser compartilhada entre gerações. A interface não usa pergaminhos, árvores ilustradas ou ornamentação nostálgica.

## Cor

Estratégia restrita com cor estrutural comprometida:

- fundo: branco neutro;
- superfície: cinza quase branco levemente tingido pelo verde-petróleo;
- tinta: verde quase preto;
- primária: verde-petróleo profundo;
- destaque: coral carmim para hipóteses e linhas de pesquisa;
- evidência documentada: verde;
- alerta: âmbar;
- conflito: vermelho;
- informação: azul.

As cores devem ser implementadas em OKLCH. Estado nunca depende apenas da cor: todo vínculo recebe texto ou símbolo.

## Tipografia

Uma família humanista contemporânea para toda a aplicação, com números tabulares nas métricas. A hierarquia é fixa e previsível na superfície de produto; a apresentação inicial pode ampliar os números sem transformar o site em uma landing page genérica.

## Forma

- raios entre 10 e 16 px;
- linhas finas e precisas;
- cartões somente quando o conteúdo é realmente independente;
- nós do grafo compactos, com geração e estado de evidência visíveis;
- sombras curtas, nunca combinadas com bordas decorativas largas;
- alvos de toque de pelo menos 44 px.

## Movimento

Transições entre 150 e 250 ms para foco, seleção e expansão do grafo. A animação comunica mudança de estado e respeita `prefers-reduced-motion`.

## Privacidade

A saída compartilhável oculta nomes de pessoas potencialmente vivas. O site local pode carregar o GEDCOM privado, mas nenhum arquivo privado deve ser publicado sem revisão explícita.

# Offers RAG — vetorização centralizada do corpus Funnel of the Week

> Autor: Mikael Lovrin

## O que é

Pipeline de ETL + vetorização local (zero custo de API) que transforma os ~2093 JSONs brutos baixados do Funnel of the Week (`C:\Users\mikae\FEG\Knowledge\Offers\raw\`, ~120 marcas) num índice vetorial persistente e consultável — o "início da vetorização centralizada pra RAG" pedido em 2026-07-17. É complementar, não substituto, ao processo manual de curadoria em `Knowledge/Offers/entries/` (schema.md): as `entries/` são fichas curadas à mão, poucas e profundas; este RAG cobre **tudo** que já foi baixado, sem curadoria manual, pra busca semântica ampla.

## Por que zero custo de API

Os dados brutos (`raw/`) já são só leitura/parsing — não há chamada de LLM nenhuma no pipeline de extração/chunking. A vetorização usa o embedding default do ChromaDB (modelo `all-MiniLM-L6-v2` local, via `onnxruntime`, baixado uma vez pro cache do usuário) — nenhuma chamada à OpenAI/Anthropic/etc, nenhum custo por token. Rodar o pipeline inteiro de novo do zero é gratuito e leva poucos minutos.

## O que os dados brutos são

Cada arquivo em `raw/<marca>/raw-api/<ordem>_<lesson_id>_<slug>.json` é um objeto "lesson" da API do Circle.so (a comunidade de onde o Funnel of the Week é exportado), **duplo-encodado em JSON** (o conteúdo do arquivo é uma string JSON contendo JSON escapado — sempre fazer `json.loads()` duas vezes). O corpo de texto rico vem em formato de árvore ProseMirror (`serialized_rich_text_body.body.content`, nós tipo `paragraph`/`bulletList`/`heading`). Cerca de 22% dos arquivos (`landing-page`, alguns `checkout-page`) são essencialmente screenshots sem texto (só `inline_attachments` com imagem) — ficam marcados como `is_image_only: true`, prontos pra um futuro passo de OCR/visão sem precisar mudar o resto do pipeline.

## Pipeline (3 scripts, rodar em sequência)

```
scripts/extract.py         raw/*.json (2093 arquivos)  → vectorstore/corpus.jsonl (1 linha por lesson, texto limpo + metadados)
scripts/chunk.py           vectorstore/corpus.jsonl    → vectorstore/chunks.jsonl (4090 chunks, ~1000 chars, overlap de 2 linhas)
scripts/embed_and_store.py vectorstore/chunks.jsonl    → vectorstore/chroma/ (coleção persistente "offers_funnel_analysis", 3639 chunks com texto real)
```

`extract.py` NÃO usa o campo `circle_ios_fallback_text` do Circle (ele às vezes concatena bloco com bloco sem separador, gerando texto colado) — em vez disso caminha a árvore ProseMirror manualmente, preservando parágrafo/bullet/heading como linhas separadas, o que dá chunks bem melhores.

### Rodar do zero (ex. depois de baixar mais marcas novas no `raw/`)

```bash
cd C:\Users\mikae\FEG\Ferramentas\offers-rag
.venv\Scripts\python.exe scripts\extract.py
.venv\Scripts\python.exe scripts\chunk.py
.venv\Scripts\python.exe scripts\embed_and_store.py   # recria a coleção do zero (drop + recreate), nunca deixa lixo de rodada anterior
```

(Uma vez, se `.venv` não existir: `python -m venv .venv` seguido de `.venv\Scripts\python.exe -m pip install chromadb`.)

## Como consultar (qualquer agente/skill do ecossistema)

```bash
cd C:\Users\mikae\FEG\Ferramentas\offers-rag
.venv\Scripts\python.exe scripts\query.py "authority medical advisory board doctor trust" --n 5
.venv\Scripts\python.exe scripts\query.py "cancellation flow friction" --n 5 --brand mars-men   # filtra por marca
.venv\Scripts\python.exe scripts\query.py "unique mechanism cortisol villain" --json             # saída JSON pra consumo por outro script/agente
```

Cada resultado traz: `brand`, `slug` (tipo de análise — `checkout-page`, `funnel-takeaways`, `authority-trust-layers`, `vsl-analysis`, etc.), `title`, `source_path` (caminho de volta ao JSON bruto original), `distance` (menor = mais similar), e o texto do chunk.

**Taxonomia de tipos de análise mais comuns** (campo `slug`, útil pra filtrar mentalmente o que procurar): `funnel-map-in-miro`, `upsell-N`, `funnel-details`, `checkout-page`, `landing-page`, `post-purchase-page`, `thank-you-page`, `sales-page`, `on-page-cart`, `order-form`, `key-notes-takeaways`, `meta-ads-strategy`, `traffic-overview-similarweb`, `quiz-page`, `advertorial-page`, `homepage-brand-positioning`, `vsl-analysis`, `authority-trust-layers`, `funnel-takeaways`, `cancellation-flow`.

## Validado em 2026-07-17

3 queries de sanidade rodadas (mecanismo de absorção intestinal, fricção de cancelamento/retenção, autoridade de fundador/médico) — todas retornaram chunks altamente relevantes e cross-brand, incluindo achados diretamente úteis pro trabalho atual da Badrock (ex. `mars-men` — concorrente direto de Low T/TRT já mapeado como gap em `Knowledge/CLAUDE.md` — apareceu com detalhamento de "medical advisory board" e "founder-as-mirror" prontos pra inspirar o Beef Organ Complex).

## Próximos passos possíveis (não feitos ainda, é "início" por design)

1. **OCR dos ~451 chunks image-only** (landing pages/checkout screenshots) — daria acesso ao conteúdo visual que hoje só existe como imagem.
2. **Promover achados validados pra `Knowledge/Offers/entries/`** — o RAG é busca ampla, não substitui a curadoria estruturada (schema.md) para as ofertas mais relevantes/validadas.
3. **Reconstruir o índice incrementalmente** em vez de recriar do zero, se o volume de `raw/` crescer muito (hoje recriar do zero leva poucos minutos, não é um problema ainda).
4. **Trocar o embedding default por um modelo melhor** (ex. via API paga) se a qualidade de retrieval não for suficiente pra um uso mais exigente — a estrutura de `chunks.jsonl` não muda, só o script `embed_and_store.py`.

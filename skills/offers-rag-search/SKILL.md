---
name: offers-rag-search
description: Busca semântica sobre o corpus completo de análises de funil/oferta de ~120 marcas concorrentes (Funnel of the Week), indexado localmente em Knowledge/Offers/vectorstore. Use SEMPRE que o usuário pedir para pesquisar como um concorrente estrutura oferta/funil/checkout/upsell/autoridade/mecanismo, pedir benchmark de um nicho, perguntar "quem mais faz X", ou antes de desenhar uma oferta/mecanismo/bundle novo para qualquer marca do grupo FEG — consulte este índice ANTES de assumir que o dado não existe ou de pesquisar do zero na web.
---

# Offers RAG Search

Índice vetorial local, sem custo de API, sobre os ~2093 JSONs brutos de análise de funil (`Knowledge/Offers/raw/`, ~120 marcas concorrentes reais — suplementos, beleza, infoproduto, ecom). Construído em 2026-07-17 (ver `Ferramentas/offers-rag/CLAUDE.md` para detalhe do pipeline).

## Quando usar

- Antes de desenhar mecanismo/oferta/bundle/pricing pra qualquer marca do grupo (Axen, Badrock, Dewlyte, Synera) — checar como marcas adjacentes já resolveram o mesmo problema.
- Quando o usuário perguntar sobre um concorrente específico (ex. "o que sabemos sobre Mars Men/Ancestral Supplements/Armra") — mesmo que não exista uma `entries/NNN_slug.json` curada pra essa marca, o corpus bruto provavelmente tem.
- Quando o usuário pedir benchmark de categoria/nicho ("como concorrentes de Low T fazem autoridade médica", "como funcionam flows de cancelamento em assinatura de suplemento").
- Como pré-passo do `mechanism-lab` (Fase 1 — Competitor Research) sempre que o produto tiver algum concorrente plausível neste corpus.

## Como consultar

Rodar via Bash/PowerShell (funciona a partir de qualquer diretório, o comando já usa caminho absoluto):

```
cd C:\Users\mikae\FEG\Ferramentas\offers-rag
.venv\Scripts\python.exe scripts\query.py "sua pergunta em linguagem natural" --n 6 --json
```

Flags úteis:
- `--brand <slug>` — filtra pra uma marca específica (slug = nome da pasta em `Knowledge/Offers/raw/`, ex. `mars-men`, `armra`, `ancestral-supplements` se existir).
- `--json` — sempre use esta flag quando for você (Claude) consumindo o resultado para sintetizar, não o formato de texto legível.
- Sem `--json` — formato legível, útil se o usuário quiser ver o output bruto ele mesmo.

Cada resultado JSON traz `brand`, `slug` (tipo de análise: `checkout-page`, `funnel-takeaways`, `authority-trust-layers`, `vsl-analysis`, `cancellation-flow`, etc.), `title`, `text` (o chunk), `distance` (menor = mais relevante), e `source_path` (caminho de volta ao JSON bruto original, caso precise ler o arquivo inteiro pra mais contexto).

## Como usar o resultado

1. Rode 1-3 queries variando a formulação se a primeira não trouxer nada relevante (é busca semântica, não por palavra-chave exata — reformular ajuda).
2. Sintetize os achados no formato que a tarefa pedir — não cole o JSON bruto pro usuário, extraia o insight acionável.
3. Se o achado for genuinamente valioso e reutilizável (não só uma observação pontual), sugira promovê-lo para uma entry estruturada em `Knowledge/Offers/entries/NNN_slug.json` (ver `Knowledge/Offers/schema.md`) — o RAG é para descoberta ampla, as `entries/` são para o conhecimento mais validado e denso.
4. **Nunca inventar dado que não veio do resultado da query** — se a busca não retornar nada relevante sobre uma marca/pergunta específica, diga isso explicitamente em vez de complementar com suposição.

## Cerca de 22% dos chunks são "image-only"

Telas de landing page/checkout de algumas marcas foram capturadas só como screenshot (sem OCR ainda) — a busca semântica não vai encontrar texto nelas. Se o usuário perguntar especificamente sobre o visual de uma página e a busca não trouxer nada, mencione essa limitação em vez de simplesmente reportar "não encontrado".

# Offers RAG

**Indexação semântica local do corpus Funnel of the Week (~2000 ofertas)**

## O que é

Pipeline de ETL + vetorização local (zero custo de API) que indexa ~2000 arquivos brutos do Funnel of the Week em embeddings vetoriais persistentes. Permite busca semântica ampla ("o Stefan já falou sobre X?") sem custo de API.

Complementar (não substituto) à curadoria estruturada — RAG é busca ampla, curadoria é profundidade.

## Instalação

1. Clone ou baixe o repositório
2. Configure venv: `python -m venv .venv`
3. Instale deps: `.venv\Scripts\python.exe -m pip install chromadb`
4. Rodar do zero (primeira vez ou após novos dados):
   ```bash
   .venv\Scripts\python.exe scripts\extract.py
   .venv\Scripts\python.exe scripts\chunk.py
   .venv\Scripts\python.exe scripts\embed_and_store.py
   ```

## Como usar

```bash
# Busca semântica básica
.venv\Scripts\python.exe scripts\query.py "authority medical advisory board" --n 5

# Filtrar por marca
.venv\Scripts\python.exe scripts\query.py "cancellation flow" --n 5 --brand mars-men

# Saída JSON (para consumo por script/agente)
.venv\Scripts\python.exe scripts\query.py "mecanismo cortisol" --json
```

**Saída por resultado:**
- `brand` — fonte/nicho
- `slug` — tipo de análise (vsl-analysis, checkout-page, etc.)
- `title` — nome do lesson
- `distance` — similaridade (menor = mais similar)
- `text` — conteúdo do chunk

## Dados Brutos

Indexa 3 fontes do corpus Stefan Georgi:
- `WeeklyTraining` (~107 arquivos) — calls semanais
- `Main-Call-Recordings` (~113 arquivos) — masterclasses
- `Misc-Assets` (~130 arquivos) — newsletters, compliance calls

Total: ~2093 arquivos, ~3639 chunks vetorizados

## Zero Custo

Embedding via ChromaDB local (`all-MiniLM-L6-v2` + ONNX) — sem chamada de API paga. Roda offline, reutilizável infinitas vezes.

## Taxonomia de Slugs (Filtros Úteis)

- `vsl-analysis`, `checkout-page`, `landing-page` — estrutura de funnel
- `funnel-takeaways`, `key-notes` — insights
- `meta-ads-strategy` — media buying
- `authority-trust-layers`, `homepage-positioning` — branding
- `cancellation-flow` — retenção

## Tempo + Custo

- Extração: ~5 min (parse JSON)
- Chunking: ~2 min
- Embedding: ~10-15 min (primeira vez)
- **Custo:** $0 (tudo local)

## Dependências

- Python 3.8+
- chromadb + onnxruntime

## Licença

CC 4.0 — Veja LICENSE.md

## Autor

Mikael Lovrin — FEG (Direct Response Marketing)

---

**Baseado em:** Funnel of the Week corpus (Stefan Georgi community)

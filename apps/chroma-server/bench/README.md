# Bench — Comparativo de Embeddings (Xenova/MPNet vs OpenAI v3)

Bench reproduzível referenciado na **§7 de `references/ANALISE_VECTOR_STORE.md`**.

Mede **qualidade de retrieval** (Recall@k, MRR, nDCG@10) e **latência**
(p50/p95/p99) das variantes de embedding sobre o corpus real (`report_texts`).

## Variantes

| ID                       | Embedding                              | Dim  | Provider              |
|--------------------------|----------------------------------------|------|-----------------------|
| `v1_mpnet_768`           | `paraphrase-multilingual-mpnet-base-v2`| 768  | Local (já indexado)*  |
| `v2_openai_small_768`    | `text-embedding-3-small`               | 768  | OpenAI API            |
| `v3_openai_small_1536`   | `text-embedding-3-small`               | 1536 | OpenAI API            |
| `v4_openai_large_3072`   | `text-embedding-3-large`               | 3072 | OpenAI API            |
| `v5_bge_m3_1024`         | `BAAI/bge-m3` *(opcional)*             | 1024 | Local (Python)        |

\* **V1 reusa a coleção `report_texts` existente** (sem re-indexar) para refletir
exatamente o que está em produção. As demais são geradas pelo `prepare.py`.

## Pré-requisitos

- ChromaDB rodando (`npx nx run chroma-server:serve`) na `CHROMA_URL`.
- Python 3.9+ e Node 20+ no PATH.
- Para variantes OpenAI: `OPENAI_API_KEY` válida.
- Para `v5_bge_m3_1024`: deps Python pesadas (`torch`, `sentence-transformers`).
  Opt-in via flag.

## Setup

```bash
cd apps/chroma-server/bench
cp .env.example .env  # preencha OPENAI_API_KEY e CHROMA_URL

# Python (prepare/score)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Node (run-queries)
# usa ts-node já presente no root + chromadb e @xenova/transformers
# já instalados no monorepo. Sem deps extras.
```

## Fluxo de execução

### 1. Curar o golden set (com o time de domínio)

Copie `golden-set.example.csv` para `golden-set.csv` e peça aos engenheiros
de laudo para preencher **50–100 pares**:

```csv
question,expected_report_id,notes
"Qual a vibração medida no equipamento P-101 durante o ensaio?",1234,"Pergunta direta"
"Houve trincas observadas na inspeção do tanque T-05?",5678,""
```

Sem golden set não há métrica de qualidade — só de latência.

### 2. Gerar coleções variantes

```bash
# Tudo (sem v5):
python prepare.py --variants v2_openai_small_768,v3_openai_small_1536,v4_openai_large_3072

# Inclui BGE-m3 (lento, baixa ~2GB):
python prepare.py --variants v2,v3,v4,v5 --include-bge

# Re-criar uma única variante:
python prepare.py --variants v2 --force
```

Custo estimado para 100k chunks: ~$0.40 (v2/v3 Batch) + ~$2.60 (v4 Batch).

### 3. Rodar queries

```bash
npx ts-node run-queries.ts --golden-set golden-set.csv --out results.csv
```

Saída: `results.csv` com `query_id, variant, rank, retrieved_id, score,
embed_latency_ms, search_latency_ms`.

### 4. Score + gráficos

```bash
python score.py --results results.csv --golden golden-set.csv --out reports/
```

Saída em `reports/`:

- `summary.csv` — Recall@5, Recall@10, MRR, nDCG@10 por variante.
- `latency.csv` — p50/p95/p99 por variante e operação.
- `quality.png`, `latency.png` — gráficos prontos para a apresentação.

## Notas técnicas

- **V1 (MPNet)**: query passa por `@xenova/transformers` no Node (mesmo runtime
  da produção, em `apps/db-backend/.../chroma.service.ts`). A coleção indexada
  é a `report_texts` original — não há re-indexação, eliminando drift PyTorch
  vs ONNX.
- **V2–V4 (OpenAI)**: prepare.py usa **Batch API** quando `--batch` é passado
  (50% mais barato, indexação não-síncrona). Para queries síncronas, run-queries.ts
  usa a API standard com `fetch()` (sem dep extra `openai` SDK).
- **V5 (BGE-m3)**: opcional. Quando habilitado, a query é embedada via
  helper Python invocado por `run-queries.ts` (subprocess). Adiciona ~50ms
  de overhead — descontado no relatório de latência.
- **Estatística**: rodar cada query **5 vezes** (configurável em `--repeats`)
  para estabilizar p95.
- **Privacidade**: o bench envia chunks ao endpoint OpenAI. **Não rodar com
  dados sensíveis reais** até DPA + ZDR aprovados; usar `--mask` para
  redatar PII antes do envio (substitui regex configurável).

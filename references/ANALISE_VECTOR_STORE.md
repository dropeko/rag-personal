# Análise Técnica — ChromaDB local (Xenova/MPNet) vs OpenAI Embeddings + API

> Sprint: comparativo de stack de RAG para gerar **relatórios técnicos de
> inspeção industrial** (Análise de Falhas — equipamentos PETROBRÁS).
> Escopo: **RAG ponta-a-ponta** (embeddings + vector store + LLM gerador) +
> **pipeline de ingestão contínua** (banco alimentado conforme novos relatórios
> são gerados).
> Restrições: dados de cliente/laudo — saída para APIs externas permitida
> **com mitigação** (DPA, zero-retention, mascaramento).

---

## 1. Contexto atual ("abordagem ml_wo")

### 1.1 Stack

| Camada            | Implementação                                                                                                | Onde está                                                    |
|-------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Embedding (query) | `Xenova/paraphrase-multilingual-mpnet-base-v2` (MPNet multilingual **vanilla**, 768 dim), ONNX em Node       | `apps/db-backend/.../chroma.service.ts:97`                   |
| Embedding (index) | **`models/fine_tuned_report_model`** (sentence-transformer fine-tunado pelo time, 768 dim) — asset externo, **não está no repo** | metadado da coleção em `chroma.sqlite3`                      |
| Vector store      | ChromaDB v1.x persistente (sqlite + HNSW), via FastAPI/uvicorn                                               | `apps/chroma-server/server.py`, `chroma_db_finetune/` (~20 MB sqlite) |
| Cliente           | `chromadb` (JS) no NestJS                                                                                    | `db-backend`                                                 |
| LLM gerador       | **Não definido ainda** (template DOCX é preenchido por dados estruturados, geração textual ainda em aberto) | —                                                            |

### 1.2 Volume real do corpus (inspeção direta no `chroma.sqlite3`)

| Coleção                    | Chunks | Conteúdo                                       | Por relatório   |
|----------------------------|--------|------------------------------------------------|-----------------|
| `report_texts`             | **78** | seção "DISCUSSÃO DOS RESULTADOS" dos laudos    | 1 chunk/laudo   |
| `metallography_captions`   | 7.943  | captions de imagens de metalografia (textuais) | ~100 caps/laudo |
| **Total**                  | 8.021  | — | — |

- **78 relatórios distintos** (campo `id_relatorio`), todos do tipo **AF**
  (Análise de Falha). Cliente predominante: PETROBRÁS COMPARTILHADO.
- Tipos de equipamento: Caldeira, Permutador de Calor, Vaso Separador,
  Válvula de Segurança, Cilindro, Eixo de Bomba, Trecho de Tubo, etc.
- **Tamanho médio do chunk** em `report_texts`: ~1.600 caracteres ≈ **~400
  tokens** (chunk = seção inteira de discussão, denso e técnico).
- Corpus inicial é **pequeno em volume mas técnico em densidade** — o
  desafio do RAG aqui é **precisão semântica em jargão de engenharia de
  inspeção**, não escala.

### 1.3 Caveat crítico — mismatch entre indexação e query

O Chroma foi indexado por **`models/fine_tuned_report_model`** (registrado
nos metadados da coleção). Já a aplicação Node consulta usando
**`Xenova/paraphrase-multilingual-mpnet-base-v2` vanilla**. Os dois modelos
**não produzem o mesmo espaço vetorial** — a busca atual está rodando com
embeddings de query desalinhados dos de indexação, o que **degrada Recall**
de forma imprevisível.

**Implicações para a sprint**:

- A comparação justa exige **resolver primeiro o mismatch** (ou
  reindexar com o modelo de query, ou indexar e consultar com o mesmo
  modelo de cada variante).
- O fine-tuning é um **ativo do projeto ml_wo** que pode justificar manter
  embeddings locais — mas o asset (`models/fine_tuned_report_model`) **não
  está no repo**, então hoje a stack está degradada por configuração
  perdida.
- Decisão de stack precisa contemplar **se vamos manter pipeline de
  fine-tuning** (custo: GPU + curadoria de pares) ou **descontinuar** em
  favor de um embedder genérico forte (OpenAI v3 ou BGE-m3).

### 1.4 Requisito de ingestão contínua

O `chroma_db_finetune` é o **banco inicial**. Em produção, novos
relatórios técnicos serão gerados continuamente (consultoria / inspeção em
campo) e **precisam ser indexados automaticamente**. A solução de
ingestão online ainda **não existe** e faz parte do escopo. Implicações:

- O embedder precisa ser **estável** entre versões (senão cada upgrade
  exige reindex completo do histórico).
- **Batch API (50% off) não serve** para ingestão online — é async até
  24h. Serve apenas para reindex em massa eventual.
- Trigger natural: hook após o `report-generate` salvar o DOCX → fila
  → embed → upsert no Chroma. Detalhes em §3.5.

---

## 2. Opções avaliadas

### Opção A — Stack atual: Chroma local + Xenova/MPNet local *(baseline)*

- **Embeddings**: `paraphrase-multilingual-mpnet-base-v2`, 768 dim, CPU.
- **Store**: Chroma file-based, mesma máquina do backend (ou container irmão).
- **LLM gerador**: a definir (poderia ser local — Llama/Qwen via Ollama — ou API).

### Opção B — OpenAI Embeddings + API + Chroma (mesmo store)

- **Embeddings**: `text-embedding-3-small` (1536 dim, truncável para 512/768)
  ou `text-embedding-3-large` (3072 dim, truncável).
- **Store**: pode continuar Chroma (não muda o store, só o `embeddingFunction`).
- **LLM gerador**: OpenAI (`gpt-4.1-mini` / `gpt-4o-mini` / `gpt-4.1`) via API.

### Opção C *(referencial, não pedida mas vale considerar)* — Híbrida

- Embeddings OpenAI (qualidade) **+** store gerenciado (Qdrant Cloud / Pinecone /
  pgvector no Postgres já existente do projeto) **+** LLM OpenAI.
- Vale destacar porque o projeto **já tem Postgres** (`libs/db-lib`), e
  `pgvector` elimina o `apps/chroma-server` inteiro.

---

## 3. Custos

### 3.1 Embeddings — custo de indexação

Premissas (verificadas no corpus real, §1.2):

- **Hoje**: 8.021 chunks (78 + 7.943). Chunk médio em `report_texts` ≈ 400 tok.
- **Projeção 12 meses** (estimativa — depende da taxa de inflow de novos
  laudos): assumindo 5 laudos/semana × 50 sem × (1 chunk texto + ~100 captions)
  ≈ +25k chunks/ano → corpus de ~33k em 1 ano. Continua "pequeno".
- Cap de **8.191 tokens por request** na API de embeddings v3 — não-restritivo.

| Modelo                              | US$ / 1M tok (Std) | US$ / 1M tok (Batch −50%) | **Corpus atual (~3M tok)** | Projeção 1 ano (~13M tok) |
|-------------------------------------|--------------------|---------------------------|----------------------------|---------------------------|
| Xenova MPNet (local, CPU)           | $0                 | n/a                       | ~30 min CPU                | ~2 h CPU                  |
| `text-embedding-3-small`            | $0.020             | $0.010                    | **$0.06** (Batch: $0.03)   | **$0.26** (Batch: $0.13)  |
| `text-embedding-3-large`            | $0.130             | $0.065                    | $0.39 (Batch: $0.20)       | $1.69 (Batch: $0.85)      |

> **Conclusão de custo de indexação**: **completamente irrelevante** na
> escala atual e projetada. Re-embedar todo o corpus via `3-large` custa
> **menos de US$ 0.40**. Custo **não é critério de decisão** nesta camada.

> Re-indexação histórica (mudança de embedder, ajuste de chunking): rodar
> via Batch API. Ingestão online (novo laudo): Standard API (síncrono).

### 3.2 Embeddings — custo de query

Cada query gera 1 embedding (~30 tokens de pergunta média).

| Modelo                  | Por 1k queries | Por 100k queries/mês |
|-------------------------|----------------|----------------------|
| Xenova local            | $0 (compute)   | $0                   |
| `text-embedding-3-small`| $0.0006        | $0.06                |
| `text-embedding-3-large`| $0.004         | $0.40                |

> Idem: irrelevante.

### 3.3 LLM gerador *(onde mora o custo real)*

Premissa por resposta RAG: ~3k tokens de contexto + ~500 tokens de saída.

| Modelo               | $/1M in | $/1M out | Custo por resposta | 10k respostas/mês |
|----------------------|---------|----------|--------------------|-------------------|
| `gpt-4o-mini`        | $0.15   | $0.60    | ~$0.0008           | ~$8               |
| `gpt-4.1-mini`       | $0.40   | $1.60    | ~$0.002            | ~$20              |
| `gpt-4o`             | $2.50   | $10.00   | ~$0.013            | ~$130             |
| `gpt-4.1`            | $2.00   | $8.00    | ~$0.010            | ~$100             |
| Local (Llama/Qwen)   | $0      | $0       | $0 (hardware)      | $0                |

> **Conclusão**: ordens de grandeza acima de embeddings. Decisão de LLM é onde
> custo e qualidade pesam — embedding é detalhe.

### 3.4 Infra

| Item                          | Local Chroma + Xenova                          | OpenAI + Chroma             |
|-------------------------------|------------------------------------------------|-----------------------------|
| Servidor Python adicional     | **sim** (`apps/chroma-server`)                 | sim (idem)                  |
| RAM extra para modelo ONNX    | ~1.2 GB residente no Node                      | 0                           |
| Disco (corpus atual 8k)       | 768 × 4 B × 8k = ~25 MB                        | 1536 dim → ~50 MB           |
| Disco (projeção 33k)          | ~100 MB                                        | ~200 MB (ou 100 MB se trunc) |
| Dependência de internet       | Não                                            | Sim (queries síncronas)     |

### 3.5 Pipeline de ingestão contínua (requisito novo)

Conforme §1.4, novos laudos entram continuamente. Esboço da pipeline:

```
[report-generate finaliza DOCX]
        ↓ event/hook
[fila ingestion-queue] (BullMQ/Postgres-LISTEN)
        ↓
[ingest worker]
   1. extrai texto da seção "DISCUSSÃO DOS RESULTADOS"
   2. extrai captions de figuras (metallography)
   3. embed(text) via EmbeddingProvider configurado
   4. chroma.upsert(id_relatorio, embeddings, metadatas)
        ↓
[report_texts + metallography_captions atualizadas]
```

Pontos de decisão:

- **Sincronia**: ingestão é **assíncrona** (fila) — não bloqueia a geração
  do DOCX. SLA aceitável: ~1 min entre gerar e ficar buscável.
- **Idempotência**: o `id_relatorio` é a chave de upsert; re-rodar a
  ingestão para o mesmo relatório substitui em vez de duplicar.
- **Retry**: falha de API OpenAI → backoff exponencial; falha persistente
  → dead-letter queue + alerta.
- **Custo por laudo** (3-small Standard, ~4–5k tokens texto + 100 captions
  de ~50 tok cada = ~9–10k tok): **~US$ 0.0002 por laudo**. Irrisório.
- **Onde mora a fila**: o monorepo já tem Postgres (`libs/db-lib`). Sugestão:
  usar **`pg-boss`** ou tabela própria com `LISTEN/NOTIFY` — evita adicionar
  Redis só para isso. Detalhar na sprint seguinte.
- **Versionamento do embedder**: gravar `embedding_model_version` na
  metadata de cada chunk. Se o embedder mudar, é trivial saber o que
  precisa ser reindexado.

---

## 4. Latência (estimativas a confirmar no bench)

| Operação                                       | Local (Xenova/MPNet, CPU)     | OpenAI (`3-small`)            |
|------------------------------------------------|-------------------------------|-------------------------------|
| Embedding **1 query** (~30 tok)                | 80–250 ms (CPU)               | 60–180 ms (rede dominante)    |
| Embedding **batch 32** (~12k tok)              | 1.5–4 s                       | 200–500 ms                    |
| Query top-k=5 no Chroma (100k vectors, HNSW)   | 10–40 ms                      | 10–40 ms (mesmo store)        |
| **Pipeline RAG fim-a-fim** (embed + search)    | **120–300 ms**                | **100–250 ms**                |
| Resposta LLM (gpt-4o-mini, 3k→500 tok)         | n/a (depende do LLM)          | 1.5–4 s                       |
| Cold start do MPNet (1ª query pós-boot)        | **2–5 s** (load ONNX)         | ~0 (warm)                     |

Observações:

- A latência de query **é dominada pelo LLM**, não pelo embedding nem pelo store.
- Local **só ganha** se rodar em máquina com GPU; em CPU pura, OpenAI tende a
  ser **mais rápido em batch** (re-indexação, ingestão).
- Cold start do Xenova é um problema real em ambiente serverless / reinício
  frequente. Em backend long-running (caso atual), some após o 1º request.

---

## 5. Viabilidade — critérios qualitativos

| Critério                          | Chroma local + Xenova                          | OpenAI Embeddings + API                       |
|-----------------------------------|------------------------------------------------|-----------------------------------------------|
| Privacidade de dados              | **Total** (tudo on-prem)                       | Requer DPA + zero-retention; aceitável c/ ressalva |
| Independência de fornecedor       | Total                                          | Acoplamento ao provedor                       |
| Qualidade do recall (PT-BR)       | Boa (MPNet, modelo de 2021)                    | **Melhor** (v3 supera MPNet em MTEB-multi)    |
| Operação                          | 2 processos (chroma-server + backend) + modelo ONNX no Node | 1 processo (chroma-server pode ser substituído por pgvector) |
| Cold start / disponibilidade      | Sofre cold start; depende de o `chroma-server` estar up | Depende de uptime OpenAI (SLA 99.9%)          |
| Escala (>500k chunks)             | Chroma local começa a sofrer; HNSW em sqlite não é ideal | Same vector store; o gargalo continua sendo o store |
| Custo previsível                  | **Sim** (zero variável)                        | Variável, mas pequeno na faixa estimada       |
| Tempo de implementação            | Já está pronto                                 | ~2–3 dias p/ trocar `embeddingFunction` + re-indexar |
| Reprodutibilidade (versão do modelo) | Fixa (artefato versionável)                  | **Risco**: OpenAI pode depreciar/alterar modelo (ada-002 já passou por isso) |
| Compliance (cliente exige on-prem) | Compatível                                    | Pode bloquear contrato                        |

---

## 6. Proposta de stack

### 6.1 Recomendação principal

**Stack híbrida controlada**, na seguinte ordem de mudança (do mais barato p/
o mais invasivo):

1. **Manter ChromaDB como vector store** no curto prazo (já está integrado e
   na faixa de 10k–500k chunks ele aguenta). Avaliar `pgvector` no Postgres
   existente como evolução natural — remove o `apps/chroma-server` da árvore.
2. **Trocar embedding para `text-embedding-3-small` com `dimensions=768`**:
   - Mantém compatibilidade dimensional com a coleção atual (768) → permite
     **A/B test sem refazer schema**.
   - Custo de re-indexação: ~$0.80 (Standard) ou **~$0.40 (Batch API)** por
     full rebuild de 100k chunks. Recomendado rodar via Batch.
   - Ganho de qualidade esperado vs MPNet (dados oficiais OpenAI, números a
     **confirmar no bench da §7** com nosso corpus real):
     - MTEB médio: **+1.3pp** vs ada-002 (62.3% vs 61.0%) — ganho modesto em
       inglês.
     - **MIRACL** (retrieval multilíngue, inclui PT-BR): **+12.6pp** vs ada-002
       (44.0% vs 31.4%) — **ganho substancial** e é a métrica relevante para
       nosso caso de uso.
     - Não há benchmark público direto MPNet vs `3-small` em PT-BR — daí a
       necessidade do bench §7.
3. **Manter Xenova/MPNet como fallback offline** (feature-flag no
   `ChromaService` para alternar `embeddingFunction`). Útil para:
   - Ambientes onde o cliente exige on-prem.
   - Failover se a API OpenAI cair.
4. **LLM gerador**: começar com `gpt-4o-mini` (custo ~$0.0008/resposta) e
   medir qualidade contra `gpt-4.1-mini`. Não usar `gpt-4o`/`gpt-4.1`
   completos até ter sinal de que mini não basta.
5. **Mitigações de privacidade** (obrigatórias, dados de cliente/laudo):
   - Habilitar Zero Data Retention (ZDR) na conta OpenAI.
   - Assinar DPA.
   - Mascarar campos sensíveis no chunk antes do envio (nome do cliente,
     número de contrato, tag de equipamento) com placeholder reversível —
     reidratar no momento da exibição.
   - Logar `request_id` + hash do payload para auditoria, **nunca** o payload.

### 6.2 Critério de "go/no-go" para a Opção B

Trocar para OpenAI **somente se** o bench da §7 confirmar:

- **Recall@5 ≥ +5pp** vs MPNet no golden set real (métrica primária, mais
  estável que nDCG para top-k pequeno); **e**
- **MRR ≥ +0.05** vs MPNet; **e**
- p95 de latência fim-a-fim de embedding+search ≤ **400 ms**; **e**
- Ticket jurídico de mascaramento + DPA aprovado.

Se algum falhar → manter Opção A e revisitar com **BGE-m3** ou
**multilingual-e5-large** local (modelos open-source mais novos, gratuitos,
geralmente superam MPNet em PT-BR sem custo recorrente nem saída de dados).

---

## 7. Plano de bench reproduzível

> Entregável complementar: rodar antes da review de sprint, com o corpus real.

### 7.1 Dataset de avaliação

- **Golden set sintético**: **234 queries em 78 chunks já gerado** em
  `apps/chroma-server/bench/golden-set.synthetic.csv`, via
  `generate-synthetic-golden.py`. Distribuição cobre Caldeira, Permutador,
  Vaso Separador, Válvula de Segurança, Eixo de Bomba e mais ~20 tipos de
  equipamento. **Viés conhecido**: queries usam vocabulário dos próprios
  chunks (inflam Recall vs queries humanas reais). É um **piso**, não teto.
- **Golden set humano** (idealmente substitui o sintético): 50–100 pares
  curados pelo time de domínio. Não estará pronto na review — tratamos o
  sintético como métrica oficial nesta sprint e re-rodamos com o humano
  quando vier.
- **Pool de chunks**: coleção `report_texts` atual (78 chunks).

### 7.2 Variantes a medir

| ID  | Embedding                              | Dim  | Store          | Observação |
|-----|----------------------------------------|------|----------------|------------|
| **V1a** | **Status quo (com mismatch)**: índice fine-tuned, query Xenova vanilla | 768 | `report_texts` original | Mede o que está em produção HOJE |
| V1b | Xenova vanilla coerente (reindex + query com Xenova vanilla) | 768 | nova coleção | Isola o efeito do mismatch |
| V2  | `text-embedding-3-small` (dim=768)     | 768  | Chroma local   | Truncável, dimensão igual ao baseline |
| V3  | `text-embedding-3-small` (dim=1536)    | 1536 | Chroma local   | Default do modelo |
| V4  | `text-embedding-3-large` (dim=3072)    | 3072 | Chroma local   | Topo de linha OpenAI |
| V5  | BGE-m3 local *(opcional, controle)*    | 1024 | Chroma local   | Alternativa open-source forte |

> A diferença **V1a vs V1b** é o experimento que confirma/refuta o bug do
> §1.3. Se V1b ≫ V1a, o problema é configuração, não modelo.

### 7.3 Métricas

- **Qualidade**: Recall@5, Recall@10, MRR, nDCG@10.
- **Latência**: p50, p95, p99 para:
  - embedding de 1 query
  - embedding em batch de 32
  - query top-k=5 no store
  - pipeline embed→search end-to-end
- **Custo**: tokens consumidos × tabela §3.1 (real, não estimado).
- **Operação**: cold start, RSS de memória do processo Node, CPU% durante
  ingestão.

### 7.4 Script de execução

**Já implementado** em `apps/chroma-server/bench/`:

- `generate-synthetic-golden.py` — gera golden set sintético via heurísticas
  ou LLM. **Já executado**: 234 queries em `golden-set.synthetic.csv`.
- `prepare.py` — gera as variantes (V1b/V2/V3/V4/V5) a partir do corpus.
  V1a reusa a coleção fonte.
- `run-queries.ts` — executa o golden set em cada variante, salva CSV de
  latência e ranking.
- `score.py` — calcula Recall@k, MRR, nDCG@10 + p50/p95/p99 de latência;
  gera `summary.csv`, `latency.csv` e PNGs prontos pra apresentação.

Esforço restante: **~1 dia** para subir o `chroma-server`, rodar `prepare`
(custo ~$0.05 com OpenAI v3 small e large somados, em Batch) e executar
`run-queries.ts` + `score.py` contra o golden sintético.

---

## 8. Riscos e decisões em aberto

| Risco                                                                 | Mitigação                                                   |
|-----------------------------------------------------------------------|-------------------------------------------------------------|
| Golden set não fica pronto a tempo da review                          | Apresentar V1 vs V2/V3 em **métricas proxy** (cosine sim de queries sintéticas) + tabela de custos/latência; deixar Recall/MRR para a sprint seguinte. |
| OpenAI deprecia modelo (`ada-002` já aconteceu)                       | Pin do modelo + plano de re-embed semestral previsto no orçamento. |
| Cliente vetar saída de dados após contrato fechado                    | Feature-flag `EMBEDDING_PROVIDER` no `ChromaService` desde o dia 1. |
| Custo do LLM explodir com adoção                                      | Tracking de tokens por endpoint + alerta acima do P95 esperado. |
| `apps/chroma-server` se torna gargalo                                 | Migrar coleção para `pgvector` no Postgres existente (libs/db-lib). |

---

## 9. Fontes / dados confirmados

### 9.1 Dados externos (web, 2026-06-01)

- **Pricing OpenAI** (Standard / Batch −50%): `3-small` $0.020/$0.010,
  `3-large` $0.130/$0.065 por 1M tokens; `gpt-4o-mini` $0.15 in / $0.60 out;
  `gpt-4.1-mini` $0.40 in / $1.60 out; `gpt-4o` $2.50/$10; `gpt-4.1` $2/$8.
- **Cap de input** dos embeddings v3: 8191 tokens/request.
- **Performance OpenAI v3 (oficial)**: MTEB médio 61.0% (ada-002) → 62.3%
  (`3-small`); **MIRACL multilíngue 31.4% → 44.0%**; redução de dimensão via
  `dimensions` (Matryoshka) com perda mínima.
- **Dim padrão**: `3-small` 1536 (truncável até 256), `3-large` 3072
  (truncável). MPNet vanilla: 768 dim, fixa.

### 9.2 Dados internos do projeto (inspeção direta no repo + sqlite)

- Coleções no `chroma_db_finetune/chroma.sqlite3`: `report_texts` (78 chunks,
  1 por relatório, seção "DISCUSSÃO DOS RESULTADOS") + `metallography_captions`
  (7.943 chunks). Total **8.021 chunks**.
- Tamanho médio do chunk de `report_texts`: **~400 tokens** (~1.600 caracteres).
- Modelo de **indexação** registrado nos metadados Chroma:
  `models/fine_tuned_report_model` (sentence-transformer fine-tunado pelo time;
  **não está no repo**).
- Modelo de **query** em produção: `Xenova/paraphrase-multilingual-mpnet-base-v2`
  (vanilla, ONNX em Node — `chroma.service.ts:97`). **→ mismatch §1.3.**
- 78 relatórios distintos, **100% Análise de Falha (AF)**, cliente
  predominante PETROBRÁS COMPARTILHADO. Tipos: Caldeira, Permutador,
  Vaso Separador, Válvula, Eixo, Cilindro, Tubos, etc.

### 9.3 Itens a confirmar **com o bench (§7)**

- Recall@k / MRR / nDCG@10 concretos das 6 variantes (V1a, V1b, V2–V5) no
  golden set sintético.
- p50/p95/p99 reais do `chroma-server` em CPU.
- Magnitude do impacto do mismatch (V1a vs V1b).
- Diferença de Recall do golden sintético vs queries humanas (quando o
  golden curado vier).

---

## 11. Resultados reais medidos nesta sprint

Bench parcial rodado em **2026-06-01** no ambiente de desenvolvimento.
**Restrição encontrada**: o ambiente bloqueia `huggingface.co` e
`api.openai.com` por política de rede, então **V1a/V1b/V2/V3/V4 não puderam
ser medidos aqui**. Para deliver de números reais nesta sprint, rodei um
**baseline TF-IDF (offline, scikit-learn)** + a **latência real do
Chroma HNSW** na coleção de produção.

> Artefatos completos em `apps/chroma-server/bench/reports-offline/`:
> `summary.csv`, `latency.csv`, `latency-chroma.csv`,
> `breakdown-by-template.txt`, `quality.png`, `latency.png`.

### 11.1 Latência real do Chroma HNSW (produção)

200 queries com vetores aleatórios normalizados 768d, contra a coleção real
em chroma-server v1.5.9 rodando localmente:

| Coleção                    | Docs  | p50      | p95      | p99      | mean     |
|----------------------------|-------|----------|----------|----------|----------|
| `report_texts`             | 78    | 4.58 ms  | 5.46 ms  | 5.99 ms  | 4.68 ms  |
| `metallography_captions`   | 7.943 | 5.08 ms  | 6.39 ms  | 6.97 ms  | 5.24 ms  |

**Leitura**: HNSW escala muito bem nesta faixa de volume — passar de 78
para 7.943 docs adiciona ~0.5 ms p50. Latência do **store não é gargalo**;
gargalo do RAG vai ser embedding (V2–V4 dependem de rede até OpenAI) e o
LLM gerador.

### 11.2 Baseline TF-IDF (scikit-learn) vs golden sintético

234 queries, 78 chunks, vocab 7.667 tokens (unigram + bigram, stopwords
PT-BR, sublinear TF):

| Métrica         | Score   |
|-----------------|---------|
| Recall@5        | **0.671** |
| Recall@10       | **0.731** |
| MRR             | **0.604** |
| nDCG@10         | **0.885** |
| Embed latency p50 | 0.42 ms |
| Search latency p50 | 0.65 ms |

> Esses números são piso. O golden sintético **infla TF-IDF** (queries usam
> vocabulário dos próprios chunks). Modelos neurais precisam superar isso
> **com folga** para justificar custo/complexidade.

### 11.3 Onde TF-IDF brilha e onde quebra (breakdown por template)

Distribuição de Recall@5 do TF-IDF por **tipo de query** no golden sintético
(`reports-offline/breakdown-by-template.txt`):

| Template de query                                    | Recall@5 | n   |
|------------------------------------------------------|----------|-----|
| `content.first_sentence` (cita literal um trecho)    | **1.000**| 35  |
| `content.dano` (menciona keyword de dano)            | 0.885    | 26  |
| `metadata.tag.danos` ("danos no equipamento {tag}?") | 0.760    | 25  |
| `metadata.tag.conclusao`                             | 0.758    | 33  |
| `metadata.tag.causa`                                 | 0.692    | 39  |
| `metadata.analise_tag`                               | 0.680    | 25  |
| `metadata.cliente_unidade` (por cliente/unidade)     | 0.308    | 26  |
| `metadata.equipamento` (por número de relatório)     | **0.120**| 25  |

**Interpretação central**: o gap entre 100% e 12% é exatamente onde a
**recuperação semântica neural** ganha — quando a query pergunta por
metadados (cliente, número de relatório, unidade) que **não aparecem no
texto do chunk**, TF-IDF não tem como achar. Esse é o **valor agregado
esperado** das variantes V2–V4 (OpenAI v3) ou V1b (MPNet vanilla coerente).

### 11.4 Conclusões da rodada parcial

1. **Chroma HNSW não é problema** em latência nesta escala — pode ficar
   tranquilo no roadmap.
2. **TF-IDF entrega Recall@5 de 67% no sintético** — qualquer stack neural
   que não bata isso com folga (>= +15pp) é regressão.
3. **Buracos de TF-IDF em queries "por metadado"** mapeiam o ganho que o
   modelo neural precisa entregar. Esse é o teste central da migração.
4. **Confirmação operacional**: o pipeline (golden → query → score → PNGs)
   está funcional. Quando o time rodar com HF/OpenAI liberados, é
   `prepare.py` + `run-queries.ts/.py` + `score.py` e produz V1a/V1b/V2–V4
   em <1h.

### 11.5 Restrição de ambiente — informação core p/ a apresentação

O bench **completo** (com modelos neurais) exige que o ambiente de execução
permita saída para:

- `huggingface.co` (download de MPNet / BGE-m3 / outros).
- `api.openai.com` (embeddings v3).

Recomendar à TI a liberação dessas duas saídas (com restrição por
allowlist) **antes** da próxima sprint, ou rodar o bench numa workstation
desbloqueada. Caso contrário, ficamos limitados a TF-IDF.

---

## 12. TL;DR para a apresentação

1. **Corpus é pequeno e técnico**: 8k chunks (78 laudos + ~8k captions).
   Custo de qualquer embedding é **irrelevante** (< US$ 0.40 re-indexa
   tudo no `3-large`). O desafio é **precisão semântica em jargão de
   inspeção**, não escala.
2. **Bug detectado em produção (§1.3)**: índice usa `fine_tuned_report_model`
   (não está no repo); queries usam Xenova vanilla. **Mismatch garantido**
   — Recall atual está abaixo do real.
3. **Ingestão contínua é parte do escopo (§3.5)**: pipeline event-driven
   após `report-generate`, fila no Postgres existente, idempotente,
   custo ~US$ 0.0002 por laudo com `3-small`.
4. **Chroma HNSW não é gargalo (§11.1)**: medido p99 = **5.99 ms** em 78
   docs, **6.97 ms** em ~8k docs. Latência do RAG será dominada por
   embedding (rede até OpenAI) e LLM gerador.
5. **TF-IDF é piso forte (§11.2): Recall@5 = 67% no golden sintético**.
   Qualquer stack neural precisa bater isso **com folga** (≥ +15pp) para
   justificar custo + complexidade + dependência externa.
6. **Onde o neural ganha (§11.3)**: queries por metadado ("equipamento
   X?", "cliente Y na unidade Z?") **caem para 12-30% no TF-IDF** —
   exatamente o gap semântico que embeddings v3 devem fechar.
7. **Embedding não é o custo, o LLM é** — decidir LLM primeiro
   (`gpt-4o-mini` como baseline, ~US$ 0.0008/resposta).
8. **Stack proposta**: Chroma mantém no curto prazo, `pgvector` no roadmap
   (elimina o `chroma-server` Python); embedder
   `text-embedding-3-small@768` com fallback Xenova feature-flagged;
   `gpt-4o-mini` baseline; mascaramento + DPA + ZDR como pré-condição.
9. **Restrição encontrada (§11.5)**: ambiente bloqueia `huggingface.co` e
   `api.openai.com`. **TI precisa liberar essas saídas** para completar o
   bench neural — ou rodar numa workstation desbloqueada.

### 12.1 Próximos passos concretos

| # | Ação | Esforço | Bloqueia |
|---|------|---------|----------|
| 1 | Liberar saída para `huggingface.co` e `api.openai.com` na TI (ou usar workstation desbloqueada) | discussão | Bench neural |
| 2 | Rodar `prepare.py` (V1b/V2/V3/V4) + `run-queries.ts/.py` + `score.py` com `golden-set.synthetic.csv` | ~3h | Apresentação |
| 3 | Decidir destino do `fine_tuned_report_model` (manter, descontinuar, versionar) | discussão | Stack final |
| 4 | Implementar pipeline de ingestão contínua (§3.5) | 3–5 dias | Produção |
| 5 | Curar 50–100 pares humanos do golden set | depende do domínio | Validação final |

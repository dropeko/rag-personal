# Análise Técnica — ChromaDB local (Xenova/MPNet) vs OpenAI Embeddings + API

> Sprint: comparativo de stack de RAG para `wo-backend` / `db-backend`.
> Escopo: **RAG ponta-a-ponta** (embeddings + vector store + LLM gerador).
> Restrições: corpus médio (10k–500k chunks); dados de cliente/laudo — saída para
> APIs externas permitida **com mitigação** (DPA, zero-retention, mascaramento).

---

## 1. Contexto atual ("abordagem ml_wo")

| Camada            | Implementação                                                                                                | Onde está                                                    |
|-------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Embedding         | `Xenova/paraphrase-multilingual-mpnet-base-v2` (MPNet multilingual, **768 dim**), ONNX em Node               | `apps/db-backend/.../chroma.service.ts:97`                   |
| Vector store      | ChromaDB v1.x persistente (sqlite + HNSW), via FastAPI/uvicorn                                               | `apps/chroma-server/server.py`, `chroma_db_finetune/` (~44 MB) |
| Coleção           | `report_texts` (chunks de relatório com `id_relatorio`, `caminho`)                                           | `chroma.service.ts:13`                                       |
| Cliente           | `chromadb` (JS) no NestJS                                                                                    | `db-backend`                                                 |
| LLM gerador       | **Não definido ainda** (template DOCX é preenchido por dados estruturados, geração textual ainda em aberto) | —                                                            |

Pontos relevantes para a decisão:

- Embedding **roda no processo Node**: bom para custo zero por token, ruim para
  cold-start e para throughput em batch (CPU, single-thread por chamada).
- O Chroma local depende de o servidor uvicorn estar de pé na mesma máquina —
  acoplamento operacional não trivial em produção.
- Modelo MPNet multilingual tem performance razoável em PT-BR, mas é de 2021;
  modelos mais novos (BGE-m3, e5-multilingual, OpenAI v3) superam em benchmarks
  recentes (MTEB pt-br/multi).

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

Premissas:

- Corpus médio: tomamos **100k chunks** como ponto central.
- Tamanho médio do chunk: **~400 tokens** (típico p/ laudos técnicos).
- Reindexação completa **2× ao ano** (mudança de modelo, ajuste de chunking).
- Cap de **8191 tokens por request** na API de embeddings v3 — bem acima do
  nosso tamanho de chunk, então é não-restritivo. Importa apenas para garantir
  que nenhum chunk extrapola.

| Modelo                              | US$ / 1M tok (Standard) | US$ / 1M tok (Batch −50%) | 100k chunks (40M tokens) | 500k chunks (200M tok) |
|-------------------------------------|-------------------------|---------------------------|--------------------------|------------------------|
| Xenova MPNet (local, CPU)           | $0 (compute)            | n/a                       | ~6–10 h CPU              | ~30–50 h CPU           |
| `text-embedding-3-small`            | **$0.020**              | **$0.010**                | **$0.80** (Batch: $0.40) | **$4.00** (Batch: $2.00) |
| `text-embedding-3-large`            | **$0.130**              | **$0.065**                | **$5.20** (Batch: $2.60) | **$26.00** (Batch: $13.00) |
| `text-embedding-ada-002` (legado)   | $0.100                  | $0.050                    | $4.00                    | $20.00                 |

> **Conclusão de custo de indexação**: irrelevante. Mesmo no pior cenário
> (re-embedding completo de 500k chunks com `large`, sem Batch), custa
> **US$ 26**. Com Batch API, **US$ 13**. Custo **não deve ser o critério de
> decisão** dessa camada.

> Re-indexação é caso típico de uso do Batch API (não precisa ser síncrona):
> sempre rodar via Batch para indexação em massa.

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
| Disco (100k chunks)           | 768 dim × 4 B = ~300 MB                        | 1536 dim → ~600 MB          |
| Disco (500k chunks)           | ~1.5 GB                                        | ~3 GB (ou 1 GB se truncar)  |

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

- **Golden set**: 50–100 pares `(pergunta, id_relatorio_esperado)` curados pelo
  time de domínio (engenheiros de laudo). Sem isso, nenhuma métrica é confiável.
- **Pool de chunks**: cópia da coleção `report_texts` atual.

### 7.2 Variantes a medir

| ID | Embedding                              | Dim  | Store          |
|----|----------------------------------------|------|----------------|
| V1 | Xenova MPNet (baseline)                | 768  | Chroma local   |
| V2 | `text-embedding-3-small` (dim=768)     | 768  | Chroma local   |
| V3 | `text-embedding-3-small` (dim=1536)    | 1536 | Chroma local   |
| V4 | `text-embedding-3-large` (dim=3072)    | 3072 | Chroma local   |
| V5 | BGE-m3 local *(opcional, controle)*    | 1024 | Chroma local   |

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

A criar em `apps/chroma-server/bench/`:

- `prepare.py` — gera as 5 coleções variantes a partir do corpus.
- `run-queries.ts` — executa o golden set em cada variante, salva CSV.
- `score.py` — calcula Recall/MRR/nDCG, exporta tabela e gráficos
  (`matplotlib`/`seaborn`) prontos pra apresentação.

Esforço estimado: **2–3 dias** para o script + ~1 dia para curar o golden set
com o domínio. Sem o golden set, qualquer comparação vira opinião.

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

## 9. Fontes / dados externos confirmados

Verificado em 2026-06-01:

- **Pricing OpenAI** (Standard / Batch −50%): `3-small` $0.020/$0.010,
  `3-large` $0.130/$0.065 por 1M tokens; `gpt-4o-mini` $0.15 in / $0.60 out;
  `gpt-4.1-mini` $0.40 in / $1.60 out; `gpt-4o` $2.50/$10; `gpt-4.1` $2/$8.
- **Cap de input** dos embeddings v3: 8191 tokens/request.
- **Performance OpenAI v3 (oficial)**: MTEB médio passou de 61.0% (ada-002)
  para 62.3% (`3-small`); MIRACL multilíngue 31.4% → 44.0%; redução de
  dimensão via parâmetro `dimensions` (Matryoshka representation learning)
  com perda mínima de qualidade.
- **Dim padrão**: `3-small` 1536 (truncável até 256), `3-large` 3072
  (truncável). `paraphrase-multilingual-mpnet-base-v2`: 768 dim, fixa.

Itens a confirmar **com o bench (§7)**, não no documento:

- Recall/MRR/nDCG concretos por variante no nosso corpus.
- Latência real do `chroma-server` atual sob carga.
- Distribuição de tokens por chunk (para validar premissa de 400 tok).

---

## 10. TL;DR para a apresentação

1. **Embedding não é o custo**: indexar 100k chunks na OpenAI custa < US$ 1.
   O LLM gerador é o item caro — decidir lá primeiro.
2. **Qualidade**: `text-embedding-3-small` tende a superar MPNet em PT-BR;
   provar no bench (§7) antes de migrar.
3. **Latência**: equivalente em pipeline RAG (LLM domina). Local perde em
   ingestão batch (CPU); OpenAI perde em cold start de rede.
4. **Stack proposta**: Chroma → mantém / `pgvector` no roadmap; embedding
   `text-embedding-3-small@768` com fallback Xenova feature-flagged; LLM
   `gpt-4o-mini` como ponto de partida.
5. **Pré-condição inegociável**: DPA + ZDR + mascaramento antes de mandar
   dado de laudo para fora.
6. **Próximo passo concreto**: curar golden set + rodar bench §7.

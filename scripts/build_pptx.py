"""
build_pptx.py — Refaz o deck reaproveitando o template Digital Labs.

Estratégia limpa (sem slides órfãos no zip):
  1. Carrega /tmp/template.pptx (12 slides com layouts distintos).
  2. Para cada slide final, modifica um slide do template in-place OU clona um
     slide do template (apenas 5 clones necessários).
  3. Reordena `sldIdLst` para a sequência final desejada.
  4. Salva em references/Apresentacao_RAG_2026-06-01.pptx.

Conteúdo em PT-BR formal acentuado, gramática revisada.
"""
from copy import deepcopy
from pathlib import Path

from pptx import Presentation

TEMPLATE = "/tmp/template.pptx"
OUT = Path(__file__).resolve().parent.parent / "references" / "Apresentacao_RAG_2026-06-01.pptx"

prs = Presentation(TEMPLATE)
TEMPLATE_SLIDES = list(prs.slides)
TOTAL = 17


# ---------- helpers ----------

def clone_slide(src_slide):
    """Clona um slide do template e o anexa ao fim da apresentação."""
    new_slide = prs.slides.add_slide(src_slide.slide_layout)
    for shp in list(new_slide.shapes):
        shp._element.getparent().remove(shp._element)
    for shp in src_slide.shapes:
        new_slide.shapes._spTree.append(deepcopy(shp._element))
    return new_slide


def find_shape(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    return None


def set_paragraphs(shape, lines):
    """Substitui o texto dos parágrafos preservando a formatação do primeiro
    run de cada parágrafo. Mantém a contagem original (excedentes esvaziados)."""
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    paras = list(tf.paragraphs)
    for i, p in enumerate(paras):
        if i < len(lines):
            new = lines[i]
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.text = new
        else:
            for r in p.runs:
                r.text = ""


def set_table_cells(shape, mapping):
    if shape.shape_type != 19:
        return
    tbl = shape.table
    for (r, c), text in mapping.items():
        cell = tbl.cell(r, c)
        tf = cell.text_frame
        paras = list(tf.paragraphs)
        if paras and paras[0].runs:
            paras[0].runs[0].text = text
            for run in paras[0].runs[1:]:
                run.text = ""
            for p in paras[1:]:
                for run in p.runs:
                    run.text = ""
        else:
            cell.text = text


def reorder_slides(prs, slides_in_order):
    """Reordena sldIdLst para refletir a ordem dos slides passados."""
    ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    sldIdLst = prs.slides._sldIdLst
    by_partname = {}
    for sldId in list(sldIdLst):
        rId = sldId.attrib[f"{ns}id"]
        part = prs.part.related_part(rId)
        by_partname[part.partname] = sldId
        sldIdLst.remove(sldId)
    for sl in slides_in_order:
        sldIdLst.append(by_partname[sl.part.partname])


# ---------- builders ----------

def b_cover(s):
    set_paragraphs(find_shape(s, "object 3"), ["ISQ BRASIL  /  NIT-DEV"])
    set_paragraphs(find_shape(s, "object 4"), ["JUNHO 2026"])
    set_paragraphs(find_shape(s, "object 5"), ["ANÁLISE TÉCNICA — SPRINT"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Stack de RAG para",
        "relatórios de inspeção.",
        "ChromaDB local versus OpenAI Embeddings + API. "
        "Levantamento técnico para definir embedder, vector store e LLM gerador, "
        "com pipeline de ingestão contínua para os novos laudos.",
    ])
    set_paragraphs(find_shape(s, "object 9"), ["ANÁLISE TÉCNICA  /  16 : 9"])


def b_roteiro(s):
    set_paragraphs(find_shape(s, "object 2"), ["ROTEIRO DA APRESENTAÇÃO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Da descoberta no corpus à recomendação de stack.",
    ])
    set_table_cells(find_shape(s, "object 5"), {
        (0, 0): "01\tContexto e descobertas críticas",
        (0, 2): "\n02",
        (0, 3): "Stack atual e bug detectado",
        (1, 0): "03\tCorpus real e ingestão contínua",
        (1, 2): "\n04",
        (1, 3): "Opções avaliadas, custos e latência",
        (2, 0): "05\tResultados reais do bench parcial",
        (2, 2): "\n06",
        (2, 3): "Stack proposta e próximos passos",
    })
    set_paragraphs(find_shape(s, "object 9"), [f"02 / {TOTAL}"])


def b_sumario(s):
    set_paragraphs(find_shape(s, "object 3"), [
        "SUMÁRIO EXECUTIVO",
        "",
        "",
        "O desafio é precisão semântica, não escala.",
        "Corpus pequeno (8.021 chunks), denso e técnico. "
        "Um bug de configuração no embedder já reduz a qualidade hoje. "
        "O custo de qualquer embedding é irrelevante. "
        "A decisão real está na qualidade do retrieval e na escolha do LLM gerador.",
    ])
    set_paragraphs(find_shape(s, "object 6"), [f"03 / {TOTAL}"])


def b_descobertas(s):
    set_paragraphs(find_shape(s, "object 2"), ["DESCOBERTAS CRÍTICAS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três achados que mudam o desenho",
        "da sprint.",
        "Inspecionei o chroma.sqlite3, o código do db-backend e a configuração da coleção. "
        "Cada achado abaixo impacta diretamente a comparação ChromaDB local versus OpenAI Embeddings.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "Bug no embedding"])
    set_paragraphs(find_shape(s, "object 11"), [
        "A indexação e a consulta usam modelos diferentes; o recall do retrieval atual "
        "está degradado de forma imprevisível.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "Corpus pequeno e denso",
        "8.021 chunks (78 laudos + 7.943 captions). "
        "O custo de qualquer embedding é irrelevante; o desafio é precisão semântica "
        "em jargão técnico.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Ingestão contínua",
        "O banco inicial será alimentado conforme novos laudos forem gerados. "
        "Esse requisito de arquitetura ainda não está desenhado.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"04 / {TOTAL}"])


def b_stack_atual(s):
    set_paragraphs(find_shape(s, "object 2"), ["STACK ATUAL"])
    set_paragraphs(find_shape(s, "object 3"), [
        "ChromaDB local e sentence-transformer fine-tunado.",
        "O backend NestJS consulta a coleção via cliente chromadb (JS). "
        "Os vetores foram gerados por um sentence-transformer fine-tunado internamente "
        "(projeto ml_wo), mas as consultas em produção usam Xenova/MPNet vanilla — "
        "origem do bug detectado.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["STACK  /  ml_wo"])
    set_paragraphs(find_shape(s, "object 9"), ["V 1"])
    set_paragraphs(find_shape(s, "object 11"), [
        "CAMADAS  ·  EMBEDDER  ·  VECTOR STORE  ·  CLIENTE  ·  LLM GERADOR",
    ])
    set_paragraphs(find_shape(s, "object 14"), [f"05 / {TOTAL}"])


def b_bug_detalhe(s):
    set_paragraphs(find_shape(s, "object 2"), ["BUG DETECTADO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "O índice e a consulta usam",
        "modelos diferentes.",
        "A coleção report_texts foi criada com um sentence-transformer fine-tunado "
        "pelo time, mas o serviço NestJS aplica Xenova/MPNet vanilla em cada consulta.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "Indexação"])
    set_paragraphs(find_shape(s, "object 11"), [
        "models/fine_tuned_report_model — sentence-transformer fine-tunado (768 dim). "
        "Ativo do ml_wo; não está versionado no repositório.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "Query",
        "Xenova/paraphrase-multilingual-mpnet-base-v2 — MPNet vanilla em ONNX no Node "
        "(768 dim). Aplicado a cada consulta de produção.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Consequência",
        "Os espaços vetoriais são incompatíveis. O recall do retrieval atual está abaixo "
        "do potencial real, e o efeito só será mensurável depois do bench.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"06 / {TOTAL}"])


def b_corpus_real(s):
    set_paragraphs(find_shape(s, "object 2"), ["CORPUS REAL"])
    set_paragraphs(find_shape(s, "object 3"), [
        "78 laudos e 7.943 captions",
        "compõem o corpus inicial.",
    ])
    set_paragraphs(find_shape(s, "object 7"), ["Coleção report_texts"])
    set_paragraphs(find_shape(s, "object 8"), [
        "78 chunks — uma seção por laudo.",
        "Cada chunk corresponde à seção “Discussão dos Resultados” de um relatório. "
        "Tamanho médio de 400 tokens. Todos do tipo Análise de Falha; "
        "cliente predominante PETROBRÁS.",
    ])
    set_paragraphs(find_shape(s, "object 12"), ["Coleção metallography_captions"])
    set_paragraphs(find_shape(s, "object 13"), [
        "7.943 captions",
        "de imagens de metalografia.",
        "Aproximadamente cem captions por laudo. Suporta consultas semânticas quando "
        "a resposta está na imagem, não no texto principal do relatório.",
    ])
    set_paragraphs(find_shape(s, "object 16"), [f"07 / {TOTAL}"])


def b_ingestao(s):
    set_paragraphs(find_shape(s, "object 2"), ["INGESTÃO CONTÍNUA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Cada novo laudo deve ficar disponível para busca em até um minuto.",
    ])
    set_paragraphs(find_shape(s, "object 5"), ["01"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Gerar",
        "O endpoint report-generate finaliza o DOCX e emite um evento de conclusão.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["02"])
    set_paragraphs(find_shape(s, "object 9"), [
        "Enfileirar",
        "A mensagem entra na fila (pg-boss sobre o Postgres já existente).",
    ])
    set_paragraphs(find_shape(s, "object 11"), ["03"])
    set_paragraphs(find_shape(s, "object 12"), [
        "Indexar",
        "O worker extrai texto, gera embeddings e faz upsert idempotente no Chroma.",
    ])
    set_paragraphs(find_shape(s, "object 14"), ["04"])
    set_paragraphs(find_shape(s, "object 15"), [
        "Servir",
        "A coleção é atualizada; a busca semântica já enxerga o novo laudo.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [f"08 / {TOTAL}"])


def b_opcoes(s):
    set_paragraphs(find_shape(s, "object 2"), ["OPÇÕES AVALIADAS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três caminhos para a stack,",
        "comparados no mesmo bench.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Opção A", "Status quo coerente",
        "Reindexar com Xenova/MPNet vanilla e manter o Chroma local. "
        "Zero dependência externa; corrige o bug atual sem migrar de provedor.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Opção B", "OpenAI Embeddings",
        "Trocar o embedder para text-embedding-3-small (dimensions=768) via API. "
        "O Chroma continua local; permite A/B sem refazer schema.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Opção C", "Híbrida",
        "Embedder OpenAI e pgvector sobre o Postgres existente. "
        "Elimina o chroma-server Python; entra no roadmap com a ingestão contínua.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"09 / {TOTAL}"])


def b_custos(s):
    set_paragraphs(find_shape(s, "object 2"), ["CUSTOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Embedding não é onde mora o custo.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Item 01", "Indexação",
        "Reindexar todo o corpus atual via text-embedding-3-small custa US$ 0,06 em "
        "Standard ou US$ 0,03 em Batch. Reindex anual é financeiramente irrelevante.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Item 02", "Consulta",
        "Cada consulta custa cerca de US$ 0,0000006. Mesmo no cenário de cem mil "
        "consultas por mês, o custo total fica em US$ 0,06.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Item 03", "LLM gerador",
        "gpt-4o-mini custa US$ 0,0008 por resposta (três mil tokens de entrada e "
        "quinhentos de saída). Dez mil respostas por mês: US$ 8. Aqui mora o custo real.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"10 / {TOTAL}"])


def b_latencia(s):
    set_paragraphs(find_shape(s, "object 2"), ["LATÊNCIA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Store medido em produção,",
        "embedder estimado.",
    ])
    set_paragraphs(find_shape(s, "object 7"), ["Estimativa"])
    set_paragraphs(find_shape(s, "object 8"), [
        "Embedder e LLM dominam o pipeline.",
        "Embedding de uma query: 80 a 250 ms (local) ou 60 a 180 ms (OpenAI). "
        "O pipeline RAG completo é dominado pelo LLM gerador (1,5 a 4 segundos).",
    ])
    set_paragraphs(find_shape(s, "object 12"), ["Medido em 2026-06-01"])
    set_paragraphs(find_shape(s, "object 13"), [
        "Chroma HNSW",
        "não é gargalo nesta escala.",
        "p50 de 4,58 ms em 78 documentos e 5,08 ms em 7.943 documentos. "
        "p99 de 5,99 ms e 6,97 ms, respectivamente. Passar de 78 para cerca de oito "
        "mil documentos adiciona apenas meio milissegundo no p99.",
    ])
    set_paragraphs(find_shape(s, "object 16"), [f"11 / {TOTAL}"])


def b_tfidf(s):
    set_paragraphs(find_shape(s, "object 2"), [
        "PROVA E EVIDÊNCIA — BENCH 2026-06-01",
        "Recall@5 = 0,671 no baseline TF-IDF.",
        "234 consultas sintéticas contra 78 chunks. O TF-IDF acerta 100 % das "
        "consultas que repetem o texto do chunk, mas apenas 12 % das consultas por "
        "número de relatório.",
        "Esse intervalo é exatamente o ganho que o retrieval semântico precisa entregar.",
    ])
    set_paragraphs(find_shape(s, "object 5"), [f"12 / {TOTAL}"])


def b_stack_proposta(s):
    set_paragraphs(find_shape(s, "object 2"), ["STACK PROPOSTA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três decisões para encerrar",
        "a sprint.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Decisão 1", "Embedder",
        "text-embedding-3-small com dimensions=768. Mantém compatibilidade dimensional, "
        "permite A/B sem refazer schema e preserva o Xenova como fallback.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Decisão 2", "Vector store",
        "Chroma local no curto prazo. O pgvector sobre o Postgres existente entra no "
        "roadmap quando a ingestão contínua for implementada.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Decisão 3", "LLM gerador",
        "gpt-4o-mini como baseline (US$ 0,0008 por resposta). Subir para gpt-4.1-mini "
        "somente com sinal claro de regressão de qualidade.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"13 / {TOTAL}"])


def b_criterios(s):
    set_paragraphs(find_shape(s, "object 2"), ["CRITÉRIOS DE DECISÃO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "“Trocar para OpenAI somente se o bench mostrar Recall@5 ≥ +5 pp, MRR ≥ +0,05 "
        "e p95 ponta a ponta ≤ 400 ms — com DPA assinado, ZDR habilitado e "
        "mascaramento de PII.”",
        "CRITÉRIOS OBJETIVOS DE GO / NO-GO PARA A MIGRAÇÃO",
    ])
    set_paragraphs(find_shape(s, "object 6"), [f"14 / {TOTAL}"])


def b_restricao(s):
    set_paragraphs(find_shape(s, "object 2"), ["BLOQUEIO IDENTIFICADO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "O ambiente atual impede",
        "o bench neural.",
        "A política de rede do sandbox bloqueia os domínios huggingface.co e "
        "api.openai.com. O bench parcial (TF-IDF e latência do Chroma) foi entregue; "
        "o bench neural depende de liberação ou de uma estação de trabalho com rede aberta.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "huggingface.co"])
    set_paragraphs(find_shape(s, "object 11"), [
        "Necessário para baixar MPNet vanilla, BGE-m3 e demais modelos open source. "
        "Uma liberação pontual basta — o modelo fica em cache local.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "api.openai.com",
        "Necessário para embeddings v3 e para o LLM gerador. "
        "Liberação permanente em produção, restrita por allowlist.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Plano B imediato",
        "Rodar o bench numa estação pessoal com rede aberta. "
        "Os scripts em apps/chroma-server/bench são reprodutíveis em cerca de três horas.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"15 / {TOTAL}"])


def b_proximos_passos(s):
    set_paragraphs(find_shape(s, "object 2"), ["PRÓXIMOS PASSOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Quatro frentes em paralelo até a próxima revisão.",
    ])
    set_paragraphs(find_shape(s, "object 5"), ["01"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Liberar",
        "Abrir chamado para a TI liberar huggingface.co e api.openai.com.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["02"])
    set_paragraphs(find_shape(s, "object 9"), [
        "Rodar",
        "Executar prepare.py, run-queries e score.py com a chave da OpenAI.",
    ])
    set_paragraphs(find_shape(s, "object 11"), ["03"])
    set_paragraphs(find_shape(s, "object 12"), [
        "Decidir",
        "Definir o destino do fine_tuned_report_model: manter, descontinuar ou versionar.",
    ])
    set_paragraphs(find_shape(s, "object 14"), ["04"])
    set_paragraphs(find_shape(s, "object 15"), [
        "Implantar",
        "Construir o pipeline de ingestão contínua sobre o Postgres existente.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [f"16 / {TOTAL}"])


def b_proxima_decisao(s):
    set_paragraphs(find_shape(s, "object 3"), ["NIT-DEV  /  DROPEKO"])
    set_paragraphs(find_shape(s, "object 4"), ["ISQ DIGITAL LABS"])
    set_paragraphs(find_shape(s, "object 5"), [
        "PRÓXIMA DECISÃO",
        "",
        "",
        "Aprovar a liberação de rede e o gate de migração.",
        "Com a TI liberada, completamos V1a, V1b, V2, V3 e V4 em uma tarde. "
        "Sem isso, a decisão de stack fica travada no piso do TF-IDF.",
    ])
    set_paragraphs(find_shape(s, "object 8"), [f"17 / {TOTAL}"])


# ---------- plan: 17 slides, sem órfãos ----------
# (mode, src_template_idx, builder)
PLAN = [
    ("inplace", 0, b_cover),
    ("inplace", 1, b_roteiro),
    ("inplace", 2, b_sumario),
    ("inplace", 3, b_descobertas),
    ("inplace", 4, b_stack_atual),
    ("clone",   3, b_bug_detalhe),
    ("inplace", 9, b_corpus_real),
    ("inplace", 10, b_ingestao),
    ("inplace", 5, b_opcoes),
    ("inplace", 7, b_custos),
    ("clone",   9, b_latencia),
    ("inplace", 8, b_tfidf),
    ("clone",   5, b_stack_proposta),
    ("inplace", 6, b_criterios),
    ("clone",   3, b_restricao),
    ("clone",   10, b_proximos_passos),
    ("inplace", 11, b_proxima_decisao),
]

ordered_slides = []
for mode, idx, builder in PLAN:
    sl = TEMPLATE_SLIDES[idx] if mode == "inplace" else clone_slide(TEMPLATE_SLIDES[idx])
    builder(sl)
    ordered_slides.append(sl)

reorder_slides(prs, ordered_slides)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"deck gerado: {OUT}  ({len(list(prs.slides))} slides)")

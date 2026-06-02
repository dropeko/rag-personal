"""
build_pptx.py — Deck Digital Labs, 16 slides, com clonagem que preserva imagens.

Corrige bug crítico: a clonagem anterior copiava só o XML; rIds de imagens
ficavam apontando para relacionamentos inexistentes no slide novo, e as imagens
do template (objetos de fundo dos cards) sumiam nos clones (slides 6, 13, 15).
Agora copio também as relações e remapeio os rIds dentro do XML clonado.
"""
from copy import deepcopy
from pathlib import Path

from pptx import Presentation

TEMPLATE = "/tmp/template.pptx"
OUT = Path(__file__).resolve().parent.parent / "references" / "Apresentacao_RAG_2026-06-01.pptx"

prs = Presentation(TEMPLATE)
TEMPLATE_SLIDES = list(prs.slides)
TOTAL = 16

R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def clone_slide(src_slide):
    """Clona slide preservando imagens e demais partes referenciadas por rId."""
    new_slide = prs.slides.add_slide(src_slide.slide_layout)

    # Remove shapes default do layout
    for shp in list(new_slide.shapes):
        shp._element.getparent().remove(shp._element)

    # Copia relações (imagens, themeOverride, etc.) e monta rId_map
    rId_map = {}
    for rel in src_slide.part.rels.values():
        if "slideLayout" in rel.reltype:
            continue  # layout já foi linkado pelo add_slide
        new_rId = new_slide.part.relate_to(rel.target_part, rel.reltype)
        rId_map[rel.rId] = new_rId

    # Copia shapes (XML) reescrevendo rIds para os novos
    for shp in src_slide.shapes:
        new_el = deepcopy(shp._element)
        for node in new_el.iter():
            for attr in (f"{R_NS}embed", f"{R_NS}link", f"{R_NS}id"):
                val = node.get(attr)
                if val and val in rId_map:
                    node.set(attr, rId_map[val])
        new_slide.shapes._spTree.append(new_el)

    return new_slide


def find_shape(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    return None


def set_paragraphs(shape, lines):
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
                if new:
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
    sldIdLst = prs.slides._sldIdLst
    by_partname = {}
    for sldId in list(sldIdLst):
        rId = sldId.attrib[f"{R_NS}id"]
        part = prs.part.related_part(rId)
        by_partname[part.partname] = sldId
        sldIdLst.remove(sldId)
    for sl in slides_in_order:
        sldIdLst.append(by_partname[sl.part.partname])


# ============================================================================
# Builders — texto enxuto + contexto explicativo
# ============================================================================

def b_cover(s):
    set_paragraphs(find_shape(s, "object 3"), ["ISQ BRASIL  /  NIT-DEV"])
    set_paragraphs(find_shape(s, "object 4"), ["JUN 2026"])
    set_paragraphs(find_shape(s, "object 5"), ["ANÁLISE TÉCNICA — SPRINT"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Stack de RAG",
        "para inspeção.",
        "Comparativo ChromaDB local vs. OpenAI Embeddings + API. "
        "Embedder, vector store, LLM e ingestão contínua.",
    ])
    set_paragraphs(find_shape(s, "object 9"), ["ANÁLISE  /  16 : 9"])


def b_roteiro(s):
    set_paragraphs(find_shape(s, "object 2"), ["ROTEIRO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Do corpus à recomendação.",
    ])
    set_table_cells(find_shape(s, "object 5"), {
        (0, 0): "01\tContexto e descobertas",
        (0, 2): "\n02",
        (0, 3): "Stack atual e bug detectado",
        (1, 0): "03\tCorpus e ingestão contínua",
        (1, 2): "\n04",
        (1, 3): "Custos e latência",
        (2, 0): "05\tBench parcial e proposta",
        (2, 2): "\n06",
        (2, 3): "Critérios e próximos passos",
    })
    set_paragraphs(find_shape(s, "object 9"), [f"02 / {TOTAL}"])


def b_sumario(s):
    set_paragraphs(find_shape(s, "object 3"), [
        "SUMÁRIO EXECUTIVO",
        "",
        "",
        "Precisão, não escala.",
        # 130 chars — 3 linhas em 21pt
        "Corpus de 8.021 chunks: pequeno e técnico. Um bug entre indexação "
        "e consulta já degrada o retrieval hoje. O embedding custa centavos.",
    ])
    set_paragraphs(find_shape(s, "object 6"), [f"03 / {TOTAL}"])


def b_descobertas(s):
    set_paragraphs(find_shape(s, "object 2"), ["ACHADOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três achados que",
        "mudam a sprint.",
        "Levantados direto no chroma.sqlite3 e no código do db-backend.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "Mismatch"])
    set_paragraphs(find_shape(s, "object 11"), [
        # 70 chars — cabe no body estreito
        "Indexação e consulta usam modelos diferentes; o recall sai degradado.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "Corpus pequeno",
        # 95 chars
        "78 laudos completos e 7.943 captions de metalografia. "
        "Chunk médio de 400 tokens, denso e técnico.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Ingestão contínua",
        # 90 chars
        "Novos laudos precisam ser indexados de forma automática. "
        "O pipeline ainda não está desenhado.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"04 / {TOTAL}"])


def b_stack_atual(s):
    set_paragraphs(find_shape(s, "object 2"), ["STACK ATUAL"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Chroma + fine-tunado.",   # 21 chars
        # 145 chars
        "Backend NestJS consulta o Chroma via cliente JS. Os vetores foram indexados "
        "com modelo fine-tunado interno (ml_wo); as consultas em produção usam "
        "MPNet vanilla — origem do bug.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["STACK / ml_wo"])
    set_paragraphs(find_shape(s, "object 9"), ["V 1"])
    set_paragraphs(find_shape(s, "object 11"), [
        "CAMADAS  ·  EMBEDDER  ·  STORE  ·  CLIENTE  ·  LLM",
    ])
    set_paragraphs(find_shape(s, "object 14"), [f"05 / {TOTAL}"])


def b_bug_detalhe(s):
    set_paragraphs(find_shape(s, "object 2"), ["MISMATCH"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Índice e consulta",
        "usam modelos diferentes.",
        "O resultado é simples: vetores indexados e vetores de consulta vivem em espaços distintos.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "Indexação"])
    set_paragraphs(find_shape(s, "object 11"), [
        # 70 chars — body estreito
        "fine_tuned_report_model — 768 dim, ativo do ml_wo, fora do repositório.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "Consulta",
        # 95 chars
        "Xenova/MPNet vanilla em ONNX no Node, 768 dim. "
        "Aplicado a cada consulta de produção.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Consequência",
        # 110 chars
        "O recall do retrieval atual está abaixo do potencial. "
        "A magnitude do impacto só será medida no bench neural.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"06 / {TOTAL}"])


def b_corpus_real(s):
    set_paragraphs(find_shape(s, "object 2"), ["CORPUS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "78 laudos",
        "+ 7.943 captions.",
    ])
    set_paragraphs(find_shape(s, "object 7"), ["report_texts"])
    set_paragraphs(find_shape(s, "object 8"), [
        "78 chunks — um por laudo.",
        # 125 chars
        "Cada chunk é a seção “Discussão dos Resultados” do laudo. "
        "Em média 400 tokens; 100 % são Análises de Falha PETROBRÁS.",
    ])
    set_paragraphs(find_shape(s, "object 12"), ["captions"])
    set_paragraphs(find_shape(s, "object 13"), [
        "7.943 captions",
        "de metalografia.",
        # 110 chars
        "Cerca de cem captions por laudo. Atendem consultas em que a "
        "resposta está na imagem, não no texto principal.",
    ])
    set_paragraphs(find_shape(s, "object 16"), [f"07 / {TOTAL}"])


def b_ingestao(s):
    set_paragraphs(find_shape(s, "object 2"), ["INGESTÃO CONTÍNUA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Novo laudo buscável em até um minuto.",
    ])
    set_paragraphs(find_shape(s, "object 5"), ["01"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Gerar",
        "report-generate fecha o DOCX e emite evento.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["02"])
    set_paragraphs(find_shape(s, "object 9"), [
        "Enfileirar",
        "Fila no Postgres existente (pg-boss).",
    ])
    set_paragraphs(find_shape(s, "object 11"), ["03"])
    set_paragraphs(find_shape(s, "object 12"), [
        "Indexar",
        "Worker embeda e faz upsert idempotente.",
    ])
    set_paragraphs(find_shape(s, "object 14"), ["04"])
    set_paragraphs(find_shape(s, "object 15"), [
        "Servir",
        "Coleção atualizada; busca enxerga o laudo.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [f"08 / {TOTAL}"])


def b_opcoes(s):
    set_paragraphs(find_shape(s, "object 2"), ["OPÇÕES"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três caminhos,",
        "mesmo bench.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Opção A", "Status quo coerente",
        # 95 chars
        "Reindexar com MPNet vanilla. Corrige o bug, mantém o Chroma local, "
        "sem dependência externa.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Opção B", "OpenAI Embeddings",
        # 85 chars
        "text-embedding-3-small @768 via API. A/B sem refazer schema; "
        "ganho de qualidade.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Opção C", "Híbrida",
        # 90 chars
        "OpenAI + pgvector no Postgres existente. "
        "Elimina o chroma-server Python da operação.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"09 / {TOTAL}"])


def b_custos(s):
    set_paragraphs(find_shape(s, "object 2"), ["CUSTOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Embedding ≠",
        "custo real.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Item 01", "Indexação",
        # 80 chars
        "Reindex completo do corpus: US$ 0,06 em Standard ou US$ 0,03 em Batch.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Item 02", "Consulta",
        # 75 chars
        "Cerca de US$ 0,0000006 por chamada. 100 mil consultas/mês: US$ 0,06.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Item 03", "LLM gpt-4o-mini",
        # 95 chars
        "US$ 0,0008 por resposta (3 k entrada + 500 saída). "
        "10 mil/mês: US$ 8. O custo real mora aqui.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"10 / {TOTAL}"])


def b_latencia(s):
    set_paragraphs(find_shape(s, "object 2"), ["LATÊNCIA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Embedder estimado;",
        "store medido.",
    ])
    set_paragraphs(find_shape(s, "object 7"), ["Estimativa"])
    set_paragraphs(find_shape(s, "object 8"), [
        "Embedder e LLM dominam.",
        # 110 chars
        "Embedding de 1 query: 80–250 ms local ou 60–180 ms via OpenAI. "
        "LLM gpt-4o-mini: 1,5–4 s por resposta.",
    ])
    set_paragraphs(find_shape(s, "object 12"), ["Bench 2026-06"])
    set_paragraphs(find_shape(s, "object 13"), [
        "Chroma HNSW",
        "não é gargalo.",
        # 100 chars
        "p50: 4,58 ms (78 docs) e 5,08 ms (7.943 docs). "
        "p99: 5,99 ms e 6,97 ms, respectivamente.",
    ])
    set_paragraphs(find_shape(s, "object 16"), [f"11 / {TOTAL}"])


def b_tfidf(s):
    set_paragraphs(find_shape(s, "object 2"), [
        "BENCH — 2026-06-01",
        "67 %",
        # 55 chars
        "Recall@5 do baseline TF-IDF — o piso a superar.",
        "234 consultas sintéticas contra 78 chunks.",
    ])
    set_paragraphs(find_shape(s, "object 5"), [f"12 / {TOTAL}"])


def b_stack_proposta(s):
    set_paragraphs(find_shape(s, "object 2"), ["PROPOSTA"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Três decisões",
        "para a stack.",
    ])
    set_paragraphs(find_shape(s, "object 10"), [
        "Decisão 1", "Embedder",
        # 90 chars
        "text-embedding-3-small @768 dim. Compatível com a coleção atual; "
        "Xenova como fallback.",
    ])
    set_paragraphs(find_shape(s, "object 17"), [
        "Decisão 2", "Vector store",
        # 90 chars
        "Chroma local segue no curto prazo. pgvector no Postgres existente "
        "entra no roadmap.",
    ])
    set_paragraphs(find_shape(s, "object 24"), [
        "Decisão 3", "LLM gerador",
        # 90 chars
        "gpt-4o-mini como baseline. Subir para gpt-4.1-mini somente com "
        "sinal de regressão.",
    ])
    set_paragraphs(find_shape(s, "object 27"), [f"13 / {TOTAL}"])


def b_criterios(s):
    set_paragraphs(find_shape(s, "object 2"), ["CRITÉRIOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        # 80 chars 52.5pt
        "“Migrar para OpenAI somente se Recall@5 ≥ +5 pp, "
        "MRR ≥ +0,05 e p95 ≤ 400 ms.”",
        "DPA  ·  ZDR  ·  MASCARAMENTO DE PII COMO PRÉ-CONDIÇÕES",
    ])
    set_paragraphs(find_shape(s, "object 6"), [f"14 / {TOTAL}"])


def b_restricao(s):
    set_paragraphs(find_shape(s, "object 2"), ["BLOQUEIO"])
    set_paragraphs(find_shape(s, "object 3"), [
        "A TI ainda não",
        "liberou a rede.",
        "Bench parcial entregue; bench neural depende de liberação.",
        "",
    ])
    set_paragraphs(find_shape(s, "object 10"), ["01", "huggingface.co"])
    set_paragraphs(find_shape(s, "object 11"), [
        # 70 chars
        "Necessário para baixar MPNet, BGE-m3 e demais open source.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [
        "02", "api.openai.com",
        # 95 chars
        "Necessário para embeddings v3 e para o LLM gerador. "
        "Liberação permanente com allowlist.",
    ])
    set_paragraphs(find_shape(s, "object 25"), [
        "03", "Plano B",
        # 95 chars
        "Rodar o bench numa estação pessoal com rede aberta. "
        "Scripts reproduzíveis em três horas.",
    ])
    set_paragraphs(find_shape(s, "object 28"), [f"15 / {TOTAL}"])


def b_proximos_passos(s):
    set_paragraphs(find_shape(s, "object 2"), ["PRÓXIMOS PASSOS"])
    set_paragraphs(find_shape(s, "object 3"), [
        "Quatro frentes em paralelo.",
    ])
    set_paragraphs(find_shape(s, "object 5"), ["01"])
    set_paragraphs(find_shape(s, "object 6"), [
        "Liberar",
        "Chamado TI: huggingface.co + api.openai.com.",
    ])
    set_paragraphs(find_shape(s, "object 8"), ["02"])
    set_paragraphs(find_shape(s, "object 9"), [
        "Rodar",
        "prepare.py + run-queries + score.py com chave OpenAI.",
    ])
    set_paragraphs(find_shape(s, "object 11"), ["03"])
    set_paragraphs(find_shape(s, "object 12"), [
        "Decidir",
        "Destino do fine_tuned_report_model.",
    ])
    set_paragraphs(find_shape(s, "object 14"), ["04"])
    set_paragraphs(find_shape(s, "object 15"), [
        "Implantar",
        "Pipeline de ingestão sobre o Postgres existente.",
    ])
    set_paragraphs(find_shape(s, "object 18"), [f"16 / {TOTAL}"])


# Plano de 16 slides (slide de fechamento removido)
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
]

ordered_slides = []
for mode, idx, builder in PLAN:
    sl = TEMPLATE_SLIDES[idx] if mode == "inplace" else clone_slide(TEMPLATE_SLIDES[idx])
    builder(sl)
    ordered_slides.append(sl)

# Lista os 17 slides originais — remove os que não usamos
used_partnames = {sl.part.partname for sl in ordered_slides}
sldIdLst = prs.slides._sldIdLst
for sldId in list(sldIdLst):
    rId = sldId.attrib[f"{R_NS}id"]
    part = prs.part.related_part(rId)
    if part.partname not in used_partnames:
        sldIdLst.remove(sldId)
        prs.part.drop_rel(rId)

reorder_slides(prs, ordered_slides)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"deck gerado: {OUT}  ({len(list(prs.slides))} slides)")

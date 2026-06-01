"""
build_pptx.py — Gera o deck da review da sprint a partir das informações
levantadas e dos números reais medidos.

Saída: references/Apresentacao_RAG_2026-06-01.pptx
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = ROOT / "apps" / "chroma-server" / "bench" / "reports-offline"
OUT_PATH = ROOT / "references" / "Apresentacao_RAG_2026-06-01.pptx"

# Paleta sóbria
NAVY = RGBColor(0x0F, 0x2A, 0x4A)
ACCENT = RGBColor(0xC8, 0x4A, 0x1E)  # laranja queimado p/ destaque
TEXT = RGBColor(0x23, 0x2A, 0x33)
MUTED = RGBColor(0x6C, 0x73, 0x7D)
BG_LIGHT = RGBColor(0xF5, 0xF1, 0xEA)
GOOD = RGBColor(0x2A, 0x6E, 0x39)
WARN = RGBColor(0xB0, 0x46, 0x16)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height

BLANK = prs.slide_layouts[6]


# ---------- helpers ----------

def add_slide():
    return prs.slides.add_slide(BLANK)


def add_rect(slide, left, top, width, height, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
    return sh


def add_text(slide, left, top, width, height, text, *,
             size=18, bold=False, color=TEXT, align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    p.text = ""
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = "Calibri"
    return tb


def add_bullets(slide, left, top, width, height, items, *,
                size=16, color=TEXT, bullet_color=ACCENT, line_spacing=1.25):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(6)
        p.line_spacing = line_spacing
        # bullet char
        rb = p.add_run()
        rb.text = "▸  "
        rb.font.size = Pt(size)
        rb.font.bold = True
        rb.font.color.rgb = bullet_color
        rb.font.name = "Calibri"
        # corpo
        rt = p.add_run()
        rt.text = item
        rt.font.size = Pt(size)
        rt.font.color.rgb = color
        rt.font.name = "Calibri"
    return tb


def header(slide, title, kicker=None):
    # Faixa lateral esquerda
    add_rect(slide, Emu(0), Emu(0), Inches(0.25), SH, NAVY)
    if kicker:
        add_text(slide, Inches(0.55), Inches(0.30), Inches(12), Inches(0.35),
                 kicker.upper(), size=11, bold=True, color=ACCENT)
    add_text(slide, Inches(0.55), Inches(0.55), Inches(12), Inches(0.7),
             title, size=28, bold=True, color=NAVY)
    # Linha fina
    add_rect(slide, Inches(0.55), Inches(1.25), Inches(12.25), Emu(20000), MUTED)


def footer(slide, num, total, label="Análise técnica — Stack RAG"):
    add_text(slide, Inches(0.55), Inches(7.05), Inches(6), Inches(0.35),
             label, size=9, color=MUTED, italic=True)
    add_text(slide, Inches(12.0), Inches(7.05), Inches(1.2), Inches(0.35),
             f"{num} / {total}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def add_table(slide, left, top, width, height, data, *,
              header_fill=NAVY, header_text=RGBColor(0xFF, 0xFF, 0xFF),
              body_size=12, header_size=12, first_col_bold=False,
              col_widths=None):
    rows = len(data)
    cols = len(data[0])
    tbl_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    tbl = tbl_shape.table
    if col_widths:
        total = sum(col_widths)
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(width * w / total))
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.add_run()
            run.text = str(val)
            run.font.name = "Calibri"
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
                run.font.size = Pt(header_size)
                run.font.bold = True
                run.font.color.rgb = header_text
            else:
                run.font.size = Pt(body_size)
                run.font.color.rgb = TEXT
                if first_col_bold and c == 0:
                    run.font.bold = True
                # zebra
                if r % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = BG_LIGHT
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return tbl


def add_callout(slide, left, top, width, height, kicker, body, *,
                fill=BG_LIGHT, accent=ACCENT):
    add_rect(slide, left, top, width, height, fill)
    add_rect(slide, left, top, Emu(int(Inches(0.08))), height, accent)
    add_text(slide, left + Inches(0.25), top + Inches(0.10), width - Inches(0.35),
             Inches(0.35), kicker.upper(), size=10, bold=True, color=accent)
    add_text(slide, left + Inches(0.25), top + Inches(0.40), width - Inches(0.35),
             height - Inches(0.50), body, size=14, color=TEXT)


# ---------- slides ----------

SLIDES = []


def slide_capa():
    s = add_slide()
    add_rect(s, Emu(0), Emu(0), SW, SH, NAVY)
    add_rect(s, Emu(0), Inches(6.5), SW, Inches(1.0), ACCENT)
    add_text(s, Inches(0.7), Inches(2.0), Inches(12), Inches(0.5),
             "SPRINT — ANÁLISE TÉCNICA", size=14, bold=True,
             color=RGBColor(0xF0, 0xC9, 0xA8))
    add_text(s, Inches(0.7), Inches(2.5), Inches(12), Inches(1.5),
             "ChromaDB local vs OpenAI Embeddings + API",
             size=42, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    add_text(s, Inches(0.7), Inches(4.1), Inches(12), Inches(0.7),
             "Stack de RAG para geração de relatórios técnicos de inspeção industrial",
             size=20, color=RGBColor(0xE0, 0xDE, 0xD0), italic=True)
    add_text(s, Inches(0.7), Inches(5.2), Inches(12), Inches(0.5),
             "ISQ Brasil — NIT-Dev",
             size=14, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    add_text(s, Inches(0.7), Inches(5.55), Inches(12), Inches(0.4),
             "Sprint encerrada em 2026-06-01",
             size=12, color=RGBColor(0xE0, 0xDE, 0xD0))


SLIDES.append(slide_capa)


def slide_agenda():
    def _():
        s = add_slide()
        header(s, "Roteiro da apresentação")
        items = [
            "1. Contexto, escopo e restrições da sprint",
            "2. Stack atual (\"ml_wo\") e mapa do código",
            "3. Corpus real — descobertas ao inspecionar o sqlite",
            "4. Bug detectado: mismatch entre indexação e query",
            "5. Ingestão contínua como requisito novo",
            "6. Opções de stack avaliadas (A, B, C)",
            "7. Custos — embedding, query e LLM gerador",
            "8. Latência — estimativa e medição real",
            "9. Resultados reais do bench (Chroma HNSW + TF-IDF baseline)",
            "10. Onde o neural deve ganhar — breakdown por tipo de query",
            "11. Proposta de stack, critérios Go/No-Go e riscos",
            "12. Restrição de ambiente, TL;DR e próximos passos",
        ]
        add_bullets(s, Inches(0.8), Inches(1.6), Inches(11.5), Inches(5.0),
                    items, size=18, line_spacing=1.2)
    return _


SLIDES.append(slide_agenda())


def slide_contexto():
    def _():
        s = add_slide()
        header(s, "Contexto e escopo", kicker="1. Contexto")
        add_bullets(s, Inches(0.6), Inches(1.6), Inches(12), Inches(2.2), [
            "Domínio: relatórios técnicos de inspeção industrial — Análise de Falhas em equipamentos PETROBRÁS (válvulas, permutadores, vasos, cilindros).",
            "Demanda da sprint: comparar ChromaDB local (abordagem ml_wo) vs OpenAI Embeddings + API. Documentar custos, latência e viabilidade. Definir stack.",
            "Escopo expandido durante a análise: RAG ponta-a-ponta (embedding + vector store + LLM gerador) + pipeline de ingestão contínua.",
        ], size=15)
        # Caixas de restrições
        add_text(s, Inches(0.6), Inches(4.2), Inches(6), Inches(0.4),
                 "Restrições confirmadas com o time", size=14, bold=True, color=NAVY)
        add_callout(s, Inches(0.6), Inches(4.6), Inches(6.0), Inches(1.0),
                    "Volume", "Corpus médio (10k–500k chunks na projeção).")
        add_callout(s, Inches(0.6), Inches(5.7), Inches(6.0), Inches(1.0),
                    "Privacidade", "Dados de cliente/laudo. OpenAI permitido com DPA + ZDR + mascaramento.")
        add_callout(s, Inches(6.9), Inches(4.6), Inches(6.0), Inches(1.0),
                    "LLM", "Inclui escolha do LLM gerador.")
        add_callout(s, Inches(6.9), Inches(5.7), Inches(6.0), Inches(1.0),
                    "Time de domínio", "NÃO participa da curadoria de bench em paralelo.")
    return _


SLIDES.append(slide_contexto())


def slide_stack_atual():
    def _():
        s = add_slide()
        header(s, "Stack atual (\"ml_wo\")", kicker="2. Stack atual")
        data = [
            ["Camada", "Implementação", "Onde"],
            ["Embedding (query)", "Xenova/paraphrase-multilingual-mpnet-base-v2 (vanilla, ONNX em Node)",
             "chroma.service.ts:97"],
            ["Embedding (index)", "models/fine_tuned_report_model (sentence-transformer fine-tunado)",
             "metadata do chroma.sqlite3"],
            ["Vector store", "ChromaDB v1.x persistente (FastAPI/uvicorn)",
             "apps/chroma-server/server.py"],
            ["Cliente", "chromadb (JS) no NestJS", "apps/db-backend"],
            ["LLM gerador", "Não definido — apenas template DOCX preenchido por estrutura", "—"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(3.6),
                  data, body_size=12, col_widths=[2.5, 6.5, 3.0])
        add_callout(s, Inches(0.6), Inches(5.6), Inches(12.1), Inches(1.3),
                    "Pontos a observar",
                    "• Embedding roda no processo Node — cold start ~2–5s na 1ª query, ruim p/ throughput em batch.\n"
                    "• Chroma local depende de uvicorn separado — acoplamento operacional não trivial.\n"
                    "• MPNet vanilla é de 2021 — modelos mais novos (v3, BGE-m3, e5) superam em benchmarks recentes.")
    return _


SLIDES.append(slide_stack_atual())


def slide_corpus():
    def _():
        s = add_slide()
        header(s, "Corpus real — inspeção direta no chroma.sqlite3", kicker="3. Descoberta")
        # Tabela de volume
        data = [
            ["Coleção", "Chunks", "Conteúdo", "Por relatório"],
            ["report_texts", "78", "Seção \"DISCUSSÃO DOS RESULTADOS\"", "1 chunk / laudo"],
            ["metallography_captions", "7.943", "Captions de imagens de metalografia", "~100 / laudo"],
            ["Total", "8.021", "—", "—"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(2.0),
                  data, body_size=13, first_col_bold=True,
                  col_widths=[3.0, 1.5, 5.5, 2.1])

        add_callout(s, Inches(0.6), Inches(4.0), Inches(6.0), Inches(2.8),
                    "Caracterização técnica",
                    "• 78 relatórios distintos — 100 % Análise de Falha (AF).\n"
                    "• Cliente predominante: PETROBRÁS COMPARTILHADO.\n"
                    "• Tipos: Caldeira, Permutador, Vaso Separador, Válvula, Eixo, Cilindro, Tubos…\n"
                    "• Chunk médio em report_texts: ≈ 400 tokens (1.600 chars).\n"
                    "• Premissa do bench validada empiricamente.")
        add_callout(s, Inches(6.9), Inches(4.0), Inches(6.0), Inches(2.8),
                    "Implicação p/ a decisão",
                    "Corpus pequeno em volume, denso em jargão de engenharia.\n\n"
                    "Desafio do RAG aqui é PRECISÃO SEMÂNTICA em terminologia de inspeção — "
                    "não é escala.\n\n"
                    "Custo de qualquer embedding é irrelevante: < US$ 0.40 reindexa tudo no text-embedding-3-large.",
                    accent=GOOD)
    return _


SLIDES.append(slide_corpus())


def slide_bug():
    def _():
        s = add_slide()
        header(s, "Bug detectado — mismatch entre indexação e query", kicker="4. ⚠️ Descoberta crítica")
        # Diagrama lateral
        add_rect(s, Inches(0.6), Inches(1.7), Inches(5.8), Inches(1.4), BG_LIGHT)
        add_text(s, Inches(0.7), Inches(1.75), Inches(5.6), Inches(0.4),
                 "INDEXAÇÃO (chroma.sqlite3)", size=11, bold=True, color=NAVY)
        add_text(s, Inches(0.7), Inches(2.10), Inches(5.6), Inches(0.5),
                 "models/fine_tuned_report_model", size=15, bold=True, color=TEXT)
        add_text(s, Inches(0.7), Inches(2.55), Inches(5.6), Inches(0.5),
                 "sentence-transformer fine-tunado pelo time, 768 dim", size=11, italic=True, color=MUTED)

        add_rect(s, Inches(6.9), Inches(1.7), Inches(5.8), Inches(1.4), BG_LIGHT)
        add_text(s, Inches(7.0), Inches(1.75), Inches(5.6), Inches(0.4),
                 "QUERY (chroma.service.ts:97)", size=11, bold=True, color=NAVY)
        add_text(s, Inches(7.0), Inches(2.10), Inches(5.6), Inches(0.5),
                 "Xenova/paraphrase-multilingual-mpnet-base-v2", size=15, bold=True, color=TEXT)
        add_text(s, Inches(7.0), Inches(2.55), Inches(5.6), Inches(0.5),
                 "MPNet vanilla, ONNX em Node, 768 dim", size=11, italic=True, color=MUTED)

        # Seta indicativa de conflito
        arrow = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW,
                                   Inches(6.42), Inches(2.2), Inches(0.45), Inches(0.4))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = WARN
        arrow.line.fill.background()

        add_callout(s, Inches(0.6), Inches(3.4), Inches(12.1), Inches(1.6),
                    "O que acontece",
                    "Os dois modelos NÃO produzem o mesmo espaço vetorial. "
                    "Embeddings de query estão desalinhados dos de indexação. "
                    "Recall do retrieval atual está DEGRADADO de forma imprevisível, "
                    "mascarado por funcionar minimamente.",
                    accent=WARN)
        add_text(s, Inches(0.6), Inches(5.2), Inches(12), Inches(0.4),
                 "Implicações para a sprint", size=14, bold=True, color=NAVY)
        add_bullets(s, Inches(0.6), Inches(5.55), Inches(12.1), Inches(1.7), [
            "Resolver o mismatch ANTES de comparar com OpenAI — caso contrário, baseline está injustamente baixa.",
            "fine_tuned_report_model é asset externo do ml_wo — NÃO está no repo. Decisão de produto: manter pipeline de fine-tuning ou descontinuar.",
            "Bench passa a ter V1a (status quo, mismatch) vs V1b (vanilla coerente) — isola o efeito do bug.",
        ], size=13)
    return _


SLIDES.append(slide_bug())


def slide_ingestao():
    def _():
        s = add_slide()
        header(s, "Ingestão contínua — requisito novo identificado", kicker="5. Escopo expandido")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12), Inches(0.4),
                 "chroma_db_finetune é apenas o banco INICIAL. Em produção, novos laudos serão indexados continuamente.",
                 size=14, italic=True, color=MUTED)

        # Caixa pipeline
        boxes = [
            ("report-generate finaliza DOCX", 0.6),
            ("fila de ingestão (pg-boss / LISTEN/NOTIFY)", 3.05),
            ("worker: extract → embed → upsert no Chroma", 5.85),
            ("report_texts + metallography_captions atualizadas", 9.45),
        ]
        for label, x in boxes:
            add_rect(s, Inches(x), Inches(2.4), Inches(3.1 if x != 9.45 else 3.3), Inches(0.7), BG_LIGHT)
            add_text(s, Inches(x + 0.1), Inches(2.45), Inches(3.0 if x != 9.45 else 3.2),
                     Inches(0.65), label, size=11, bold=True, color=NAVY)
        for x in (2.55, 5.35, 8.95):
            tri = s.shapes.add_shape(MSO_SHAPE.RIGHT_TRIANGLE,
                                     Inches(x + 1.07), Inches(2.55), Inches(0.4), Inches(0.4))
            tri.rotation = 0
            tri.fill.solid()
            tri.fill.fore_color.rgb = ACCENT
            tri.line.fill.background()

        # Decisões
        data = [
            ["Ponto de decisão", "Recomendação"],
            ["Sincronia", "Assíncrona via fila — SLA ~1 min entre gerar e buscável."],
            ["Idempotência", "Upsert por id_relatorio — re-roda sem duplicar."],
            ["Fila", "Reusar Postgres já existente (pg-boss ou LISTEN/NOTIFY). Evita Redis."],
            ["Versionamento", "Gravar embedding_model_version no metadado de cada chunk."],
            ["Custo por laudo", "≈ US$ 0.0002 com text-embedding-3-small (Standard API)."],
            ["Batch API (−50 %)", "NÃO serve para online — é assíncrona até 24 h. Só p/ reindex em massa."],
        ]
        add_table(s, Inches(0.6), Inches(3.55), Inches(12.1), Inches(3.3),
                  data, body_size=11, col_widths=[3.0, 9.1])
    return _


SLIDES.append(slide_ingestao())


def slide_opcoes():
    def _():
        s = add_slide()
        header(s, "Opções de stack avaliadas", kicker="6. Comparativo")
        data = [
            ["Opção", "Embedding", "Vector store", "LLM gerador"],
            ["A — Baseline (atual)", "Xenova/MPNet local (ou fine-tuned)", "Chroma local (file-based)",
             "A definir (local ou API)"],
            ["B — OpenAI completo", "text-embedding-3-small/large (API)", "Chroma local (mesmo store)",
             "OpenAI (4o-mini → 4.1)"],
            ["C — Híbrida (referencial)", "OpenAI v3 (qualidade)", "pgvector no Postgres existente",
             "OpenAI ou local (fallback)"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(2.6),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[3.0, 3.4, 3.0, 2.7])

        add_callout(s, Inches(0.6), Inches(4.5), Inches(12.1), Inches(2.4),
                    "Por que C entra no radar mesmo sem ser a pergunta original",
                    "• Projeto já tem Postgres (libs/db-lib) — pgvector elimina o apps/chroma-server "
                    "Python e simplifica deploy.\n"
                    "• Vector store deixa de ser dependência operacional separada.\n"
                    "• Permite ingestão continua via transação no MESMO banco onde o laudo é salvo.\n"
                    "• Recomendação prática: começar com B (troca isolada do embedder), evoluir p/ C "
                    "quando a pipeline de ingestão for implementada.")
    return _


SLIDES.append(slide_opcoes())


def slide_custos():
    def _():
        s = add_slide()
        header(s, "Custos — embedding e LLM gerador", kicker="7. Custos")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12), Inches(0.4),
                 "Custos verificados via OpenAI Pricing em 2026-06-01.",
                 size=11, italic=True, color=MUTED)

        # Embedding
        add_text(s, Inches(0.6), Inches(1.95), Inches(12), Inches(0.4),
                 "Indexação (Standard / Batch −50 %)", size=14, bold=True, color=NAVY)
        emb = [
            ["Modelo", "$/1M tok (Std/Batch)", "Corpus atual ~3M tok", "Projeção 1 ano ~13M tok"],
            ["Xenova MPNet (local)", "$0 / n/a", "~30 min CPU", "~2 h CPU"],
            ["text-embedding-3-small", "$0.020 / $0.010", "$0.06 / $0.03", "$0.26 / $0.13"],
            ["text-embedding-3-large", "$0.130 / $0.065", "$0.39 / $0.20", "$1.69 / $0.85"],
        ]
        add_table(s, Inches(0.6), Inches(2.35), Inches(12.1), Inches(1.7),
                  emb, body_size=11, first_col_bold=True,
                  col_widths=[3.2, 2.9, 3.0, 3.0])

        # LLM
        add_text(s, Inches(0.6), Inches(4.25), Inches(12), Inches(0.4),
                 "LLM gerador (onde mora o custo real)", size=14, bold=True, color=NAVY)
        llm = [
            ["Modelo", "$/1M in", "$/1M out", "Por resposta (3k in / 500 out)", "10k respostas/mês"],
            ["gpt-4o-mini", "$0.15", "$0.60", "~$0.0008", "~$8"],
            ["gpt-4.1-mini", "$0.40", "$1.60", "~$0.0020", "~$20"],
            ["gpt-4o", "$2.50", "$10.00", "~$0.0130", "~$130"],
            ["gpt-4.1", "$2.00", "$8.00", "~$0.0100", "~$100"],
        ]
        add_table(s, Inches(0.6), Inches(4.65), Inches(12.1), Inches(2.05),
                  llm, body_size=11, first_col_bold=True,
                  col_widths=[2.6, 1.6, 1.6, 3.4, 2.9])

        add_text(s, Inches(0.6), Inches(6.80), Inches(12), Inches(0.4),
                 "Conclusão: embedding NÃO é critério de decisão. Custo da camada é irrelevante. "
                 "Decidir LLM primeiro — gpt-4o-mini como baseline.",
                 size=11, italic=True, color=ACCENT, bold=True)
    return _


SLIDES.append(slide_custos())


def slide_viabilidade():
    def _():
        s = add_slide()
        header(s, "Viabilidade qualitativa", kicker="8. Trade-offs")
        data = [
            ["Critério", "Chroma local + Xenova", "OpenAI Embeddings + API"],
            ["Privacidade", "✓ Total (on-prem)", "△ DPA + ZDR + mascaramento"],
            ["Qualidade em PT-BR", "△ MPNet de 2021", "✓ v3 supera em MTEB/MIRACL"],
            ["Operação", "△ 2 processos + modelo ONNX no Node", "✓ 1 processo (pgvector pode reduzir mais)"],
            ["Cold start", "△ 2–5 s (1ª query)", "✓ ~0 (SLA OpenAI 99.9 %)"],
            ["Reprodutibilidade", "✓ Modelo versionável local", "△ Modelo pode mudar (ada-002 já passou por isso)"],
            ["Escala (>500k chunks)", "△ Chroma sqlite sofre", "△ store é o gargalo, não o embedder"],
            ["Compliance on-prem", "✓ Compatível", "✗ Pode bloquear contrato"],
            ["Tempo p/ implementar", "Pronto", "2–3 dias (troca embeddingFunction + reindex)"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.0),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[3.4, 4.4, 4.3])
    return _


SLIDES.append(slide_viabilidade())


def slide_latencia_estimada():
    def _():
        s = add_slide()
        header(s, "Latência — estimativa por etapa do pipeline", kicker="9. Latência (estimativa)")
        data = [
            ["Operação", "Local (Xenova / CPU)", "OpenAI (3-small)"],
            ["Embedding de 1 query (~30 tok)", "80–250 ms", "60–180 ms"],
            ["Embedding batch 32 (~12k tok)", "1.5–4 s", "200–500 ms"],
            ["Query top-k=5 (HNSW, 100k vetores)", "10–40 ms", "10–40 ms (mesmo store)"],
            ["Pipeline RAG (embed + search)", "120–300 ms", "100–250 ms"],
            ["Resposta LLM (gpt-4o-mini, 3k→500 tok)", "n/a", "1.5–4 s"],
            ["Cold start MPNet (1ª query pós-boot)", "2–5 s", "~0 (warm)"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(3.6),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[5.0, 3.6, 3.5])
        add_callout(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.4),
                    "Leitura",
                    "Latência do pipeline RAG é DOMINADA pelo LLM, não pelo embedding nem pelo store. "
                    "Local só ganha com GPU. Em CPU pura, OpenAI ganha em batch. "
                    "Cold start do Xenova é problema em ambiente serverless — irrelevante em backend long-running.")
    return _


SLIDES.append(slide_latencia_estimada())


def slide_lat_real():
    def _():
        s = add_slide()
        header(s, "Resultado real — latência do Chroma HNSW", kicker="10. Bench rodado em 2026-06-01")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12.0), Inches(0.4),
                 "200 queries × vetores aleatórios 768d normalizados, contra o chroma-server v1.5.9 local.",
                 size=12, italic=True, color=MUTED)

        data = [
            ["Coleção", "Docs", "p50", "p95", "p99", "mean"],
            ["report_texts", "78", "4.58 ms", "5.46 ms", "5.99 ms", "4.68 ms"],
            ["metallography_captions", "7.943", "5.08 ms", "6.39 ms", "6.97 ms", "5.24 ms"],
        ]
        add_table(s, Inches(0.6), Inches(2.05), Inches(12.1), Inches(1.6),
                  data, body_size=13, first_col_bold=True,
                  col_widths=[3.5, 1.4, 1.7, 1.7, 1.7, 2.1])

        add_callout(s, Inches(0.6), Inches(4.0), Inches(12.1), Inches(2.7),
                    "Conclusão sobre o store",
                    "• Passar de 78 para ~8 000 docs adiciona apenas ~0.5 ms p50.\n"
                    "• HNSW NÃO É GARGALO nesta faixa de volume.\n"
                    "• Latência do RAG vai ser dominada por embedding (rede até OpenAI) e LLM gerador.\n"
                    "• Chroma local pode permanecer no roadmap de curto prazo; pgvector é evolução, não urgência.",
                    accent=GOOD)
    return _


SLIDES.append(slide_lat_real())


def slide_tfidf():
    def _():
        s = add_slide()
        header(s, "Resultado real — baseline TF-IDF (piso de qualidade)",
               kicker="11. Bench rodado em 2026-06-01")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12.0), Inches(0.4),
                 "234 queries do golden sintético × 78 chunks. scikit-learn unigram+bigram, stopwords PT-BR, sublinear TF.",
                 size=11, italic=True, color=MUTED)

        data = [
            ["Métrica", "Valor", "Leitura"],
            ["Recall@5", "0.671", "67 % dos relatórios certos no top-5"],
            ["Recall@10", "0.731", "+6pp ampliando até top-10"],
            ["MRR", "0.604", "Posição média do hit ≈ 1.65"],
            ["nDCG@10", "0.885", "Quando acha, está no topo"],
            ["Embed latency p50", "0.42 ms", "in-process, sem rede"],
            ["Search latency p50", "0.65 ms", "cosine vs 78 docs em memória"],
        ]
        add_table(s, Inches(0.6), Inches(2.05), Inches(7.0), Inches(3.6),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[2.5, 1.8, 2.7])

        # Imagem do gráfico
        chart = CHARTS_DIR / "quality.png"
        if chart.exists():
            s.shapes.add_picture(str(chart), Inches(7.8), Inches(2.05),
                                 width=Inches(4.9), height=Inches(2.45))

        add_callout(s, Inches(0.6), Inches(5.85), Inches(12.1), Inches(1.1),
                    "Por que isso importa",
                    "TF-IDF é um piso conhecido. Qualquer stack neural que não bata isso "
                    "com folga (≥ +15pp em Recall@5) é REGRESSÃO disfarçada — "
                    "não justifica custo, complexidade, dependência externa.",
                    accent=ACCENT)
    return _


SLIDES.append(slide_tfidf())


def slide_breakdown():
    def _():
        s = add_slide()
        header(s, "Onde TF-IDF brilha — e onde o neural precisa ganhar",
               kicker="12. Insight central")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12.0), Inches(0.4),
                 "Recall@5 do TF-IDF segmentado por tipo de query no golden sintético.",
                 size=11, italic=True, color=MUTED)

        data = [
            ["Tipo de query", "Recall@5", "n", "Comportamento"],
            ["content.first_sentence (cita frase literal)", "1.000", "35", "Match lexical perfeito"],
            ["content.dano (keyword de dano)", "0.885", "26", "Palavra-chave presente no chunk"],
            ["metadata.tag.danos / conclusao / causa", "0.69–0.76", "97", "Tag aparece no texto"],
            ["metadata.analise_tag", "0.680", "25", "Tag + termo técnico"],
            ["metadata.cliente_unidade", "0.308", "26", "Cliente/unidade NÃO está no chunk"],
            ["metadata.equipamento (por nº relatório)", "0.120", "25", "Nº relatório NÃO está no texto"],
        ]
        add_table(s, Inches(0.6), Inches(2.05), Inches(12.1), Inches(3.6),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[4.5, 1.6, 1.0, 5.0])

        add_callout(s, Inches(0.6), Inches(5.85), Inches(12.1), Inches(1.2),
                    "Tradução do gráfico",
                    "O abismo de 100 % → 12 % é EXATAMENTE onde embedding neural deve ganhar: "
                    "queries que pedem por metadado não presente no texto exigem entendimento semântico. "
                    "Esse é o teste central da migração — V2/V3/V4 precisam fechar esse gap.",
                    accent=GOOD)
    return _


SLIDES.append(slide_breakdown())


def slide_stack_proposta():
    def _():
        s = add_slide()
        header(s, "Stack proposta", kicker="13. Recomendação")
        items = [
            ("1.", "Manter ChromaDB como store no curto prazo; pgvector entra no roadmap (elimina chroma-server Python)."),
            ("2.", "Trocar embedder para text-embedding-3-small com dimensions=768 — compatível com a coleção atual; A/B sem refazer schema."),
            ("3.", "Manter Xenova/MPNet como fallback feature-flagged — cobre ambientes on-prem e failover OpenAI."),
            ("4.", "LLM gerador: começar com gpt-4o-mini (~US$ 0.0008/resposta), medir contra gpt-4.1-mini antes de subir para os modelos completos."),
            ("5.", "Pré-condições inegociáveis: DPA assinado + Zero Data Retention habilitado + mascaramento de PII (cliente, contrato, tag) antes do envio."),
            ("6.", "Resolver o mismatch §4 ANTES da migração — ou indexar coerentemente com vanilla, ou recuperar o fine_tuned_report_model."),
            ("7.", "Implementar pipeline de ingestão contínua usando Postgres existente — pg-boss ou LISTEN/NOTIFY."),
        ]
        y = Inches(1.55)
        for num, text in items:
            add_text(s, Inches(0.6), y, Inches(0.5), Inches(0.5),
                     num, size=18, bold=True, color=ACCENT)
            add_text(s, Inches(1.05), y + Inches(0.02), Inches(11.6), Inches(0.7),
                     text, size=13, color=TEXT)
            y += Inches(0.74)
    return _


SLIDES.append(slide_stack_proposta())


def slide_gonogo():
    def _():
        s = add_slide()
        header(s, "Critérios de Go / No-Go para Opção B",
               kicker="14. Decisão objetiva")
        add_text(s, Inches(0.6), Inches(1.55), Inches(12), Inches(0.4),
                 "Trocar de MPNet para OpenAI Embeddings SOMENTE se o bench confirmar TODOS os critérios abaixo:",
                 size=14, color=NAVY, italic=True)
        items = [
            "Recall@5 do candidato (V2/V3/V4) ≥ +5pp acima do baseline coerente (V1b) no golden sintético.",
            "MRR do candidato ≥ +0.05 acima do baseline coerente.",
            "p95 de latência end-to-end de embedding + search ≤ 400 ms.",
            "DPA assinado + ZDR habilitado + ticket jurídico de mascaramento aprovado.",
        ]
        add_bullets(s, Inches(0.6), Inches(2.5), Inches(12.1), Inches(2.5),
                    items, size=16, bullet_color=GOOD)
        add_callout(s, Inches(0.6), Inches(5.3), Inches(12.1), Inches(1.6),
                    "Caso algum critério falhe",
                    "Manter Opção A. Revisitar com BGE-m3 ou multilingual-e5-large local — "
                    "modelos open-source mais novos, gratuitos, geralmente superam MPNet em PT-BR "
                    "sem custo recorrente nem saída de dados.")
    return _


SLIDES.append(slide_gonogo())


def slide_riscos():
    def _():
        s = add_slide()
        header(s, "Riscos e mitigações", kicker="15. Riscos")
        data = [
            ["Risco", "Mitigação"],
            ["Golden curado humano não fica pronto até a review", "Usar golden sintético já gerado (234 queries em /bench/golden-set.synthetic.csv) como métrica oficial; substituir quando o humano vier."],
            ["OpenAI deprecia modelo (ada-002 já foi)", "Pin do modelo + reembed semestral previsto no orçamento (~US$ 0.20 por full rebuild)."],
            ["Cliente vetar saída de dados após contrato fechado", "Feature-flag EMBEDDING_PROVIDER no ChromaService desde o dia 1 — fallback Xenova permanece deployável."],
            ["Custo de LLM explodir com adoção", "Tracking de tokens por endpoint + alerta acima do P95 esperado."],
            ["apps/chroma-server vira gargalo / SPOF", "Migrar coleção para pgvector no Postgres existente (libs/db-lib)."],
            ["Pipeline de fine-tuning é mantido mas asset some de novo", "Versionar fine_tuned_report_model em S3 + Git LFS, ou descontinuar formalmente e adotar embedder padrão."],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.3),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[4.3, 7.8])
    return _


SLIDES.append(slide_riscos())


def slide_restricao():
    def _():
        s = add_slide()
        header(s, "Restrição operacional — pendência de TI",
               kicker="16. Bloqueio identificado")
        add_callout(s, Inches(0.6), Inches(1.65), Inches(12.1), Inches(1.5),
                    "O que foi detectado",
                    "Tentativa de rodar o bench neural no ambiente de desenvolvimento atual "
                    "falhou: a política de rede bloqueia saída para huggingface.co e "
                    "api.openai.com. Sem essas duas saídas, V1a/V1b/V2/V3/V4 não podem "
                    "ser medidas.",
                    accent=WARN)
        add_text(s, Inches(0.6), Inches(3.35), Inches(12), Inches(0.4),
                 "Hosts que precisam ser liberados (allowlist)",
                 size=14, bold=True, color=NAVY)
        data = [
            ["Host", "Para quê", "Quando"],
            ["huggingface.co", "Download de MPNet vanilla, BGE-m3, e5-multilingual e outros modelos open-source", "Uma vez (cache local) — depois pode bloquear"],
            ["api.openai.com", "Embeddings v3 (small/large) + LLM gerador (gpt-4o-mini)", "Permanente em prod"],
        ]
        add_table(s, Inches(0.6), Inches(3.8), Inches(12.1), Inches(1.7),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[3.0, 6.0, 3.1])
        add_callout(s, Inches(0.6), Inches(5.7), Inches(12.1), Inches(1.2),
                    "Alternativa imediata enquanto a TI processa",
                    "Rodar o bench numa workstation pessoal desbloqueada. Scripts em "
                    "apps/chroma-server/bench/ são reproducíveis: ~3 h para gerar V1b/V2/V3/V4 "
                    "+ score + PNGs no mesmo formato dos que já estão neste deck.")
    return _


SLIDES.append(slide_restricao())


def slide_tldr():
    def _():
        s = add_slide()
        header(s, "TL;DR", kicker="17. Resumo executivo")
        items = [
            "Corpus é pequeno (8 021 chunks) e técnico — desafio é precisão semântica, não escala. Custo de embedding é IRRELEVANTE.",
            "BUG em produção: índice usa fine_tuned_report_model (fora do repo); query usa Xenova vanilla. Mismatch resolve antes de tudo.",
            "Ingestão contínua entra no escopo: pipeline event-driven no Postgres já existente; ~US$ 0.0002 por laudo.",
            "Chroma HNSW NÃO é gargalo (medido): p99 = 5.99 ms em 78 docs, 6.97 ms em ~8k docs.",
            "TF-IDF entrega Recall@5 = 67 % no sintético — stack neural precisa bater isso com ≥ +15pp.",
            "Onde o neural deve ganhar: queries por metadado (12–31 % no TF-IDF) — gap semântico claro.",
            "Stack proposta: Chroma → pgvector no roadmap; text-embedding-3-small@768 com fallback Xenova; gpt-4o-mini baseline; DPA + ZDR + mascaramento.",
            "Bloqueio: TI precisa liberar huggingface.co e api.openai.com para completar o bench neural antes da review.",
        ]
        add_bullets(s, Inches(0.6), Inches(1.55), Inches(12.1), Inches(5.5),
                    items, size=14, line_spacing=1.2)
    return _


SLIDES.append(slide_tldr())


def slide_next():
    def _():
        s = add_slide()
        header(s, "Próximos passos concretos", kicker="18. Plano de ação")
        data = [
            ["#", "Ação", "Esforço", "Bloqueia"],
            ["1", "Pedir TI a liberação de huggingface.co + api.openai.com (allowlist)", "discussão", "Bench neural"],
            ["2", "Rodar prepare.py + run-queries-local.py / run-queries.ts + score.py com OPENAI_API_KEY", "~3 h", "Apresentação completa"],
            ["3", "Decidir destino do fine_tuned_report_model (manter, descontinuar, versionar em S3 + LFS)", "discussão", "Stack final"],
            ["4", "Implementar pipeline de ingestão contínua (§5)", "3–5 dias", "Produção"],
            ["5", "Curar 50–100 pares humanos do golden set com o time de domínio", "depende do domínio", "Validação final"],
            ["6", "Assinar DPA OpenAI + habilitar Zero Data Retention + plano de mascaramento de PII", "jurídico + dev", "Produção c/ dados reais"],
        ]
        add_table(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(4.8),
                  data, body_size=12, first_col_bold=True,
                  col_widths=[0.6, 6.5, 1.8, 3.2])
        add_text(s, Inches(0.6), Inches(6.55), Inches(12), Inches(0.4),
                 "Documento completo: references/ANALISE_VECTOR_STORE.md  •  Scripts: apps/chroma-server/bench/",
                 size=11, italic=True, color=MUTED)
    return _


SLIDES.append(slide_next())


def slide_obrigado():
    def _():
        s = add_slide()
        add_rect(s, Emu(0), Emu(0), SW, SH, NAVY)
        add_rect(s, Emu(0), Inches(6.5), SW, Inches(1.0), ACCENT)
        add_text(s, Inches(0.7), Inches(2.5), Inches(12), Inches(1.5),
                 "Perguntas?", size=54, bold=True,
                 color=RGBColor(0xFF, 0xFF, 0xFF))
        add_text(s, Inches(0.7), Inches(4.0), Inches(12), Inches(0.5),
                 "Branch: claude/eloquent-pasteur-hMz2o",
                 size=14, color=RGBColor(0xE0, 0xDE, 0xD0))
        add_text(s, Inches(0.7), Inches(4.4), Inches(12), Inches(0.5),
                 "Documento técnico: references/ANALISE_VECTOR_STORE.md",
                 size=14, color=RGBColor(0xE0, 0xDE, 0xD0))
        add_text(s, Inches(0.7), Inches(4.8), Inches(12), Inches(0.5),
                 "Bench: apps/chroma-server/bench/",
                 size=14, color=RGBColor(0xE0, 0xDE, 0xD0))
    return _


SLIDES.append(slide_obrigado())


# ---------- render ----------

# clean default slide
total = len(SLIDES)
for fn in SLIDES:
    fn()

# add footers to all content slides except cover and back
content_slides = list(prs.slides)
for idx, sl in enumerate(content_slides, start=1):
    if 1 < idx < len(content_slides):
        footer(sl, idx, total)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT_PATH)
print(f"deck gerado: {OUT_PATH}  ({total} slides)")

"""
generate-synthetic-golden.py — Gera um golden set sintético a partir dos chunks
reais da coleção `report_texts`, sem depender de curadoria humana.

Dois modos:
  --mode heuristic   (default) usa templates + entidades dos metadados
                     (cliente, tag, tipo_equipamento, tipo_analise) e frases
                     do próprio chunk. Sem LLM, sem API key, offline.
  --mode llm         usa OpenAI gpt-4o-mini para gerar perguntas mais naturais.
                     Requer OPENAI_API_KEY.

Saída: CSV com colunas
  question, expected_report_id, source_chunk_excerpt, mode, template

IMPORTANTE — limitações conhecidas do golden sintético:
  - Viés positivo: a pergunta tende a usar o vocabulário do próprio chunk,
    inflacionando Recall vs queries humanas reais.
  - É um PISO de qualidade, não um teto. Use enquanto o curado humano não vem.
  - Heurístico cobre menos diversidade que o modo LLM.

Uso:
  python generate-synthetic-golden.py \
      --db ../chroma_db_finetune/chroma.sqlite3 \
      --out golden-set.synthetic.csv \
      --per-chunk 2

  python generate-synthetic-golden.py --mode llm --per-chunk 3
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# ---------- leitura dos chunks ----------

def fetch_chunks(db_path: str, collection_name: str = "report_texts") -> list[dict]:
    con = sqlite3.connect(os.path.abspath(db_path))
    cur = con.cursor()
    row = cur.execute("SELECT id FROM collections WHERE name=?", (collection_name,)).fetchone()
    if not row:
        sys.exit(f"coleção '{collection_name}' não encontrada em {db_path}")
    coll_id = row[0]
    emb_pks = [r[0] for r in cur.execute(
        "SELECT id FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection=?)",
        (coll_id,),
    )]
    chunks = []
    for pk in emb_pks:
        meta: dict = {}
        for k, sv, iv in cur.execute(
            "SELECT key, string_value, int_value FROM embedding_metadata WHERE id=?",
            (pk,),
        ):
            meta[k] = sv if sv is not None else iv
        doc = meta.pop("chroma:document", "")
        if not doc or "id_relatorio" not in meta:
            continue
        chunks.append({"document": doc, "metadata": meta})
    return chunks


# ---------- modo heurístico ----------

# Templates que casam com o domínio (Análise de Falhas industrial)
TEMPLATES_BY_FIELD = {
    "tipo_equipamento": [
        "Qual o tipo de equipamento analisado no relatório {numero_relatorio}?",
        "Que equipamento foi alvo da análise de falha no contrato {numero_contrato}?",
    ],
    "tag": [
        "Quais foram os danos observados no equipamento {tag}?",
        "Qual a conclusão da análise de falha do {tag}?",
        "O que causou a falha no {tag}?",
    ],
    "cliente_unidade": [
        "Qual a análise de falha realizada para o cliente {cliente} na unidade {unidade}?",
    ],
    "tipo_analise_tag": [
        "Quais foram os mecanismos de dano identificados na análise de {tag}?",
    ],
}

# Padrões para extrair "primeiro fato" do chunk (frase inicial técnica)
KEYWORDS_DANOS = [
    "corrosão", "trinca", "fratura", "desgaste", "deformação",
    "fissura", "ruptura", "fadiga", "vazamento", "erosão",
    "perda de espessura", "incrustação", "pite", "envelhecimento",
]


def first_sentence(text: str, max_chars: int = 220) -> str:
    # Pega a primeira sentença útil (não trivial).
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    for s in sentences:
        s = s.strip()
        if len(s) > 40:
            return s[:max_chars]
    return text[:max_chars]


def find_danos(text: str) -> list[str]:
    found = []
    low = text.lower()
    for kw in KEYWORDS_DANOS:
        if kw in low:
            found.append(kw)
    return found


def generate_queries_heuristic(chunk: dict, n: int) -> list[tuple[str, str]]:
    """Retorna lista de (question, template_used)."""
    m = chunk["metadata"]
    doc = chunk["document"]
    queries: list[tuple[str, str]] = []

    # 1. Templates baseados em metadados
    if m.get("numero_relatorio"):
        for t in TEMPLATES_BY_FIELD["tipo_equipamento"]:
            queries.append((t.format(**m), "metadata.equipamento"))
            break  # 1 só por template
    if m.get("tag"):
        # Vai gerar 1 query "danos" e 1 "conclusão"
        queries.append((TEMPLATES_BY_FIELD["tag"][0].format(**m), "metadata.tag.danos"))
        queries.append((TEMPLATES_BY_FIELD["tag"][1].format(**m), "metadata.tag.conclusao"))
        queries.append((TEMPLATES_BY_FIELD["tag"][2].format(**m), "metadata.tag.causa"))
    if m.get("cliente") and m.get("unidade"):
        queries.append((TEMPLATES_BY_FIELD["cliente_unidade"][0].format(**m), "metadata.cliente_unidade"))
    if m.get("tipo_analise") == "AF" and m.get("tag"):
        queries.append((TEMPLATES_BY_FIELD["tipo_analise_tag"][0].format(**m), "metadata.analise_tag"))

    # 2. Queries baseadas em conteúdo do chunk
    danos = find_danos(doc)
    if danos:
        damage_q = (
            f"Houve indícios de {danos[0]} na análise do equipamento "
            f"{m.get('tipo_equipamento', 'em questão')}?"
        )
        queries.append((damage_q, "content.dano"))

    # 3. Query "natural" usando trecho do início
    fs = first_sentence(doc)
    if fs:
        # Transforma a frase inicial num query "Sobre qual relatório fala-se de ...?"
        snippet = fs[:150].rstrip(",. ")
        nat_q = f"Em qual relatório é descrito: \"{snippet}\"?"
        queries.append((nat_q, "content.first_sentence"))

    # Deduplica e amostra
    seen = set()
    unique: list[tuple[str, str]] = []
    for q, tpl in queries:
        if q not in seen:
            seen.add(q)
            unique.append((q, tpl))
    random.shuffle(unique)
    return unique[:n]


# ---------- modo LLM ----------

def generate_queries_llm(chunk: dict, n: int) -> list[tuple[str, str]]:
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("modo llm requer: pip install openai")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY ausente no ambiente")
    client = OpenAI(api_key=api_key)

    m = chunk["metadata"]
    doc = chunk["document"][:2000]  # limita
    prompt = (
        "Você é um engenheiro de inspeção industrial. Dado o trecho de uma "
        "ANÁLISE DE FALHA abaixo, gere "
        f"{n} perguntas curtas em português (PT-BR) que um inspetor faria para "
        "RECUPERAR esse trecho num sistema de busca semântica. As perguntas "
        "devem ser específicas, variadas (1 sobre dano, 1 sobre equipamento, "
        f"1 sobre causa), e NÃO devem usar o número do relatório.\n\n"
        f"Metadados: equipamento={m.get('tipo_equipamento')}, "
        f"tag={m.get('tag')}, cliente={m.get('cliente')}, unidade={m.get('unidade')}\n\n"
        f"Trecho:\n{doc}\n\n"
        "Saída: uma pergunta por linha, sem numeração, sem aspas."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=300,
    )
    text = resp.choices[0].message.content or ""
    questions = [
        line.strip().lstrip("-*0123456789. )") for line in text.splitlines() if line.strip()
    ]
    return [(q, "llm.gpt-4o-mini") for q in questions[:n]]


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default="../chroma_db_finetune/chroma.sqlite3",
        help="caminho do chroma.sqlite3",
    )
    parser.add_argument("--collection", default="report_texts")
    parser.add_argument("--out", default="golden-set.synthetic.csv")
    parser.add_argument("--mode", choices=["heuristic", "llm"], default="heuristic")
    parser.add_argument("--per-chunk", type=int, default=2)
    parser.add_argument("--max-chunks", type=int, default=None,
                        help="limita o número de chunks (default: todos)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    chunks = fetch_chunks(args.db, args.collection)
    print(f"[fetch] {len(chunks)} chunks lidos de {args.db}::{args.collection}")
    if args.max_chunks:
        chunks = chunks[: args.max_chunks]

    rows = []
    gen = generate_queries_llm if args.mode == "llm" else generate_queries_heuristic

    # Distribuição por tipo_equipamento (sanity check)
    eq_count: dict[str, int] = defaultdict(int)

    for i, c in enumerate(chunks, 1):
        rid = c["metadata"].get("id_relatorio")
        if rid is None:
            continue
        try:
            qs = gen(c, args.per_chunk)
        except Exception as e:
            print(f"[{i}/{len(chunks)}] erro: {e}", file=sys.stderr)
            continue
        excerpt = c["document"][:200].replace("\n", " ")
        for q, tpl in qs:
            rows.append({
                "question": q,
                "expected_report_id": rid,
                "source_chunk_excerpt": excerpt,
                "mode": args.mode,
                "template": tpl,
            })
        eq_count[c["metadata"].get("tipo_equipamento", "?")] += 1
        if i % 20 == 0:
            print(f"  ...processados {i}/{len(chunks)}")

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["question", "expected_report_id",
                                          "source_chunk_excerpt", "mode", "template"])
        w.writeheader()
        w.writerows(rows)

    print(f"\n[ok] {len(rows)} queries em {out_path}")
    print("[distribuição por tipo_equipamento]")
    for k, v in sorted(eq_count.items(), key=lambda x: -x[1]):
        print(f"  {v:>3}  {k}")


if __name__ == "__main__":
    main()

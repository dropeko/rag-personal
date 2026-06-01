"""
run-bench-offline.py — Bench que NÃO depende de download de modelos do HF
nem de OpenAI. Útil quando o ambiente bloqueia huggingface.co.

Produz dois conjuntos de números reais:

(A) Qualidade com baseline TF-IDF (scikit-learn) sobre os 78 chunks de
    report_texts. É um piso conhecido — modelos neurais devem superar.
    Métricas: Recall@5/10, MRR, nDCG@10.

(B) Latência REAL do Chroma HNSW na coleção existente `report_texts`
    (que está indexada com fine_tuned_report_model — 768 dim). Como não
    precisamos da qualidade aqui, usamos vetores aleatórios 768d
    normalizados para medir o tempo puro de search.

Saídas:
    - results-tfidf.csv  (qualidade do baseline TF-IDF)
    - latency-chroma.csv (latência por query, p50/p95/p99)

Uso:
    python run-bench-offline.py --golden-set golden-set.synthetic.csv \
        --out-dir reports-offline/ --repeats 5
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import sqlite3
import time
from pathlib import Path

import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

SQLITE_PATH = "../chroma_db_finetune/chroma.sqlite3"
SOURCE_COLLECTION = "report_texts"


def load_chunks_from_sqlite(db_path: str) -> list[dict]:
    con = sqlite3.connect(os.path.abspath(db_path))
    cur = con.cursor()
    coll_id = cur.execute(
        "SELECT id FROM collections WHERE name=?", (SOURCE_COLLECTION,)
    ).fetchone()[0]
    emb_pks = [
        r[0]
        for r in cur.execute(
            "SELECT id FROM embeddings WHERE segment_id IN "
            "(SELECT id FROM segments WHERE collection=?)",
            (coll_id,),
        )
    ]
    chunks = []
    for pk in emb_pks:
        emb_id = cur.execute("SELECT embedding_id FROM embeddings WHERE id=?", (pk,)).fetchone()[0]
        meta: dict = {}
        doc = None
        for k, sv, iv in cur.execute(
            "SELECT key, string_value, int_value FROM embedding_metadata WHERE id=?",
            (pk,),
        ):
            if k == "chroma:document":
                doc = sv
            else:
                val = sv if sv is not None else iv
                if val is not None:
                    meta[k] = val
        if doc and "id_relatorio" in meta:
            chunks.append({"id": emb_id, "document": doc, "metadata": meta})
    return chunks


def parse_golden(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            rows.append({
                "query_id": i,
                "question": row["question"],
                "expected_report_id": str(row["expected_report_id"]),
            })
    return rows


# ---------- (A) TF-IDF baseline ----------

PT_STOPWORDS = [
    "a", "ao", "aos", "as", "à", "às", "com", "como", "da", "das", "de",
    "do", "dos", "e", "em", "entre", "é", "foi", "foram", "havia", "hão",
    "ja", "já", "mais", "mas", "me", "mesmo", "meu", "minha", "muito",
    "nao", "não", "na", "nas", "no", "nos", "nós", "o", "os", "ou", "para",
    "pela", "pelas", "pelo", "pelos", "por", "qual", "que", "quem", "se",
    "sem", "seu", "sua", "também", "te", "tem", "tém", "tinha", "tu", "um",
    "uma", "uns", "umas", "você", "vocês", "esta", "este", "isso",
]


def run_tfidf_quality(chunks: list[dict], golden: list[dict], top_k: int, repeats: int) -> tuple[list[dict], dict]:
    print(f"\n[A] TF-IDF baseline — {len(chunks)} chunks × {len(golden)} queries")
    docs = [c["document"] for c in chunks]
    doc_report_ids = [str(c["metadata"]["id_relatorio"]) for c in chunks]
    doc_ids = [c["id"] for c in chunks]

    vec = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=20000,
        stop_words=PT_STOPWORDS,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    t0 = time.perf_counter()
    doc_matrix = vec.fit_transform(docs)
    fit_ms = (time.perf_counter() - t0) * 1000
    print(f"[A] fit + transform de {len(docs)} chunks: {fit_ms:.0f} ms, vocab={len(vec.vocabulary_)}")

    rows = []
    for q in tqdm(golden, desc="[A] TF-IDF queries"):
        for r in range(1, repeats + 1):
            t0 = time.perf_counter()
            qv = vec.transform([q["question"]])
            embed_ms = (time.perf_counter() - t0) * 1000

            t1 = time.perf_counter()
            sims = cosine_similarity(qv, doc_matrix)[0]
            top_idx = np.argsort(-sims)[:top_k]
            search_ms = (time.perf_counter() - t1) * 1000

            for rank, i in enumerate(top_idx, start=1):
                rows.append({
                    "query_id": q["query_id"],
                    "variant": "v_tfidf_baseline",
                    "repeat": r,
                    "rank": rank,
                    "retrieved_id": doc_ids[i],
                    "retrieved_report_id": doc_report_ids[i],
                    "score": float(sims[i]),
                    "embed_latency_ms": embed_ms,
                    "search_latency_ms": search_ms,
                })

    return rows, {"fit_ms": fit_ms, "vocab_size": len(vec.vocabulary_)}


# ---------- (B) Latência Chroma HNSW ----------

def run_chroma_latency(client, top_k: int, n_queries: int, embedding_dim: int = 768) -> list[dict]:
    print(f"\n[B] Latência Chroma HNSW — {n_queries} queries × dim={embedding_dim}")
    coll = client.get_collection(SOURCE_COLLECTION)
    print(f"[B] coleção '{SOURCE_COLLECTION}' tem {coll.count()} docs")

    rng = np.random.default_rng(seed=42)
    rows = []
    for i in tqdm(range(n_queries), desc="[B] random queries"):
        v = rng.standard_normal(embedding_dim).astype(np.float32)
        v = v / np.linalg.norm(v)  # normalize
        t0 = time.perf_counter()
        res = coll.query(query_embeddings=[v.tolist()], n_results=top_k, include=["distances"])
        ms = (time.perf_counter() - t0) * 1000
        rows.append({
            "query_id": i + 1,
            "variant": "chroma_hnsw_latency",
            "search_latency_ms": ms,
            "results_returned": len(res["ids"][0]),
        })
    return rows


# ---------- writers ----------

def write_csv(path: str, rows: list[dict], cols: list[str]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"[ok] {len(rows)} linhas → {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="golden-set.synthetic.csv")
    parser.add_argument("--out-dir", default="reports-offline/")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--latency-queries", type=int, default=200)
    parser.add_argument("--chroma-url", default="http://localhost:8000")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks_from_sqlite(SQLITE_PATH)
    print(f"[sqlite] {len(chunks)} chunks lidos de report_texts")
    golden = parse_golden(args.golden_set)
    print(f"[golden] {len(golden)} queries")

    host = args.chroma_url.split("://")[-1].split(":")[0]
    port = int(args.chroma_url.rsplit(":", 1)[-1])
    client = chromadb.HttpClient(host=host, port=port)

    # (A) TF-IDF
    tfidf_rows, tfidf_info = run_tfidf_quality(chunks, golden, args.top_k, args.repeats)
    write_csv(out_dir / "results-tfidf.csv", tfidf_rows, [
        "query_id", "variant", "repeat", "rank", "retrieved_id",
        "retrieved_report_id", "score", "embed_latency_ms", "search_latency_ms",
    ])

    # (B) Latência Chroma
    lat_rows = run_chroma_latency(client, args.top_k, args.latency_queries)
    write_csv(out_dir / "latency-chroma.csv", lat_rows,
              ["query_id", "variant", "search_latency_ms", "results_returned"])

    # Resumo rápido
    lat_arr = np.array([r["search_latency_ms"] for r in lat_rows])
    tfidf_lat = np.array([r["search_latency_ms"] for r in tfidf_rows if r["rank"] == 1])
    tfidf_embed = np.array([r["embed_latency_ms"] for r in tfidf_rows if r["rank"] == 1])

    print("\n=== Latência ===")
    print(f"  Chroma HNSW search (random 768d, {len(lat_arr)} queries):")
    print(f"    p50={np.percentile(lat_arr, 50):.2f} ms  "
          f"p95={np.percentile(lat_arr, 95):.2f} ms  "
          f"p99={np.percentile(lat_arr, 99):.2f} ms  "
          f"mean={lat_arr.mean():.2f} ms")
    print(f"  TF-IDF embed (in-process, {len(tfidf_embed)} queries):")
    print(f"    p50={np.percentile(tfidf_embed, 50):.3f} ms  "
          f"p95={np.percentile(tfidf_embed, 95):.3f} ms")
    print(f"  TF-IDF search (cosine vs 78 docs):")
    print(f"    p50={np.percentile(tfidf_lat, 50):.3f} ms  "
          f"p95={np.percentile(tfidf_lat, 95):.3f} ms")

    print(f"\nPróximo passo: rodar score.py sobre results-tfidf.csv para Recall/MRR/nDCG.")


if __name__ == "__main__":
    main()

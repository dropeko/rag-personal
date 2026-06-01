"""
run-queries-local.py — Versão Python do runner para variantes que NÃO precisam
de OpenAI. Mede V1a (status quo, mismatch) e V1b (vanilla coerente) usando
sentence-transformers/paraphrase-multilingual-mpnet-base-v2.

Uso:
    python run-queries-local.py \
        --golden-set golden-set.synthetic.csv \
        --out results.csv \
        --repeats 5 --top-k 10

V1a: query a coleção `report_texts` existente (indexada com
     fine_tuned_report_model) usando MPNet vanilla → reproduz o mismatch.
V1b: cria/reusa coleção `bench_v1b_vanilla` (reindex com vanilla),
     query também com vanilla → cenário coerente.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
SOURCE_COLLECTION = "report_texts"
V1B_COLLECTION = "bench_v1b_vanilla"
SQLITE_PATH = "../chroma_db_finetune/chroma.sqlite3"


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


def ensure_v1b_collection(client: chromadb.HttpClient, model, force: bool):
    existing = {c.name for c in client.list_collections()}
    if V1B_COLLECTION in existing and not force:
        coll = client.get_collection(V1B_COLLECTION)
        if coll.count() > 0:
            print(f"[V1b] coleção '{V1B_COLLECTION}' já existe ({coll.count()} docs) — reutilizando")
            return coll

    if V1B_COLLECTION in existing:
        print(f"[V1b] deletando coleção existente '{V1B_COLLECTION}'")
        client.delete_collection(V1B_COLLECTION)

    print(f"[V1b] lendo chunks de '{SOURCE_COLLECTION}' via sqlite local...")
    chunks = load_chunks_from_sqlite(SQLITE_PATH)
    print(f"[V1b] {len(chunks)} chunks lidos")

    print(f"[V1b] criando coleção '{V1B_COLLECTION}' (cosine)")
    coll = client.create_collection(
        name=V1B_COLLECTION,
        metadata={"description": "vanilla MPNet coerente — bench V1b"},
        configuration={"hnsw": {"space": "cosine"}},
    )

    print(f"[V1b] embedando {len(chunks)} chunks com MPNet vanilla...")
    t0 = time.perf_counter()
    docs = [c["document"] for c in chunks]
    embeddings = model.encode(docs, normalize_embeddings=True, show_progress_bar=True)
    dt = time.perf_counter() - t0
    print(f"[V1b] embedding pronto em {dt:.1f}s ({len(chunks)} chunks)")

    # chromadb não aceita None em metadata; sanitizar
    metas = []
    for c in chunks:
        m = {k: v for k, v in c["metadata"].items() if v is not None}
        metas.append(m)

    coll.add(
        ids=[c["id"] for c in chunks],
        documents=docs,
        metadatas=metas,
        embeddings=embeddings.tolist(),
    )
    print(f"[V1b] inserido. count={coll.count()}")
    return coll


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


def run_variant(
    variant: str,
    collection,
    model,
    golden: list[dict],
    top_k: int,
    repeats: int,
) -> list[dict]:
    print(f"\n[{variant}] rodando {len(golden)} queries × {repeats} repetições "
          f"sobre coleção com {collection.count()} docs")

    # Warm-up
    _ = model.encode(["warmup"], normalize_embeddings=True)

    rows = []
    pbar = tqdm(total=len(golden) * repeats, desc=f"[{variant}]")
    for q in golden:
        for r in range(1, repeats + 1):
            t0 = time.perf_counter()
            emb = model.encode([q["question"]], normalize_embeddings=True)[0]
            embed_ms = (time.perf_counter() - t0) * 1000

            t1 = time.perf_counter()
            res = collection.query(
                query_embeddings=[emb.tolist()],
                n_results=top_k,
                include=["metadatas", "distances"],
            )
            search_ms = (time.perf_counter() - t1) * 1000

            ids = res["ids"][0]
            distances = res["distances"][0]
            metadatas = res["metadatas"][0] or []
            for k, rid in enumerate(ids, start=1):
                meta = metadatas[k - 1] if k - 1 < len(metadatas) else {}
                rows.append({
                    "query_id": q["query_id"],
                    "variant": variant,
                    "repeat": r,
                    "rank": k,
                    "retrieved_id": rid,
                    "retrieved_report_id": str(meta.get("id_relatorio", "")),
                    "score": float(1.0 - distances[k - 1]),
                    "embed_latency_ms": embed_ms,
                    "search_latency_ms": search_ms,
                })
            pbar.update(1)
    pbar.close()
    return rows


def write_results(path: str, rows: list[dict]):
    cols = ["query_id", "variant", "repeat", "rank", "retrieved_id",
            "retrieved_report_id", "score", "embed_latency_ms", "search_latency_ms"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\n[ok] {len(rows)} linhas escritas em {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="golden-set.synthetic.csv")
    parser.add_argument("--out", default="results-local.csv")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--chroma-url", default="http://localhost:8000")
    parser.add_argument("--variants", default="v1a,v1b")
    parser.add_argument("--force-reindex", action="store_true")
    args = parser.parse_args()

    golden = parse_golden(args.golden_set)
    print(f"golden: {len(golden)} queries")

    # Cliente Chroma
    host = args.chroma_url.split("://")[-1].split(":")[0]
    port = int(args.chroma_url.rsplit(":", 1)[-1])
    client = chromadb.HttpClient(host=host, port=port)

    print(f"\n[model] carregando {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"[model] embedding dim = {model.get_sentence_embedding_dimension()}")

    variants = [v.strip() for v in args.variants.split(",")]
    all_rows: list[dict] = []

    if "v1a" in variants:
        col_a = client.get_collection(SOURCE_COLLECTION)
        all_rows.extend(run_variant("v1a_mismatch", col_a, model, golden, args.top_k, args.repeats))

    if "v1b" in variants:
        col_b = ensure_v1b_collection(client, model, force=args.force_reindex)
        all_rows.extend(run_variant("v1b_vanilla_coherent", col_b, model, golden, args.top_k, args.repeats))

    write_results(args.out, all_rows)


if __name__ == "__main__":
    main()

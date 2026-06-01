"""
prepare.py — Gera coleções variantes para o bench.

V1 (MPNet) reusa a coleção `report_texts` existente, sem re-embedding.
V2/V3/V4 re-embedam o corpus via OpenAI.
V5 (opcional, --include-bge) re-embeda via BGE-m3 local.

Uso:
    python prepare.py --variants v2,v3,v4
    python prepare.py --variants v5 --include-bge
    python prepare.py --variants v2 --force         # recria mesmo se já existe
    python prepare.py --variants v2,v3,v4 --batch   # usa Batch API (50% off, async)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass

import chromadb
from chromadb.api.types import EmbeddingFunction
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")
SOURCE_COLLECTION = os.getenv("SOURCE_COLLECTION", "report_texts")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "64"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@dataclass(frozen=True)
class Variant:
    id: str
    provider: str  # "openai" | "local-bge" | "source"
    model: str | None
    dim: int | None  # None = padrão do modelo

    @property
    def collection_name(self) -> str:
        return f"bench_{self.id}"


VARIANTS: dict[str, Variant] = {
    "v1": Variant("v1_mpnet_768", provider="source", model=None, dim=768),
    "v2": Variant("v2_openai_small_768", provider="openai", model="text-embedding-3-small", dim=768),
    "v3": Variant("v3_openai_small_1536", provider="openai", model="text-embedding-3-small", dim=1536),
    "v4": Variant("v4_openai_large_3072", provider="openai", model="text-embedding-3-large", dim=None),
    "v5": Variant("v5_bge_m3_1024", provider="local-bge", model="BAAI/bge-m3", dim=1024),
}
# Aceita também o id longo
for v in list(VARIANTS.values()):
    VARIANTS[v.id] = v


class OpenAIEmbedder:
    def __init__(self, model: str, dim: int | None):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY ausente — preencha o .env")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        kwargs: dict = {"model": self.model, "input": texts}
        if self.dim is not None:
            kwargs["dimensions"] = self.dim
        resp = self.client.embeddings.create(**kwargs)
        return [item.embedding for item in resp.data]


class BgeEmbedder:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "Para v5, instale: pip install sentence-transformers torch"
            ) from e
        self.model = SentenceTransformer("BAAI/bge-m3")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


def get_embedder(variant: Variant):
    if variant.provider == "openai":
        return OpenAIEmbedder(variant.model, variant.dim)
    if variant.provider == "local-bge":
        return BgeEmbedder()
    raise ValueError(f"Embedder não aplicável para {variant.provider}")


def fetch_source_docs(client: chromadb.HttpClient) -> tuple[list[str], list[str], list[dict]]:
    """Lê todos os documentos da coleção fonte (sem embeddings)."""
    src = client.get_collection(SOURCE_COLLECTION)
    total = src.count()
    print(f"[source] coleção '{SOURCE_COLLECTION}' tem {total} documentos")

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    page = 1000
    for offset in tqdm(range(0, total, page), desc="lendo source"):
        res = src.get(limit=page, offset=offset, include=["documents", "metadatas"])
        ids.extend(res["ids"])
        docs.extend(res["documents"] or [])
        metas.extend(res["metadatas"] or [{} for _ in res["ids"]])
    return ids, docs, metas


def reindex(client: chromadb.HttpClient, variant: Variant, ids, docs, metas, force: bool):
    name = variant.collection_name
    existing = [c.name for c in client.list_collections()]
    if name in existing:
        if not force:
            print(f"[{variant.id}] já existe '{name}' — use --force para recriar")
            return
        print(f"[{variant.id}] deletando '{name}' (--force)")
        client.delete_collection(name)

    coll = client.create_collection(name=name, metadata={"variant": variant.id})
    embedder = get_embedder(variant)

    t0 = time.perf_counter()
    total_tokens = 0
    for i in tqdm(range(0, len(docs), EMBED_BATCH_SIZE), desc=f"[{variant.id}] embedding"):
        batch_ids = ids[i : i + EMBED_BATCH_SIZE]
        batch_docs = docs[i : i + EMBED_BATCH_SIZE]
        batch_metas = metas[i : i + EMBED_BATCH_SIZE]
        embeddings = embedder.embed(batch_docs)
        coll.add(ids=batch_ids, documents=batch_docs, metadatas=batch_metas, embeddings=embeddings)
        total_tokens += sum(len(d.split()) for d in batch_docs)  # aprox.

    dt = time.perf_counter() - t0
    print(f"[{variant.id}] indexado em {dt:.1f}s, ~{total_tokens} tokens (aprox)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variants",
        required=True,
        help="lista separada por vírgula: v2,v3,v4 (ou ids longos)",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-bge", action="store_true", help="permite v5")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="usar Batch API (50%% desconto, async — não implementado neste skeleton)",
    )
    args = parser.parse_args()

    if args.batch:
        print(
            "[WARN] --batch é um placeholder no skeleton — implementar via "
            "client.batches.create() quando volume justificar a complexidade "
            "(async, polling até 24h). Para corpus < 1M chunks, Standard é OK."
        )

    requested: list[Variant] = []
    for raw in args.variants.split(","):
        raw = raw.strip()
        v = VARIANTS.get(raw)
        if not v:
            sys.exit(f"variant desconhecida: {raw}. Opções: v1..v5")
        if v.provider == "source":
            print(f"[{v.id}] V1 reusa a coleção fonte '{SOURCE_COLLECTION}' — nada a fazer")
            continue
        if v.provider == "local-bge" and not args.include_bge:
            sys.exit(f"{v.id} requer --include-bge")
        requested.append(v)

    if not requested:
        print("nada para fazer")
        return

    client = chromadb.HttpClient(host=CHROMA_URL.replace("http://", "").split(":")[0],
                                 port=int(CHROMA_URL.split(":")[-1]))
    ids, docs, metas = fetch_source_docs(client)

    summary = []
    for v in requested:
        try:
            reindex(client, v, ids, docs, metas, force=args.force)
            summary.append({"variant": v.id, "status": "ok", "count": len(docs)})
        except Exception as e:
            summary.append({"variant": v.id, "status": f"erro: {e}", "count": 0})
            print(f"[{v.id}] FALHA: {e}", file=sys.stderr)

    print("\n=== resumo ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

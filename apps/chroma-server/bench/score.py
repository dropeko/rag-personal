"""
score.py — Calcula Recall@k, MRR, nDCG@10 e percentis de latência por variante,
e gera gráficos prontos para a apresentação.

Uso:
    python score.py --results results.csv --golden golden-set.csv --out reports/
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def recall_at_k(retrieved_ids: list[str], expected_id: str, k: int) -> int:
    return int(expected_id in retrieved_ids[:k])


def mrr(retrieved_ids: list[str], expected_id: str) -> float:
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid == expected_id:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], expected_id: str, k: int) -> float:
    # Relevância binária (1 se id == expected, 0 caso contrário)
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids[:k], start=1):
        if rid == expected_id:
            dcg += 1.0 / math.log2(i + 1)
    idcg = 1.0 / math.log2(2)  # ideal: relevante em posição 1
    return dcg / idcg if idcg > 0 else 0.0


def score_quality(results: pd.DataFrame, golden: pd.DataFrame) -> pd.DataFrame:
    # Para qualidade, usar apenas repeat=1 (a métrica não muda entre repeats)
    res = results[results["repeat"] == 1].copy()

    # Junta com expected_report_id
    res = res.merge(
        golden[["query_id", "expected_report_id"]],
        on="query_id",
        how="left",
    )
    res["expected_report_id"] = res["expected_report_id"].astype(str)
    res["retrieved_report_id"] = res["retrieved_report_id"].astype(str)

    summary_rows = []
    for variant, g in res.groupby("variant"):
        by_query = g.sort_values(["query_id", "rank"]).groupby("query_id")
        recalls5, recalls10, mrrs, ndcgs = [], [], [], []
        for qid, qg in by_query:
            retrieved = qg["retrieved_report_id"].tolist()
            expected = qg["expected_report_id"].iloc[0]
            recalls5.append(recall_at_k(retrieved, expected, 5))
            recalls10.append(recall_at_k(retrieved, expected, 10))
            mrrs.append(mrr(retrieved, expected))
            ndcgs.append(ndcg_at_k(retrieved, expected, 10))
        summary_rows.append({
            "variant": variant,
            "n_queries": len(recalls5),
            "recall@5": np.mean(recalls5),
            "recall@10": np.mean(recalls10),
            "mrr": np.mean(mrrs),
            "ndcg@10": np.mean(ndcgs),
        })
    return pd.DataFrame(summary_rows).sort_values("recall@5", ascending=False)


def score_latency(results: pd.DataFrame) -> pd.DataFrame:
    # Para latência, considera todos os repeats (rank=1 é suficiente — embed/search por query)
    res = results[results["rank"] == 1].copy()
    rows = []
    for variant, g in res.groupby("variant"):
        for op in ["embed_latency_ms", "search_latency_ms"]:
            vals = g[op].to_numpy()
            rows.append({
                "variant": variant,
                "operation": op.replace("_latency_ms", ""),
                "p50": float(np.percentile(vals, 50)),
                "p95": float(np.percentile(vals, 95)),
                "p99": float(np.percentile(vals, 99)),
                "mean": float(np.mean(vals)),
                "n": len(vals),
            })
    return pd.DataFrame(rows)


def plot_quality(summary: pd.DataFrame, out_dir: Path):
    sns.set_theme(style="whitegrid")
    metrics = ["recall@5", "recall@10", "mrr", "ndcg@10"]
    melted = summary.melt(id_vars="variant", value_vars=metrics,
                          var_name="metric", value_name="score")
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=melted, x="metric", y="score", hue="variant")
    ax.set_ylim(0, 1)
    ax.set_title("Qualidade de retrieval por variante de embedding")
    ax.set_ylabel("score (0–1)")
    plt.tight_layout()
    plt.savefig(out_dir / "quality.png", dpi=150)
    plt.close()


def plot_latency(lat: pd.DataFrame, out_dir: Path):
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, op in zip(axes, ["embed", "search"]):
        d = lat[lat["operation"] == op]
        melted = d.melt(id_vars="variant", value_vars=["p50", "p95", "p99"],
                        var_name="percentile", value_name="ms")
        sns.barplot(data=melted, x="variant", y="ms", hue="percentile", ax=ax)
        ax.set_title(f"Latência — {op}")
        ax.set_ylabel("ms")
        ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    plt.savefig(out_dir / "latency.png", dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.csv")
    parser.add_argument("--golden", default="golden-set.csv")
    parser.add_argument("--out", default="reports/")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(args.results)
    golden = pd.read_csv(args.golden)
    golden.rename(columns={golden.columns[0]: "question"}, inplace=True) if "question" not in golden.columns else None
    # Atribui query_id sequencial (mesma ordem do run-queries.ts)
    golden = golden.reset_index().rename(columns={"index": "query_id"})
    golden["query_id"] = golden["query_id"] + 1

    summary = score_quality(results, golden)
    latency = score_latency(results)

    summary.to_csv(out_dir / "summary.csv", index=False, float_format="%.4f")
    latency.to_csv(out_dir / "latency.csv", index=False, float_format="%.2f")

    plot_quality(summary, out_dir)
    plot_latency(latency, out_dir)

    print("\n=== Qualidade ===")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\n=== Latência (ms) ===")
    print(latency.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\nGráficos: {out_dir}/quality.png, {out_dir}/latency.png")


if __name__ == "__main__":
    main()

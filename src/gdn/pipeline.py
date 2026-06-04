from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .analysis import compute_graph_metrics, compute_sample_activation_metrics, compute_vertex_metrics
from .export import (
    export_figure,
    export_graph_summary,
    export_isolated_nodes,
    export_sample_metrics,
    export_vertex_metrics,
)
from .io import NETWORK_ORDER, discover_available_networks
from .plotting import plot_degree_vs_frequency, plot_spontaneous_vs_total


def summarize_run(skipped_networks: dict[str, list[str]], processed_networks: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for network_name in processed_networks:
        rows.append({"network": network_name, "status": "processed", "details": "all required inputs found"})
    for network_name, missing in skipped_networks.items():
        rows.append({"network": network_name, "status": "skipped", "details": f"missing: {', '.join(missing)}"})
    return pd.DataFrame(rows)


def process_network_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    vertex_metrics = compute_vertex_metrics(bundle)
    graph_metrics = compute_graph_metrics(vertex_metrics, bundle)
    sample_metrics = compute_sample_activation_metrics(bundle)

    export_vertex_metrics(vertex_metrics, bundle["results_dir"])
    export_isolated_nodes(vertex_metrics, bundle["results_dir"])
    export_graph_summary(graph_metrics, bundle["results_dir"])
    export_sample_metrics(sample_metrics, bundle["results_dir"], bundle["network_name"])

    figure1 = plot_degree_vs_frequency(vertex_metrics, bundle)
    export_figure(figure1, bundle["results_dir"], "figure1_degree_vs_frequency")

    figure2 = plot_spontaneous_vs_total(sample_metrics, bundle)
    export_figure(figure2, bundle["results_dir"], "figure2_spontaneous_vs_total")

    return {
        "network": bundle["network_name"],
        "label": bundle["network_label"],
        "results_dir": str(bundle["results_dir"]),
        "n_nodes": graph_metrics["n_nodes"],
        "n_edges": graph_metrics["n_edges"],
        "n_samples": graph_metrics["n_samples"],
        "distance_method": graph_metrics["distance_method"],
        "exports": [
            "vertex_metrics.csv",
            "isolated_nodes.csv",
            "graph_metrics_summary.json",
            "graph_metrics_summary.txt",
            "sample_activation_metrics.csv",
            "figure1_degree_vs_frequency.png",
            "figure1_degree_vs_frequency.pdf",
            "figure2_spontaneous_vs_total.png",
            "figure2_spontaneous_vs_total.pdf",
        ],
    }


def run_analysis(root: Path) -> dict[str, Any]:
    bundles, skipped_networks = discover_available_networks(root)
    processed: list[dict[str, Any]] = []

    for network_name in NETWORK_ORDER:
        bundle = bundles.get(network_name)
        if bundle is None:
            continue
        processed.append(process_network_bundle(bundle))

    return {
        "root": str(root),
        "processed": processed,
        "skipped": skipped_networks,
        "run_status": summarize_run(skipped_networks, [item["network"] for item in processed]),
    }

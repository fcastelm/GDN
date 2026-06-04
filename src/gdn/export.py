from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def export_vertex_metrics(vertex_metrics: pd.DataFrame, results_dir: Path) -> Path:
    output_path = results_dir / "vertex_metrics.csv"
    export_frame = vertex_metrics.loc[:, ["node_id", "name", "frequency", "in_degree", "out_degree"]]
    export_frame.to_csv(output_path, index=False)
    return output_path


def export_isolated_nodes(vertex_metrics: pd.DataFrame, results_dir: Path) -> Path:
    isolated_nodes = vertex_metrics.loc[
        (vertex_metrics["in_degree"] == 0) & (vertex_metrics["out_degree"] == 0),
        ["node_id", "name", "frequency"],
    ].copy()
    isolated_nodes = isolated_nodes.rename(columns={"node_id": "graph_index"})
    output_path = results_dir / "isolated_nodes.csv"
    isolated_nodes.to_csv(output_path, index=False)
    return output_path


def export_graph_summary(summary: dict[str, Any], results_dir: Path) -> tuple[Path, Path]:
    json_path = results_dir / "graph_metrics_summary.json"
    txt_path = results_dir / "graph_metrics_summary.txt"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    ordered_lines = [
        "Graph metrics summary",
        f"Network: {summary['network']}",
        f"Label: {summary['label']}",
        f"Nodes: {summary['n_nodes']}",
        f"Edges: {summary['n_edges']}",
        f"Samples: {summary['n_samples']}",
        f"Density: {summary['density']:.10f}",
        f"Maximum in-degree: {summary['max_in_degree']}",
        f"Mean in-degree: {summary['mean_in_degree']:.6f}",
        f"Maximum out-degree: {summary['max_out_degree']}",
        f"Mean out-degree: {summary['mean_out_degree']:.6f}",
        f"Isolated nodes: {summary['isolated_nodes']}",
        f"Orphan nodes (non-isolated, in-degree 0): {summary['orphan_nodes']}",
        f"Child-less nodes (non-isolated, out-degree 0): {summary['childless_nodes']}",
        f"Maximum diameter (directed reachable pairs): {summary['maximum_diameter']}",
        f"Mean diameter (directed reachable pairs): {summary['mean_diameter']:.6f}",
        f"Largest WCC size: {summary['largest_wcc_size']}",
        f"Largest WCC undirected diameter: {summary['largest_wcc_undirected_diameter']}",
        f"Distance method: {summary['distance_method']}",
    ]
    with txt_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(ordered_lines) + "\n")
    return json_path, txt_path


def export_sample_metrics(sample_metrics: pd.DataFrame, results_dir: Path, network_name: str) -> Path:
    output_path = results_dir / "sample_activation_metrics.csv"
    export_frame = sample_metrics.copy()
    if network_name == "N_Network":
        export_frame = export_frame.rename(
            columns={
                "spontaneous_active": "spontaneous_inactive",
                "total_active": "total_inactive",
            }
        )
    export_frame.to_csv(output_path, index=False)
    return output_path


def export_figure(figure: Figure, results_dir: Path, stem: str) -> tuple[Path, Path]:
    png_path = results_dir / f"{stem}.png"
    pdf_path = results_dir / f"{stem}.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return png_path, pdf_path

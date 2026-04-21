from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

try:
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import shortest_path
except ImportError:  # pragma: no cover - fallback path when scipy is unavailable
    csr_matrix = None
    shortest_path = None


REQUIRED_DATA_FILES = [
    "graph_file.adjlist",
    "test_frequencies.txt",
    "nodes.txt",
    "sample.txt",
    "names.csv",
]

NETWORK_ORDER = ["T_Network", "N_Network"]
NETWORK_SHORT_NAME = {"T_Network": "T", "N_Network": "N"}


def get_network_dir(root: Path, network_name: str) -> Path:
    return root / network_name


def get_data_dir(root: Path, network_name: str) -> Path:
    return get_network_dir(root, network_name) / "data"


def get_results_dir(root: Path, network_name: str) -> Path:
    results_dir = get_network_dir(root, network_name) / "result_files"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def validate_network_inputs(root: Path, network_name: str) -> list[str]:
    data_dir = get_data_dir(root, network_name)
    missing = [name for name in REQUIRED_DATA_FILES if not (data_dir / name).exists()]
    return missing


def parse_node_groups(nodes_path: Path) -> list[list[int]]:
    node_groups: list[list[int]] = []
    with nodes_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            tokens = stripped.replace(",", " ").split()
            try:
                node_groups.append([int(token) for token in tokens])
            except ValueError as exc:
                raise ValueError(f"No se pudo parsear nodes.txt en la línea {line_number}: {raw_line!r}") from exc
    return node_groups


def read_names(names_path: Path) -> list[str]:
    names = pd.read_csv(names_path, header=None).iloc[:, 0].astype(str).tolist()
    return names


def read_frequencies(frequencies_path: Path) -> list[float]:
    frequencies = pd.read_csv(frequencies_path, header=None).iloc[:, 0].astype(float).tolist()
    return frequencies


def read_sample_matrix(sample_path: Path) -> np.ndarray:
    matrix = np.loadtxt(sample_path, dtype=int)
    if matrix.ndim == 1:
        matrix = matrix.reshape(-1, 1)
    return matrix


def load_graph(adjlist_path: Path, expected_graph_nodes: list[int]) -> nx.DiGraph:
    graph = nx.read_adjlist(adjlist_path, nodetype=int, create_using=nx.DiGraph())
    graph.add_nodes_from(expected_graph_nodes)
    unknown_nodes = sorted(set(graph.nodes()) - set(expected_graph_nodes))
    if unknown_nodes:
        preview = unknown_nodes[:10]
        raise ValueError(
            "El grafo contiene nodos que no corresponden a índices válidos de vértices comprimidos. "
            f"Ejemplos: {preview}"
        )
    return graph


def load_network_bundle(root: Path, network_name: str) -> dict[str, Any]:
    missing = validate_network_inputs(root, network_name)
    if missing:
        raise FileNotFoundError(
            f"Faltan archivos requeridos en {network_name}/data: {', '.join(missing)}"
        )

    data_dir = get_data_dir(root, network_name)
    node_groups = parse_node_groups(data_dir / "nodes.txt")
    representative_original_ids = [group[0] for group in node_groups]
    names = read_names(data_dir / "names.csv")
    frequencies = read_frequencies(data_dir / "test_frequencies.txt")
    sample_matrix = read_sample_matrix(data_dir / "sample.txt")
    n_nodes = len(node_groups)
    graph_node_ids = list(range(n_nodes))
    graph = load_graph(data_dir / "graph_file.adjlist", graph_node_ids)

    if len(frequencies) != n_nodes:
        raise ValueError(
            f"{network_name}: test_frequencies.txt tiene {len(frequencies)} filas y nodes.txt tiene {n_nodes}."
        )
    if sample_matrix.shape[0] != n_nodes:
        raise ValueError(
            f"{network_name}: sample.txt tiene {sample_matrix.shape[0]} filas y nodes.txt tiene {n_nodes}."
        )

    if not representative_original_ids:
        raise ValueError(f"{network_name}: nodes.txt no contiene grupos válidos.")

    max_representative_id = max(representative_original_ids)
    if max_representative_id >= len(names):
        raise ValueError(
            f"{network_name}: names.csv tiene {len(names)} filas, pero nodes.txt referencia el índice original {max_representative_id}."
        )

    graph_names = [names[original_id] for original_id in representative_original_ids]

    row_to_node = graph_node_ids
    node_to_row = {node_id: row_index for row_index, node_id in enumerate(row_to_node)}
    if len(node_to_row) != len(row_to_node):
        raise ValueError(f"{network_name}: índices de vértice comprimido duplicados detectados.")

    return {
        "network_name": network_name,
        "network_label": NETWORK_SHORT_NAME.get(network_name, network_name),
        "data_dir": data_dir,
        "results_dir": get_results_dir(root, network_name),
        "graph": graph,
        "row_to_node": row_to_node,
        "node_to_row": node_to_row,
        "names": graph_names,
        "representative_original_ids": representative_original_ids,
        "node_groups": node_groups,
        "frequencies": np.asarray(frequencies, dtype=float),
        "sample_matrix": sample_matrix,
        "n_nodes": n_nodes,
        "n_samples": int(sample_matrix.shape[1]),
    }


def discover_available_networks(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    bundles: dict[str, dict[str, Any]] = {}
    skipped: dict[str, list[str]] = {}
    for network_name in NETWORK_ORDER:
        missing = validate_network_inputs(root, network_name)
        if missing:
            skipped[network_name] = missing
            continue
        try:
            bundles[network_name] = load_network_bundle(root, network_name)
        except Exception as exc:
            skipped[network_name] = [f"invalid input set: {exc}"]
    return bundles, skipped


def compute_vertex_metrics(bundle: dict[str, Any]) -> pd.DataFrame:
    graph: nx.DiGraph = bundle["graph"]
    row_to_node: list[int] = bundle["row_to_node"]
    names: list[str] = bundle["names"]
    frequencies: np.ndarray = bundle["frequencies"]

    vertex_metrics = pd.DataFrame(
        {
            "row_index": np.arange(len(row_to_node), dtype=int),
            "node_id": row_to_node,
            "representative_original_id": bundle["representative_original_ids"],
            "name": names,
            "frequency": frequencies,
            "in_degree": [graph.in_degree(node_id) for node_id in row_to_node],
            "out_degree": [graph.out_degree(node_id) for node_id in row_to_node],
        }
    )
    return vertex_metrics


def compute_graph_metrics(vertex_metrics: pd.DataFrame, bundle: dict[str, Any]) -> dict[str, Any]:
    graph: nx.DiGraph = bundle["graph"]
    total_degree = vertex_metrics["in_degree"] + vertex_metrics["out_degree"]
    isolated_mask = total_degree == 0
    orphan_mask = (vertex_metrics["in_degree"] == 0) & (~isolated_mask)
    childless_mask = (vertex_metrics["out_degree"] == 0) & (~isolated_mask)

    summary = {
        "network": bundle["network_name"],
        "label": bundle["network_label"],
        "n_nodes": int(graph.number_of_nodes()),
        "n_edges": int(graph.number_of_edges()),
        "n_samples": int(bundle["n_samples"]),
        "density": float(nx.density(graph)),
        "max_in_degree": int(vertex_metrics["in_degree"].max()),
        "mean_in_degree": float(vertex_metrics["in_degree"].mean()),
        "max_out_degree": int(vertex_metrics["out_degree"].max()),
        "mean_out_degree": float(vertex_metrics["out_degree"].mean()),
        "isolated_nodes": int(len(vertex_metrics[isolated_mask])),
        "orphan_nodes": int(len(vertex_metrics[orphan_mask])),
        "childless_nodes": int(len(vertex_metrics[childless_mask])),
    }
    summary.update(compute_distance_metrics(graph))
    return summary


def compute_distance_metrics(graph: nx.DiGraph) -> dict[str, Any]:
    if csr_matrix is not None and shortest_path is not None:
        return _compute_distance_metrics_scipy(graph)
    return _compute_distance_metrics_networkx(graph)


def _compute_distance_metrics_scipy(graph: nx.DiGraph) -> dict[str, Any]:
    assert csr_matrix is not None
    assert shortest_path is not None
    ordered_nodes = list(graph.nodes())
    node_to_index = {node_id: index for index, node_id in enumerate(ordered_nodes)}
    row_indices: list[int] = []
    col_indices: list[int] = []
    data: list[int] = []

    for source, target in graph.edges():
        row_indices.append(node_to_index[source])
        col_indices.append(node_to_index[target])
        data.append(1)

    adjacency = csr_matrix((data, (row_indices, col_indices)), shape=(len(ordered_nodes), len(ordered_nodes)))
    directed_distances = shortest_path(adjacency, directed=True, unweighted=True)
    finite_mask = np.isfinite(directed_distances) & (directed_distances > 0)

    if finite_mask.any():
        reachable_values = directed_distances[finite_mask]
        reachable_max = int(reachable_values.max())
        mean_reachable_distance = float(reachable_values.mean())
    else:
        reachable_max = 0
        mean_reachable_distance = 0.0

    weakly_connected_components = list(nx.weakly_connected_components(graph))
    largest_wcc_size = 0
    largest_wcc_undirected_diameter = 0
    if weakly_connected_components:
        largest_component_nodes = max(weakly_connected_components, key=len)
        largest_wcc_size = len(largest_component_nodes)
        if largest_wcc_size > 1:
            largest_indices = [node_to_index[node_id] for node_id in largest_component_nodes]
            undirected_distances = shortest_path(adjacency[largest_indices][:, largest_indices], directed=False, unweighted=True)
            finite_undirected = undirected_distances[np.isfinite(undirected_distances)]
            if finite_undirected.size:
                largest_wcc_undirected_diameter = int(finite_undirected.max())

    return {
        "maximum_diameter": int(reachable_max),
        "mean_diameter": float(mean_reachable_distance),
        "directed_reachable_diameter": int(reachable_max),
        "directed_mean_reachable_distance": float(mean_reachable_distance),
        "largest_wcc_size": int(largest_wcc_size),
        "largest_wcc_undirected_diameter": int(largest_wcc_undirected_diameter),
        "distance_method": "scipy_shortest_path",
    }


def _compute_distance_metrics_networkx(graph: nx.DiGraph) -> dict[str, Any]:
    reachable_count = 0
    reachable_sum = 0
    reachable_max = 0

    for source in graph.nodes():
        distances = nx.single_source_shortest_path_length(graph, source)
        finite_nonzero = [distance for target, distance in distances.items() if target != source]
        if not finite_nonzero:
            continue
        reachable_count += len(finite_nonzero)
        reachable_sum += sum(finite_nonzero)
        local_max = max(finite_nonzero)
        if local_max > reachable_max:
            reachable_max = local_max

    if reachable_count:
        mean_reachable_distance = reachable_sum / reachable_count
    else:
        mean_reachable_distance = 0.0

    weakly_connected_components = list(nx.weakly_connected_components(graph))
    largest_wcc_size = 0
    largest_wcc_undirected_diameter = 0
    if weakly_connected_components:
        largest_component_nodes = max(weakly_connected_components, key=len)
        largest_wcc_size = len(largest_component_nodes)
        undirected_subgraph = graph.subgraph(largest_component_nodes).to_undirected()
        if undirected_subgraph.number_of_nodes() > 1:
            largest_wcc_undirected_diameter = nx.diameter(undirected_subgraph)

    return {
        "maximum_diameter": int(reachable_max),
        "mean_diameter": float(mean_reachable_distance),
        "directed_reachable_diameter": int(reachable_max),
        "directed_mean_reachable_distance": float(mean_reachable_distance),
        "largest_wcc_size": int(largest_wcc_size),
        "largest_wcc_undirected_diameter": int(largest_wcc_undirected_diameter),
        "distance_method": "networkx_bfs_exact",
    }


def compute_sample_activation_metrics(bundle: dict[str, Any]) -> pd.DataFrame:
    graph: nx.DiGraph = bundle["graph"]
    sample_matrix: np.ndarray = bundle["sample_matrix"]
    row_to_node: list[int] = bundle["row_to_node"]
    node_to_row: dict[int, int] = bundle["node_to_row"]

    predecessor_rows: list[np.ndarray] = []
    for node_id in row_to_node:
        rows = [node_to_row[parent] for parent in graph.predecessors(node_id) if parent in node_to_row]
        predecessor_rows.append(np.asarray(rows, dtype=int))

    total_active: list[int] = []
    spontaneous_active: list[int] = []

    for sample_index in range(sample_matrix.shape[1]):
        active_mask = sample_matrix[:, sample_index].astype(bool)
        active_rows = np.flatnonzero(active_mask)
        spontaneous_count = 0
        for row_index in active_rows:
            parent_rows = predecessor_rows[row_index]
            if parent_rows.size == 0 or not active_mask[parent_rows].any():
                spontaneous_count += 1

        total_active.append(int(active_rows.size))
        spontaneous_active.append(int(spontaneous_count))

    return pd.DataFrame(
        {
            "sample_index": np.arange(sample_matrix.shape[1], dtype=int),
            "spontaneous_active": spontaneous_active,
            "total_active": total_active,
        }
    )


def plot_degree_vs_frequency(vertex_metrics: pd.DataFrame, bundle: dict[str, Any]) -> Figure:
    label = bundle["network_label"]
    figure, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    axes[0].scatter(vertex_metrics["frequency"], vertex_metrics["out_degree"] + 1, s=10, alpha=0.6, color="#1f77b4")
    axes[0].set_xlabel(f"freq{label}")
    axes[0].set_ylabel("1 + out-degree")
    axes[0].set_yscale("log")
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title(f"{label}-network")

    axes[1].scatter(vertex_metrics["frequency"], vertex_metrics["in_degree"] + 1, s=10, alpha=0.6, color="#1f77b4")
    axes[1].set_xlabel(f"freq{label}")
    axes[1].set_ylabel("1 + in-degree")
    axes[1].set_yscale("log")
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title(f"{label}-network")

    figure.suptitle(f"Degree vs frequency — {bundle['network_name']}", fontsize=14)
    return figure


def plot_spontaneous_vs_total(sample_metrics: pd.DataFrame, bundle: dict[str, Any]) -> Figure:
    label = bundle["network_label"]
    max_spontaneous = int(sample_metrics["spontaneous_active"].max()) if not sample_metrics.empty else 0
    max_total = int(sample_metrics["total_active"].max()) if not sample_metrics.empty else 0
    reference_max = max(max_spontaneous, 1)

    if reference_max <= 10:
        x_limit = reference_max + 1
    else:
        magnitude = 10 ** (len(str(reference_max)) - 1)
        x_limit = int(np.ceil(reference_max / magnitude) * magnitude)

    figure, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    axis.scatter(sample_metrics["spontaneous_active"], sample_metrics["total_active"], alpha=0.65, color="#1f77b4")
    diagonal_limit = max(x_limit, max_total)
    axis.plot([0, diagonal_limit], [0, diagonal_limit], "r--", linewidth=2, label="y = x")
    axis.set_xlabel(f"Spont. activ. {label}-genes")
    axis.set_ylabel(f"Total activ. {label}-genes")
    axis.grid(True, alpha=0.3)
    axis.legend()
    axis.set_xlim(0, x_limit)
    axis.set_title(f"Spontaneous vs total activations — {bundle['network_name']}")
    return figure


def export_vertex_metrics(vertex_metrics: pd.DataFrame, results_dir: Path) -> Path:
    output_path = results_dir / "vertex_metrics.csv"
    vertex_metrics.to_csv(output_path, index=False)
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


def export_sample_metrics(sample_metrics: pd.DataFrame, results_dir: Path) -> Path:
    output_path = results_dir / "sample_activation_metrics.csv"
    sample_metrics.to_csv(output_path, index=False)
    return output_path


def export_figure(figure: Figure, results_dir: Path, stem: str) -> tuple[Path, Path]:
    png_path = results_dir / f"{stem}.png"
    pdf_path = results_dir / f"{stem}.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return png_path, pdf_path


def summarize_run(skipped_networks: dict[str, list[str]], processed_networks: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for network_name in processed_networks:
        rows.append({"network": network_name, "status": "processed", "details": "all required inputs found"})
    for network_name, missing in skipped_networks.items():
        rows.append({"network": network_name, "status": "skipped", "details": f"missing: {', '.join(missing)}"})
    return pd.DataFrame(rows)

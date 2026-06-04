from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

try:
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import shortest_path
except ImportError:  # pragma: no cover - fallback path when scipy is unavailable
    csr_matrix = None
    shortest_path = None


def compute_vertex_metrics(bundle: dict[str, Any]) -> pd.DataFrame:
    graph: nx.DiGraph = bundle["graph"]
    row_to_node: list[int] = bundle["row_to_node"]
    names: list[str] = bundle["names"]
    frequencies: np.ndarray = bundle["frequencies"]

    return pd.DataFrame(
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
            undirected_distances = shortest_path(
                adjacency[largest_indices][:, largest_indices], directed=False, unweighted=True
            )
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

    mean_reachable_distance = (reachable_sum / reachable_count) if reachable_count else 0.0

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

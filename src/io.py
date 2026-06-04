from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

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
    return [name for name in REQUIRED_DATA_FILES if not (data_dir / name).exists()]


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
                raise ValueError(
                    f"Could not parse nodes.txt at line {line_number}: {raw_line!r}"
                ) from exc
    return node_groups


def read_names(names_path: Path) -> list[str]:
    return pd.read_csv(names_path, header=None).iloc[:, 0].astype(str).tolist()


def resolve_representative_names(
    names: list[str], representative_original_ids: list[int], network_name: str
) -> list[str]:
    if not representative_original_ids:
        raise ValueError(f"{network_name}: nodes.txt does not contain valid groups.")

    min_original_id = min(representative_original_ids)
    max_original_id = max(representative_original_ids)
    if min_original_id < 0:
        raise ValueError(f"{network_name}: nodes.txt contains negative original indices.")
    if max_original_id >= len(names):
        raise ValueError(
            f"{network_name}: names.csv has {len(names)} rows, but nodes.txt references original index "
            f"{max_original_id}. The full original gene list is required to resolve representative names."
        )

    return [names[original_id] for original_id in representative_original_ids]


def read_frequencies(frequencies_path: Path) -> list[float]:
    return pd.read_csv(frequencies_path, header=None).iloc[:, 0].astype(float).tolist()


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
            "The graph contains nodes that do not match valid compressed vertex indices. "
            f"Examples: {preview}"
        )
    return graph


def load_network_bundle(root: Path, network_name: str) -> dict[str, Any]:
    missing = validate_network_inputs(root, network_name)
    if missing:
        raise FileNotFoundError(f"Missing required files in {network_name}/data: {', '.join(missing)}")

    data_dir = get_data_dir(root, network_name)
    node_groups = parse_node_groups(data_dir / "nodes.txt")
    representative_original_ids = [group[0] for group in node_groups]
    names = read_names(data_dir / "names.csv")
    representative_names = resolve_representative_names(names, representative_original_ids, network_name)
    frequencies = read_frequencies(data_dir / "test_frequencies.txt")
    sample_matrix = read_sample_matrix(data_dir / "sample.txt")
    n_nodes = len(node_groups)
    graph_node_ids = list(range(n_nodes))
    graph = load_graph(data_dir / "graph_file.adjlist", graph_node_ids)

    if len(frequencies) != n_nodes:
        raise ValueError(
            f"{network_name}: test_frequencies.txt has {len(frequencies)} rows while nodes.txt has {n_nodes}."
        )
    if sample_matrix.shape[0] != n_nodes:
        raise ValueError(
            f"{network_name}: sample.txt has {sample_matrix.shape[0]} rows while nodes.txt has {n_nodes}."
        )

    row_to_node = graph_node_ids
    node_to_row = {node_id: row_index for row_index, node_id in enumerate(row_to_node)}
    if len(node_to_row) != len(row_to_node):
        raise ValueError(f"{network_name}: duplicate compressed vertex indices were detected.")

    return {
        "network_name": network_name,
        "network_label": NETWORK_SHORT_NAME.get(network_name, network_name),
        "data_dir": data_dir,
        "results_dir": get_results_dir(root, network_name),
        "graph": graph,
        "row_to_node": row_to_node,
        "node_to_row": node_to_row,
        "names": representative_names,
        "original_names": names,
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

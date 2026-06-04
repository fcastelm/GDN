from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure


def plot_degree_vs_frequency(vertex_metrics: pd.DataFrame, bundle: dict[str, object]) -> Figure:
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


def plot_spontaneous_vs_total(sample_metrics: pd.DataFrame, bundle: dict[str, object]) -> Figure:
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

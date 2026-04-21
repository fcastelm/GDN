# GDN

Reproducible network-analysis repository for the prostate cancer (**PRAD**) calculations associated with the GDN paper.

This project is designed to provide the data organization, notebook workflow, and exported metrics required to inspect the **T-network** and **N-network** analyses used in the study.

## Project purpose

The repository focuses on two directed gene deregulation networks:

- **T_Network**: tumor network
- **N_Network**: normal network

For each network, the repository stores:

- input data files in `data/`
- exported metrics and figures in `result_files/`

The current notebook is able to:

- validate whether the required input files exist
- process `T_Network` and `N_Network` automatically
- skip incomplete networks without failing
- compute vertex-level and graph-level metrics
- compute sample-level spontaneous activation statistics
- export figures and summary tables

## Repository structure

```text
GDN/
├── Get_Metrics.ipynb
├── gdn_analysis.py
├── requirements.txt
├── README.md
├── T_Network/
│   ├── data/
│   │   ├── graph_file.adjlist
│   │   ├── test_frequencies.txt
│   │   ├── nodes.txt
│   │   ├── sample.txt
│   │   └── names.csv
│   └── result_files/
└── N_Network/
    ├── data/
    │   ├── graph_file.adjlist
    │   ├── test_frequencies.txt
    │   ├── nodes.txt
    │   ├── sample.txt
    │   └── names.csv
    └── result_files/
```

## Input files

Each network folder (`T_Network` or `N_Network`) is expected to contain the following files inside `data/`.

### `graph_file.adjlist`

Directed graph stored in NetworkX adjacency-list format.

### `test_frequencies.txt`

Frequency value for each network vertex.

### `nodes.txt`

List of compressed graph nodes. Each row corresponds to one graph vertex. When several genes have identical behavior in the original binary matrix, they are compressed into one representative graph vertex. In those cases, multiple original gene indices may appear on the same line, and the first index is treated as the representative original gene used to recover the gene name.

### `sample.txt`

Binary matrix in which:

- each **row** corresponds to a graph vertex (gene)
- each **column** corresponds to a sample
- `1` means the gene is deregulated in that sample
- `0` means the gene is not deregulated in that sample

For `T_Network`, columns represent tumor samples. For `N_Network`, columns represent normal samples.

### `names.csv`

Gene names using Ensembl gene identifiers. For compressed nodes, the exported name corresponds to the first index listed in the matching row of `nodes.txt`.

## Output files

For each processed network, the notebook exports results into `result_files/`.

Expected outputs:

- `vertex_metrics.csv`
- `graph_metrics_summary.json`
- `graph_metrics_summary.txt`
- `isolated_nodes.csv`
- `sample_activation_metrics.csv`
- `figure1_degree_vs_frequency.png`
- `figure1_degree_vs_frequency.pdf`
- `figure2_spontaneous_vs_total.png`
- `figure2_spontaneous_vs_total.pdf`

## Metrics currently computed

### Vertex-level metrics

For each node:

- graph index
- representative original gene index
- gene name
- frequency
- in-degree
- out-degree

### Graph-level metrics

- number of nodes
- number of edges
- density
- maximum in-degree
- mean in-degree
- maximum out-degree
- mean out-degree
- isolated nodes
- orphan nodes (non-isolated nodes with in-degree `0`)
- child-less nodes (non-isolated nodes with out-degree `0`)
- directed reachable diameter
- directed mean reachable distance
- largest weakly connected component size
- largest weakly connected component undirected diameter

### Isolated-node export

For each processed network, the analysis also exports `isolated_nodes.csv`, containing:

- graph index
- gene name
- frequency

Only nodes with both in-degree `0` and out-degree `0` are included in this file.

### Sample-level metrics

For each sample:

- total active genes
- spontaneously active genes

A gene is counted as **spontaneously active** when it is active in a sample and none of its parent nodes are active in that same sample.

## Environment setup

Create a Python environment and install the dependencies:

```bash
pip install -r requirements.txt
```

If you prefer using a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## How to run

Open the notebook:

```bash
jupyter notebook Get_Metrics.ipynb
```

or:

```bash
jupyter lab Get_Metrics.ipynb
```

Then run the cells in order.

The notebook will:

1. detect which network folders are complete
2. process all complete networks
3. skip incomplete ones
4. export all metrics and figures automatically

# GDN

This is the official repository associated to the paper [N-Gene and T-Gene Desregulation Networks: A data-driven causal framework for the analysis of gene interventions in cancer](https://www.biorxiv.org/content/10.1101/2023.12.28.573550v2).

**Background:** The construction of realistic gene regulatory networks is currently hindered by the complex, often redundant, combinatorial and multi-layered nature of gene interdependencies, the limited availability of functional annotations, and the intrinsic shortcomings of co-expression-based approaches. Here, we introduce Gene Deregulation Networks (GDNs), a new structure in which linked genes indicate that an expression deregulation in one is likely to propagate to the other. GDNs are inferred directly from gene expression data using a probabilistic theory of causation, without requiring prior functional annotation or other domain knowledge.

**Methods:** Using highly specific tissue markers—N-genes specifically expressed in normal tissues and T-genes specifically expressed in tumors—we construct separate GDNs for normal and tumor tissues. Data are obtained from TCGA RNA-Seq profiles of bulk tumor and normal tissue samples across multiple cancer localizations. GDN links are preliminarily identified via a statistical test of causal sufficiency between gene expression deregulation events, and then reassessed as spurious or redundant using additional causal criteria. A simple scheme based on the GDNs is implemented in order to describe the evolution dynamics.

**Results:** The T-GDN in prostate adenocarcinoma comprises 6138 genes and 102362 directed edges (0.27% of possible connections). Genes with low expression deregulation frequency (< 0.2) exhibit high out-degrees, indicating high deregulation potential, while high-frequency genes (> 0.4) show high in-degrees, suggesting they are convergence points of deregulation cascades. EPHA10 (frequency 0.74, in-degree 182) and ENSG00000275479 (out-degree 209) represent these extremes. The N-GDN contains 1097 genes and 4984 edges, featuring compressed nodes reflecting the multistep nature of somatic evolution. Analysis of tumor samples reveals that early-stage tumors rely primarily on spontaneous gene activations, while advanced tumors exhibit extensive cascade-driven deregulation. Preliminary simulations show qualitative agreement with experiments on gene knockdown in tumor cellular lines.

**Conclusions:** GDNs provide a robust framework to understand cancer progression through deregulation cascades. The separation into N and T networks, connected by NT-genes, i.e. genes common to both networks, offers a systematic basis for modeling carcinogenesis and the possible outcomes of therapeutic interventions.

The paper is based on the construction of the causal networks described by J. P. Gomez in his Diploma Thesis, whose algorithm was used to obtain the tissue-specific networks included in the paper.

This repository provides the reproducible network-analysis workflow and exported metrics required to inspect the **T_Network** and **N_Network** analyses for prostate adenocarcinoma (**PRAD**) used in the study.

## Project purpose

The repository focuses on two directed gene deregulation networks:

- **T_Network**: tumor network
- **N_Network**: normal network

For each network, the repository stores:

- input data files in `data/`
- exported metrics and figures in `result_files/`

The `result_files/` directories are intentionally versioned in this repository. They are the published, reproducible outputs generated from the current input data and analysis workflow, so readers can inspect the exported tables and figures directly without rerunning the notebook first.

The current notebook is able to:

- validate whether the required input files exist
- process `T_Network` and `N_Network` automatically
- skip incomplete networks without failing
- compute vertex-level and graph-level metrics
- compute sample-level spontaneous activation statistics
- export figures and summary tables

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

These files are committed to the repository as analysis outputs, not temporary artifacts. Re-running the notebook may regenerate them, but the checked-in versions represent the current published outputs associated with this project state.

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

- graph node identifier
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

- `T_Network`: total active genes and spontaneously active genes
- `N_Network`: total inactive genes and spontaneously inactive genes

A gene is counted as **spontaneously active** when it is active in a sample and none of its parent nodes are active in that same sample. In the exported `N_Network` table, the corresponding columns are labeled as inactive metrics to match the interpretation used for the normal network outputs.

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

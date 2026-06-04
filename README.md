# GDN

This is the official repository associated to the paper [N-Gene and T-Gene Desregulation Networks: A data-driven causal framework for the analysis of gene interventions in cancer](https://www.biorxiv.org/content/10.1101/2023.12.28.573550v2).

**Background:** Current gene regulatory networks (GRNs) are limited by incomplete functional annotation and the difficulty of inferring true causal relationships from expression data. Here we introduce Gene Deregulation Networks (GDNs), a new structure in which a directed link from gene C to gene E indicates that a deregulation of C makes a deregulation of E more probable. GDNs are inferred purely from expression data using a probabilistic theory of causation, without requiring any prior biological knowledge.

**Methods:** Using previously defined N- and T-genes with exclusive expression intervals for normal tissue and tumors, respectively, we construct separate GDNs for normal and for tumor samples. Data are TCGA RNA-Seq bulk profiles from five cancer types. Links are identified via the Loevinger coefficient and pruned with Reichenbach-type and Mokken tests. We then project each sample onto its corresponding GDN to visualise the exact deregulation cascades that have occurred. Finally, we define a simple deterministic dynamics: spontaneous evolution follows the direction of the GDN edges; interventions (e.g., gene knockdown) acting against spontaneous evolution induce cascades along the reversed network.

**Results:** In prostate adenocarcinoma, the T-GDN contains 6138 genes and 102362 directed edges (0.27% of all possible). Genes with low deregulation frequency (< 0.2) have high out-degrees (e.g., ENSG00000275479, out-degree 209), suggesting they act as upstream regulators. High-frequency genes (> 0.4) have high in-degrees (e.g., EPHA10, in-degree 182), indicating they are convergence points. Projecting tumor samples onto the T-GDN reveals that early tumors rely mostly on spontaneous T-gene activations, whereas advanced tumors show wide, branching cascades. Simulated knockdown of EPHA10 and of an 8-gene panel illustrates how the network topology determines whether an intervention can be resisted by the tumor. A reported experiment (POM121 knockdown in two prostate cancer cell lines) qualitatively confirms the predicted directionality of cascades (chi-squared p-value ~ 10⁻5).

**Conclusions:** GDNs provide a robust, scalable, and annotation-free framework to understand cancer onset and progression. Their two key advantages over traditional GRNs are: (1) by projecting any sample onto the GDN, one can visualize exactly which deregulation cascades have taken place; (2) modeling spontaneous evolution or the effect of gene interventions becomes almost trivial—simply follow the edges (for spontaneous) or the reversed edges (for forced changes). The separation into N- and T-GDNs, connected by NT-genes, offers a systematic basis for studying carcinogenesis and designing targeted therapies. As detailed in a companion paper, the framework generates specific, testable predictions for RNA-based therapeutic interventions.

The paper is based on the construction of the causal networks described by J. P. Gomez in his Diploma Thesis, whose algorithm was used to obtain the tissue-specific networks included in the paper.

This repository provides the reproducible network-analysis workflow and exported metrics required to inspect the **T_Network** and **N_Network** analyses for prostate adenocarcinoma (**PRAD**) used in the study.

## Project purpose

The repository focuses on two directed gene deregulation networks:

- **T_Network**: tumor network
- **N_Network**: normal network

For each network, the repository stores:

- input data files in `data/`
- exported metrics and figures in `result_files/`

The `result_files/` directories are intentionally versioned in this repository. They are the published, reproducible outputs generated from the current input data and analysis workflow, so readers can inspect the exported tables and figures directly without rerunning the analysis first.

The repository now separates the batch workflow from the exploration workflow:

- `scripts/run_analysis.py` is the primary executable entrypoint for reproducible exports
- `src/` contains the reusable analysis package modules directly at the package root
- `notebooks/Explore_GDN_Results.ipynb` is a secondary notebook for visual inspection of generated outputs

Primary script capabilities:

- validate whether the required input files exist
- process `T_Network` and `N_Network` automatically
- skip incomplete networks without failing the whole run
- compute vertex-level and graph-level metrics
- compute sample-level spontaneous activation statistics
- export figures and summary tables

## Repository structure

```text
GDN/
├── README.md
├── requirements.txt
├── scripts/
│   └── run_analysis.py
├── src/
│   ├── __init__.py
│   ├── analysis.py
│   ├── export.py
│   ├── io.py
│   ├── pipeline.py
│   └── plotting.py
├── notebooks/
│   └── Explore_GDN_Results.ipynb
├── T_Network/
└── N_Network/
```

## Input files

Each network folder (`T_Network` or `N_Network`) is expected to contain the following files inside `data/`.

### `graph_file.adjlist`

Directed graph stored in NetworkX adjacency-list format.

### `test_frequencies.txt`

Frequency value for each network vertex. Row `i` corresponds to graph vertex `i`.

### `nodes.txt`

List of compressed graph nodes. Each row corresponds to one graph vertex. When several genes have identical behavior in the original binary matrix, they are compressed into one representative graph vertex. In those cases, multiple original gene indices may appear on the same line. The first value on each row is the representative original gene index used to recover the displayed gene name from the full `names.csv` list.

### `sample.txt`

Binary matrix in which:

- each **row** corresponds to a graph vertex (gene)
- each **column** corresponds to a sample
- `1` means the gene is deregulated in that sample
- `0` means the gene is not deregulated in that sample

For `T_Network`, columns represent tumor samples. For `N_Network`, columns represent normal samples. Row `i` must refer to the same graph vertex as row `i` in `nodes.txt` and `test_frequencies.txt`.

### `names.csv`

Full original gene-order list using Ensembl gene identifiers, one original gene per row and no header. This file is not aligned to compressed graph vertices. Instead, the analysis resolves each vertex name through the representative original index stored as the first value of the corresponding `nodes.txt` row.

## Output files

For each processed network, the script exports results into `result_files/`.

These files are committed to the repository as analysis outputs, not temporary artifacts. Re-running the script may regenerate them, but the checked-in versions represent the current published outputs associated with this project state.

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

Run the primary batch workflow from the repository root:

```bash
python scripts/run_analysis.py
```

The script will:

1. detect which network folders are complete
2. process all complete networks
3. skip incomplete ones
4. export all metrics and figures automatically
5. print a concise run summary

## Notebook exploration workflow

After the script has generated or refreshed the outputs, open the notebook for visual exploration:

```bash
jupyter notebook notebooks/Explore_GDN_Results.ipynb
```

or:


```bash
jupyter lab notebooks/Explore_GDN_Results.ipynb
```

The notebook is intentionally focused on:

1. inspecting exported summaries
2. previewing CSV outputs
3. displaying committed figures inline

It is not the primary documented execution path for batch exports.

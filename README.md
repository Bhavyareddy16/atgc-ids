# ATGC-MACIDS: Adaptive Trust Graph Consensus Multi-Agent Intrusion Detection System

[![Research Status](https://img.shields.io/badge/Research-IEEE%20TDSC%2FTIFS%20Ready-success?style=for-the-badge)](https://github.com/Bhavyareddy16/atgc-ids)
[![Python Version](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)](https://www.python.org/)
[![GNN Stack](https://img.shields.io/badge/PyG-PyTorch%20Geometric-orange?style=for-the-badge)](https://pytorch-geometric.com/)

An implementation of the **ATGC-MACIDS** (Adaptive Trust Graph Consensus Multi-Agent Intrusion Detection System) framework, centered around the **Adaptive Trust Graph Consensus Optimization (ATGCO)** algorithm. 

This repository contains the complete end-to-end dataset preprocessing, Dynamic Temporal Graph Construction, Hierarchical Multi-Agent Encoders, Dynamic Trust Evolution, Graph Episodic Memory, Differentiable Graph Consensus Optimization, Open-Set Zero-Day Detection, Autonomous Response Agents, and an **Interactive Glassmorphic Neon Web Dashboard** for pipeline simulation.

---

## 📐 Algorithmic Overview & Mathematical Formulation

The core contribution of this work, **ATGCO**, dynamically evolves trust values for hosts, routes messages via trust-modulated self-attention, and solves a multi-objective consensus relaxation problem:

$$z^* = \underset{z}{\text{argmin}} \sum_i T_i \|z_i - x_i\|^2 + \lambda \sum_{i,j} A_{ij} \|z_i - z_j\|^2$$

Where:
- $T_i \in [0, 1]$ represents the evolved host trust score from the **Dynamic Trust Evolution Network (DTEN)**.
- $x_i$ represents the raw classification logits from the **Trust-aware Graph Transformer (TAGT)**.
- $A_{ij}$ represents adjacent graph links.
- $z_i$ represents the consensus threat logits solved dynamically in under 5 iterations via a parallelized Jacobi solver.

---

## 📁 Repository Structure

```text
atgc-macids/
├── preprocessing/          # Part 1: Tabular data loading, cleaning & scaling
│   ├── clean.py
│   └── normalization.py
├── graph_builder/          # Part 2: Chronological graph snapshot constructors
│   ├── dynamic_graph.py
│   └── dynamic_graph_cicids.py
├── agents/                 # Part 3: Packet, Flow, Host Encoders & Response Agents
│   ├── encoder.py
│   ├── packet_agent.py
│   ├── flow_agent.py
│   ├── host_agent.py
│   └── response_agent.py
├── trust/                  # Part 4: Dynamic Trust Evolution Network (DTEN)
│   └── dten.py
├── memory/                 # Part 5: Graph Episodic Memory (GEM)
│   └── graph_memory.py
├── transformer/            # Part 6: Trust-modulated Graph Transformer (TAGT)
│   └── trust_graph_transformer.py
├── consensus/              # Part 7: Jacobi Graph Consensus Solver (GCO)
│   └── graph_consensus.py
├── models/                 # Part 8: Unified ATGCO Model Assembly
│   └── atgc_macids.py
├── losses/                 # Part 9: Multi-Objective Loss Formulation
│   └── multi_objective.py
├── trainer/                # Part 10: Sequential Graph Snapshot Training Engine
│   └── train_engine.py
├── explainability/         # Part 11: Explainability attributions (plots generated here)
│   ├── plots/
│   │   ├── consensus_convergence.png
│   │   └── feature_saliency.png
│   ├── shap_explainer.py
│   └── visualization.py
├── experiments/            # Part 12: Ablations and baseline models evaluations
│   ├── run_experiments.py  # Master evaluation suite
│   ├── baseline_compare.py
│   └── ablation.py
├── frontend/               # Interactive Neon Cybersecurity Dashboard
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── feature_saliency.png
│   └── consensus_convergence.png
├── tests/                  # End-to-end differentiable execution unit tests
│   └── test_components.py
├── .gitignore              # Ignores heavy data, pickles, and models
└── README.md
```

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites & Dependencies
Ensure your environment has Python 3.11+ and the required deep learning packages installed:
```bash
pip install torch torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric scikit-learn pandas numpy tabulate
```

### 2. Run Verification Unit Tests
To verify mathematical shape flow, GCO convergence, SIEM response alerts, and backpropagation gradients, run:
```bash
PYTHONPATH=. python3 tests/test_components.py
```
*This command runs in seconds and saves the explainability saliency and convergence plots under `explainability/plots/`.*

### 3. Run the Benchmark & Ablation Experiments
To train the unified ATGCO model, evaluate standard baselines (Random Forest, Gradient Boosting, CNN, GCN, GAT), and execute GNN ablations, run:
```bash
PYTHONPATH=. python3 experiments/run_experiments.py
```
*Evaluates performance metrics (F1-score, False Positive Rate, and Latency) on the real UNSW-NB15 dataset and validates schema compatibility on the synthetic CICIDS2017-style pipeline.*

---

## 💻 Interactive Cybersecurity Dashboard

To visually demonstrate runtime trust propagation, alert overrides, and zero-day mitigations, an interactive frontend dashboard is provided.

### Dashboard Features
- **SVG Topology Graph**: Dynamic hosts (nodes) glow color-coded based on active trust values (Cyan/Green for healthy, Orange for suspected anomalies, Magenta/Red for isolated hosts).
- **Interactive Host Inspector**: Click any router, switch, server, or client node to view its logits, trust score ($T_i$), and manually **Isolate Host** or **Reset Trust**.
- **Attack Simulation**: Trigger an intrusion on a random node to watch GCO consensus relaxation and autonomous SIEM containment rules trigger in real-time.
- **Explainability Tab**: View the gradient feature saliency rankings and Jacobi convergence error.

### How to Run:
Navigate to the `frontend/` folder and start a local HTTP server:
```bash
cd frontend
python3 -m http.server 8000
```
Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)**.
*(Alternatively, you can simply double-click `index.html` inside the unzipped `frontend` folder to open it natively without a server.)*

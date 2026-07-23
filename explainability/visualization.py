import os
import torch
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import torch.nn.functional as F

def plot_consensus_convergence(consensus_layer, x, edge_index, trust, save_path):
    """
    Plots the convergence of node predictions toward consensus across iterations.
    """
    print("Generating consensus convergence plot...")
    N = x.size(0)
    row, col = edge_index
    
    # Track variance of representation at each iteration step
    variances = []
    
    z = x.clone()
    # Manual Jacobi loop to track convergence metrics
    for step in range(consensus_layer.num_iterations + 1):
        # Calculate local difference from consensus (mean distance between neighbors)
        if len(row) > 0:
            diff = torch.norm(z[row] - z[col], p=2, dim=-1).mean().item()
        else:
            diff = 0.0
        variances.append(diff)
        
        # Iteration update step
        if step < consensus_layer.num_iterations:
            ones = torch.ones_like(row, dtype=torch.float32, device=x.device)
            deg = torch.zeros(N, dtype=torch.float32, device=x.device)
            deg.index_add_(0, row, ones)
            
            trust_expanded = trust.unsqueeze(1)
            deg_expanded = deg.unsqueeze(1)
            
            neighbor_sum = torch.zeros_like(z)
            neighbor_sum.index_add_(0, row, z[col])
            
            numerator = trust_expanded * x + 2.0 * consensus_layer.lmbda * neighbor_sum
            denominator = trust_expanded + 2.0 * consensus_layer.lmbda * deg_expanded + consensus_layer.eps
            z = numerator / denominator
            
    plt.figure(figsize=(6, 4))
    plt.plot(range(len(variances)), variances, marker='o', color='#1f77b4', linewidth=2)
    plt.title("ATGCO Consensus Convergence Curve")
    plt.xlabel("Iteration step (k)")
    plt.ylabel("Mean Neighbor Representation Distance")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Consensus convergence plot saved to: {save_path}")

def plot_trust_evolution(trust_history, node_idx_to_track, save_path):
    """
    Plots the trust scores of selected nodes over time snapshots.
    trust_history: List of dicts mapping global node index -> trust score
    """
    print("Generating trust evolution plot...")
    plt.figure(figsize=(8, 4))
    
    steps = range(len(trust_history))
    
    for node_idx in node_idx_to_track:
        y_vals = []
        for step_data in trust_history:
            y_vals.append(step_data.get(node_idx, 0.5)) # Default to neutral trust if not in snapshot
            
        plt.plot(steps, y_vals, label=f"Node/Flow Agent {node_idx}", marker='x', alpha=0.8)
        
    plt.title("Dynamic Trust Evolution Over Snapshots (DTEN)")
    plt.xlabel("Time Step / Snapshot Index")
    plt.ylabel("Trust Score (T_i)")
    plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Trust evolution plot saved to: {save_path}")

def compute_and_plot_saliency(model, x, edge_index, trust, feature_names, save_path):
    """
    Computes gradient-based saliency (feature importance) for the model's predictions.
    """
    print("Generating feature saliency plot...")
    model.eval()
    
    # Detach trust scores to avoid autograd graph reuse issues
    trust = trust.detach()
    
    # Enable gradients on input x
    x_input = x.clone().detach().requires_grad_(True)
    
    # Run model forward pass
    outputs = model(x_input, edge_index, trust)
    logits = outputs['logits_consensus']
    
    # Take max logit across nodes and backpropagate
    loss = logits.sum()
    loss.backward()
    
    # Saliency is the absolute value of the input gradients
    saliency = torch.abs(x_input.grad).mean(dim=0).cpu().numpy()
    
    # Find top 15 features
    top_indices = np.argsort(saliency)[-15:]
    top_features = [feature_names[i] for i in top_indices]
    top_scores = saliency[top_indices]
    
    plt.figure(figsize=(10, 5))
    plt.barh(range(len(top_scores)), top_scores, color='#2ca02c', alpha=0.8)
    plt.yticks(range(len(top_scores)), top_features)
    plt.title("Gradient-based Feature Saliency (ATGC-MACIDS)")
    plt.xlabel("Attribution Score Magnitude")
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saliency plot saved to: {save_path}")

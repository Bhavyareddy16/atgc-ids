import torch
import torch.nn as nn
from torch_geometric.utils import scatter

class GraphConsensusLayer(nn.Module):
    """
    Graph Consensus Optimization (GCO) Layer.
    Solves the consensus optimization problem:
    z* = argmin_z sum_i T_i ||z - x_i||^2 + lambda sum_{i,j} A_{ij} ||z_i - z_j||^2
    
    Using a differentiable Jacobi iterative solver:
    z_i^{(k+1)} = (T_i * x_i + 2 * lambda * sum_j A_{ij} z_j^{(k)}) / (T_i + 2 * lambda * D_i + eps)
    """
    def __init__(self, lmbda=0.5, num_iterations=5, eps=1e-6):
        super(GraphConsensusLayer, self).__init__()
        self.lmbda = lmbda
        self.num_iterations = num_iterations
        self.eps = eps
        
    def forward(self, x, edge_index, trust):
        """
        Args:
            x (Tensor): [N, num_classes/emb_dim] - Local decision logits or embeddings
            edge_index (Tensor): [2, E] - Graph adjacency
            trust (Tensor): [N] - Dynamic node trust scores in [0, 1]
            
        Returns:
            z (Tensor): [N, num_classes/emb_dim] - Consensus-aligned representations
        """
        N = x.size(0)
        row, col = edge_index
        
        # 1. Compute node degrees D_i
        # We assume A_ij = 1 (unweighted topology) or we can scale adjacency by trust: A_ij = trust_j
        # Let's use simple unweighted adjacency first, scaled by lambda
        ones = torch.ones_like(row, dtype=torch.float32, device=x.device)
        deg = scatter(ones, row, dim=0, dim_size=N, reduce='sum') # [N]
        
        # Resqueeze tensors for broadcasting
        trust_expanded = trust.unsqueeze(1) # [N, 1]
        deg_expanded = deg.unsqueeze(1)     # [N, 1]
        
        # 2. Iterative Jacobi updates
        z = x.clone()
        for _ in range(self.num_iterations):
            # Sum of neighbor embeddings S_i = sum_j A_{ij} z_j
            neighbor_sum = scatter(z[col], row, dim=0, dim_size=N, reduce='sum') # [N, emb_dim]
            
            # Jacobi iteration step
            numerator = trust_expanded * x + 2.0 * self.lmbda * neighbor_sum
            denominator = trust_expanded + 2.0 * self.lmbda * deg_expanded + self.eps
            
            z = numerator / denominator
            
        return z

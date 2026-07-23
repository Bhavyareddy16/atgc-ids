import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import softmax

class TrustGraphTransformerConv(MessagePassing):
    """
    Custom Trust-Aware Graph Transformer Convolutional Layer.
    Attention logits between node i and neighbor j are modulated by node j's trust score.
    """
    def __init__(self, in_channels, out_channels, heads=4, dropout=0.1):
        # We aggregate messages using sum (softmax handles normalisation)
        super(TrustGraphTransformerConv, self).__init__(aggr='add', node_dim=0)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.dropout = dropout
        
        assert out_channels % heads == 0, f"out_channels ({out_channels}) must be divisible by heads ({heads})"
        self.head_dim = out_channels // heads
        
        # Query, Key, and Value linear layers
        self.lin_q = nn.Linear(in_channels, out_channels, bias=True)
        self.lin_k = nn.Linear(in_channels, out_channels, bias=True)
        self.lin_v = nn.Linear(in_channels, out_channels, bias=True)
        
        # Skip connection & output projection
        self.lin_skip = nn.Linear(in_channels, out_channels, bias=True)
        self.lin_out = nn.Linear(out_channels, out_channels)
        
        self.reset_parameters()
        
    def reset_parameters(self):
        nn.init.xavier_uniform_(self.lin_q.weight)
        nn.init.xavier_uniform_(self.lin_k.weight)
        nn.init.xavier_uniform_(self.lin_v.weight)
        nn.init.xavier_uniform_(self.lin_skip.weight)
        nn.init.xavier_uniform_(self.lin_out.weight)
        
    def forward(self, x, edge_index, trust):
        """
        Args:
            x (Tensor): [N, in_channels] - Node representations
            edge_index (Tensor): [2, E] - Graph adjacency
            trust (Tensor): [N] - Dynamic node trust scores in [0, 1]
            
        Returns:
            out (Tensor): [N, out_channels] - Updated node representations
        """
        # 1. Project to Query, Key, Value
        # Shape: [N, heads, head_dim]
        q = self.lin_q(x).view(-1, self.heads, self.head_dim)
        k = self.lin_k(x).view(-1, self.heads, self.head_dim)
        v = self.lin_v(x).view(-1, self.heads, self.head_dim)
        
        # 2. Perform message propagation
        # Pass Query, Key, Value, trust, and index mappings
        out = self.propagate(edge_index, q=q, k=k, v=v, trust=trust, size=None)
        
        # 3. Reshape and project outputs
        out = out.view(-1, self.out_channels)
        out = self.lin_out(out)
        
        # Add skip connection
        out = out + self.lin_skip(x)
        return out
        
    def message(self, q_i, k_j, v_j, trust_j, index, ptr, size_i):
        """
        q_i: Queries of target nodes [E, heads, head_dim]
        k_j: Keys of source nodes [E, heads, head_dim]
        v_j: Values of source nodes [E, heads, head_dim]
        trust_j: Trust score of source nodes [E]
        index: Target node index for each edge [E]
        """
        # Compute scaled dot-product attention logits
        # dot_product shape: [E, heads]
        dot_product = (q_i * k_j).sum(dim=-1) / (self.head_dim ** 0.5)
        
        # Compute softmax over neighbors for each target node
        alpha = softmax(dot_product, index, ptr, num_nodes=size_i) # [E, heads]
        
        # Modulate attention weights by the trust score of the sender node (trust_j)
        # trust_j shape is [E], unsqueeze to [E, 1] to broadcast across attention heads
        alpha_trust = alpha * trust_j.unsqueeze(1)
        
        # Re-normalize trust-weighted attention weights
        # Avoid division by zero by adding epsilon
        sum_neighbor_alpha = torch.zeros((size_i, self.heads), dtype=alpha_trust.dtype, device=alpha_trust.device)
        sum_neighbor_alpha.index_add_(0, index, alpha_trust)
        
        # Map target sums back to edges
        sum_edge = sum_neighbor_alpha[index] # [E, heads]
        alpha_normalized = alpha_trust / torch.clamp(sum_edge, min=1e-6)
        
        # Apply dropout to attention coefficients
        alpha_dropout = F.dropout(alpha_normalized, p=self.dropout, training=self.training)
        
        # Shape: [E, heads, head_dim]
        return alpha_dropout.unsqueeze(-1) * v_j

class TrustGraphTransformer(nn.Module):
    """
    Multi-layer Trust-Aware Graph Transformer model.
    """
    def __init__(self, in_channels, hidden_channels, out_channels, num_layers=2, heads=4, dropout=0.1):
        super(TrustGraphTransformer, self).__init__()
        self.layers = nn.ModuleList()
        
        # Input layer
        self.layers.append(TrustGraphTransformerConv(in_channels, hidden_channels, heads, dropout))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.layers.append(TrustGraphTransformerConv(hidden_channels, hidden_channels, heads, dropout))
            
        # Output layer
        if num_layers > 1:
            self.layers.append(TrustGraphTransformerConv(hidden_channels, out_channels, heads, dropout))
        else:
            self.layers[0] = TrustGraphTransformerConv(in_channels, out_channels, heads, dropout)
            
        self.dropout = dropout
        
    def forward(self, x, edge_index, trust):
        """
        Args:
            x (Tensor): [N, in_channels] - Input features
            edge_index (Tensor): [2, E] - Graph adjacency
            trust (Tensor): [N] - Node trust scores
            
        Returns:
            x (Tensor): [N, out_channels] - Encoded graph representation
        """
        for i, layer in enumerate(self.layers):
            x = layer(x, edge_index, trust)
            if i < len(self.layers) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        return x

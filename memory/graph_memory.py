import torch
import torch.nn as nn
import torch.nn.functional as F

class GraphEpisodicMemory(nn.Module):
    """
    Graph Episodic Memory (GEM) that stores graph-level experiences.
    Each experience consists of pooled neighborhood subgraph embeddings,
    average neighbor trust scores, and anomaly decisions/labels.
    Retrieval is based on subgraph embedding similarity.
    """
    def __init__(self, embedding_dim=128, capacity=1000, update_threshold=0.85):
        super(GraphEpisodicMemory, self).__init__()
        self.embedding_dim = embedding_dim
        self.capacity = capacity
        self.update_threshold = update_threshold
        
        # Buffers to store experience representations
        # Using register_buffer so they are saved with the state_dict and moved to the correct device
        self.register_buffer('memory_embeddings', torch.zeros((capacity, embedding_dim), dtype=torch.float32))
        self.register_buffer('memory_labels', torch.zeros((capacity,), dtype=torch.long))
        self.register_buffer('memory_trusts', torch.zeros((capacity,), dtype=torch.float32))
        self.register_buffer('memory_filled', torch.zeros((capacity,), dtype=torch.bool))
        
        # Pointer to the next position to write (circular buffer)
        self.register_buffer('write_ptr', torch.zeros((1,), dtype=torch.long))
        
    def _compute_subgraph_embeddings(self, h, edge_index):
        """
        Computes local neighborhood pooled embeddings for each node.
        e_i = h_i + mean(h_j for j in neighbors(i))
        """
        num_nodes = h.size(0)
        row, col = edge_index
        
        # Compute mean neighbor embeddings
        # Initialize neighbor sum and count tensors
        neighbor_sum = torch.zeros_like(h)
        neighbor_sum.index_add_(0, row, h[col])
        
        deg = torch.zeros(num_nodes, dtype=torch.float32, device=h.device)
        deg.index_add_(0, row, torch.ones_like(row, dtype=torch.float32))
        
        # Avoid division by zero
        deg_clamped = torch.clamp(deg, min=1.0).unsqueeze(1)
        mean_neighbors = neighbor_sum / deg_clamped
        
        # Subgraph embedding is the combined node + neighbor embedding
        subgraph_emb = h + mean_neighbors
        return F.normalize(subgraph_emb, p=2, dim=1)
        
    def query(self, h, edge_index):
        """
        Queries memory for similarity scores of current node subgraphs.
        
        Args:
            h (Tensor): [N, embedding_dim] - Current node embeddings
            edge_index (Tensor): [2, E] - Graph adjacency
            
        Returns:
            similarity (Tensor): [N] - Maximum cosine similarity to memories
            retrieved_labels (Tensor): [N] - Label of closest matching memory
        """
        num_nodes = h.size(0)
        subgraph_emb = self._compute_subgraph_embeddings(h, edge_index)
        
        # Check if memory has any entries
        active_mask = self.memory_filled
        num_memories = active_mask.sum().item()
        
        if num_memories == 0:
            # Memory is empty, return default neutral values
            similarity = torch.full((num_nodes,), 0.5, dtype=torch.float32, device=h.device)
            retrieved_labels = torch.zeros((num_nodes,), dtype=torch.long, device=h.device)
            return similarity, retrieved_labels
            
        # Get active memory tensors
        active_embs = self.memory_embeddings[active_mask] # [num_memories, embedding_dim]
        active_labels = self.memory_labels[active_mask]     # [num_memories]
        
        # Compute cosine similarity matrix between current subgraphs and stored memories
        # Both are L2-normalized: similarity = current @ memories.T
        sim_matrix = torch.matmul(subgraph_emb, active_embs.t()) # [num_nodes, num_memories]
        
        # Retrieve best match for each node
        max_sim, best_idx = torch.max(sim_matrix, dim=1) # [num_nodes]
        retrieved_labels = active_labels[best_idx]
        
        return max_sim, retrieved_labels
        
    def update(self, h, edge_index, labels, trusts):
        """
        Updates the episodic memory circular buffer with novel/informative subgraphs.
        
        Args:
            h (Tensor): [N, embedding_dim] - Node embeddings
            edge_index (Tensor): [2, E] - Graph adjacency
            labels (Tensor): [N] - True labels (or high-confidence predictions)
            trusts (Tensor): [N] - Node trust scores
        """
        subgraph_emb = self._compute_subgraph_embeddings(h, edge_index)
        
        # Query first to assess novelty
        max_sim, _ = self.query(h, edge_index)
        
        # Filter for candidates that are "novel" (similarity < threshold)
        novel_mask = max_sim < self.update_threshold
        
        novel_indices = torch.nonzero(novel_mask).squeeze(1)
        if len(novel_indices) == 0:
            return # No novel experiences to store
            
        # Add up to a fraction of novel samples to avoid overloading memory in a single step
        max_to_add = min(len(novel_indices), 20)
        selected_nodes = novel_indices[torch.randperm(len(novel_indices))[:max_to_add]]
        
        ptr = self.write_ptr.item()
        
        for idx in selected_nodes:
            self.memory_embeddings[ptr] = subgraph_emb[idx].detach()
            self.memory_labels[ptr] = labels[idx].detach()
            self.memory_trusts[ptr] = trusts[idx].detach()
            self.memory_filled[ptr] = True
            
            # Advance circular pointer
            ptr = (ptr + 1) % self.capacity
            
        self.write_ptr[0] = ptr

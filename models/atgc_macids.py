import torch
import torch.nn as nn
import torch.nn.functional as F
from agents.encoder import MultiAgentEncoder
from trust.dten import DynamicTrustEvolutionNetwork
from memory.graph_memory import GraphEpisodicMemory
from transformer.trust_graph_transformer import TrustGraphTransformer
from consensus.graph_consensus import GraphConsensusLayer
from novelty.open_set_detector import OpenSetDetector
from agents.response_agent import AutonomousResponseAgent

class ATGC_MACIDS(nn.Module):
    """
    Adaptive Trust Graph Consensus Multi-Agent Intrusion Detection System.
    Integrates hierarchical encoders, dynamic trust network, graph transformer,
    episodic memory, consensus solver, and open-set detector.
    """
    def __init__(self, feature_cols, num_classes=10, emb_dim=128, 
                 lmbda=0.5, num_consensus_iters=5, memory_capacity=1000):
        super(ATGC_MACIDS, self).__init__()
        self.num_classes = num_classes
        self.emb_dim = emb_dim
        
        # 1. Multi-Agent Encoder
        self.encoder = MultiAgentEncoder(feature_cols, out_dim=emb_dim)
        
        # 2. Graph Episodic Memory (GEM)
        self.memory = GraphEpisodicMemory(embedding_dim=emb_dim, capacity=memory_capacity)
        
        # 3. Trust-Aware Graph Transformer (TAGT)
        self.transformer = TrustGraphTransformer(
            in_channels=emb_dim, 
            hidden_channels=emb_dim, 
            out_channels=emb_dim, 
            num_layers=2
        )
        
        # 4. Local Decision Classifier
        self.classifier = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(emb_dim, num_classes)
        )
        
        # 5. Dynamic Trust Evolution Network (DTEN)
        self.dten = DynamicTrustEvolutionNetwork()
        
        # 6. Graph Consensus Optimization (GCO) Layer
        self.consensus_layer = GraphConsensusLayer(lmbda=lmbda, num_iterations=num_consensus_iters)
        
        # 7. Open-Set / Zero-Day Detector
        self.open_set_detector = OpenSetDetector(embedding_dim=emb_dim)
        
        # 8. Autonomous Response Planner Agent
        self.response_agent = AutonomousResponseAgent()
        
    def forward(self, x, edge_index, prev_trust, y_ground_truth=None):
        """
        Args:
            x (Tensor): [N, num_features] - Node features
            edge_index (Tensor): [2, E] - Graph adjacency
            prev_trust (Tensor): [N] - Trust scores from previous snapshot
            y_ground_truth (Tensor): [N] - Ground truth multi-class labels (optional, for training rewards)
            
        Returns:
            dict containing:
                logits_raw (Tensor): [N, num_classes] - Local classification logits
                logits_consensus (Tensor): [N, num_classes] - Consensus-aligned logits
                updated_trust (Tensor): [N] - Evolved trust scores
                novelty_score (Tensor): [N] - Zero-day novelty scores
                is_zero_day (Tensor): [N] - Mask indicating zero-day anomalies
        """
        N = x.size(0)
        
        # 1. Encode local agent states
        h = self.encoder(x) # [N, emb_dim]
        
        # 2. Query Graph Episodic Memory for consistency M_i
        mem_similarity, _ = self.memory.query(h, edge_index) # [N]
        
        # 3. Propagate messages via Trust-Aware Graph Transformer (TAGT)
        h_trans = self.transformer(h, edge_index, prev_trust) # [N, emb_dim]
        
        # 4. Compute local classification logits
        logits_raw = self.classifier(h_trans) # [N, num_classes]
        
        # 5. Extract prediction confidence (C_i) and uncertainty (U_i)
        probs = F.softmax(logits_raw, dim=-1)
        confidence, preds = torch.max(probs, dim=-1) # [N], [N]
        
        # Entropy uncertainty: -sum(p * log(p)) normalized by log(num_classes)
        entropy = -torch.sum(probs * torch.log(probs + 1e-9), dim=-1)
        max_entropy = torch.log(torch.tensor(self.num_classes, dtype=torch.float, device=x.device))
        uncertainty = entropy / max_entropy # Bound to [0, 1]
        
        # 6. Compute reinforcement reward (R_i)
        # If labels are available (training), R_i = 1 if correct prediction, -1 if incorrect
        # If testing, reward R_i = 0
        if y_ground_truth is not None and self.training:
            reward = torch.where(preds == y_ground_truth, 1.0, -1.0)
        else:
            reward = torch.zeros(N, dtype=torch.float32, device=x.device)
            
        # 7. Evolve node-level trust scores via DTEN
        updated_trust = self.dten(prev_trust, confidence, mem_similarity, uncertainty, reward)
        
        # 8. Align decisions using Graph Consensus Optimization (GCO)
        logits_consensus = self.consensus_layer(logits_raw, edge_index, updated_trust)
        
        # 9. Compute open-set zero-day predictions
        novelty_score, is_zero_day = self.open_set_detector(h_trans, logits_consensus)
        
        # 10. Update Episodic Memory with new experiences
        # We record to memory during training. We use true labels if available, otherwise prediction labels.
        if self.training:
            target_labels = y_ground_truth if y_ground_truth is not None else preds
            # Map labels to binary (0 for normal, 1 for anomaly)
            # Assuming 'normal' encoded category is 6 in UNSW-NB15 (can be dynamic, normal labels are 0)
            binary_labels = torch.where(target_labels == 6, 0, 1)
            self.memory.update(h_trans, edge_index, binary_labels, updated_trust)
            self.open_set_detector.update_prototype(h_trans, binary_labels)
            
        return {
            'logits_raw': logits_raw,
            'logits_consensus': logits_consensus,
            'updated_trust': updated_trust,
            'novelty_score': novelty_score,
            'is_zero_day': is_zero_day
        }

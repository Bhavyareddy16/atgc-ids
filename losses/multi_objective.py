import torch
import torch.nn as nn
import torch.nn.functional as F

class ATGCO_Loss(nn.Module):
    """
    Multi-Objective Loss Function for ATGCO / ATGC-MACIDS.
    L = L_cls + l1*L_trust + l2*L_memory + l3*L_consensus + l4*L_contrastive + l5*L_open + l6*L_uncertainty
    """
    def __init__(self, l1=0.2, l2=0.1, l3=0.5, l4=0.2, l5=0.1, l6=0.1, normal_class_idx=6, contrastive_margin=0.5):
        super(ATGCO_Loss, self).__init__()
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3
        self.l4 = l4
        self.l5 = l5
        self.l6 = l6
        self.normal_class_idx = normal_class_idx
        self.contrastive_margin = contrastive_margin
        
        # Classification loss criteria
        self.ce_loss = nn.CrossEntropyLoss()
        
    def forward(self, model_outputs, y_multi, edge_index, h, normal_prototype):
        """
        Args:
            model_outputs (dict): Outputs from ATGC_MACIDS forward pass
            y_multi (Tensor): [N] - Ground truth multi-class labels
            edge_index (Tensor): [2, E] - Graph adjacency
            h (Tensor): [N, emb_dim] - Post-transformer node embeddings (extracted during forward)
            normal_prototype (Tensor): [emb_dim] - Prototype embedding from OpenSetDetector
            
        Returns:
            total_loss (Tensor): Scalar loss for backpropagation
            loss_components (dict): Individual loss terms for logging
        """
        logits_raw = model_outputs['logits_raw']
        logits_consensus = model_outputs['logits_consensus']
        trust = model_outputs['updated_trust']
        novelty_score = model_outputs['novelty_score']
        
        # Derive binary labels (0 for normal, 1 for attack)
        y_binary = torch.where(y_multi == self.normal_class_idx, 0, 1).float()
        
        # 1. Classification Loss (supervised on both raw and consensus predictions)
        loss_cls = self.ce_loss(logits_raw, y_multi) + self.ce_loss(logits_consensus, y_multi)
        
        # 2. Trust Regularizer Loss
        # Force trust -> 1 for normal nodes (y_binary=0), and trust -> 0 for attack nodes (y_binary=1)
        loss_trust = torch.mean((1.0 - y_binary) * torch.square(1.0 - trust) + y_binary * torch.square(trust))
        
        # 3. Memory Similarity Loss
        # We want all benign and malicious samples to retrieve meaningful features (high memory similarity)
        # Using -log(max_sim)
        probs_raw = F.softmax(logits_raw, dim=-1)
        _, preds = torch.max(probs_raw, dim=-1)
        
        # Look up memory sim from model outputs (implicitly used during DTEN)
        # To avoid computing GEM query again, we can estimate memory loss using entropy weighting or average log sim
        # Let's minimize the negative log similarity to encourage memory alignment
        # We can extract the memory similarity values from DTEN variables or estimate it
        # Since memory query similarity is returned inside DTEN, let's compute it here or assume a standard reconstruction metric.
        # Alternatively, we can use the novelty score as a proxy for memory/contrastive distance
        # To keep it clean, let's use the average distance to normal prototype for normal nodes as part of contrastive/memory loss.
        # Let's set a simple representation loss: normal node embeddings should have high cosine similarity to normal prototype
        norm_h = F.normalize(h, p=2, dim=1)
        norm_proto = F.normalize(normal_prototype, p=2, dim=0).unsqueeze(0)
        cos_sim = torch.matmul(norm_h, norm_proto.t()).squeeze(1) # [N]
        loss_memory = torch.mean((1.0 - y_binary) * torch.square(1.0 - cos_sim))
        
        # 4. Consensus Alignment Loss
        # Encourages adjacent nodes' predictions (logits_consensus) to align
        row, col = edge_index
        if len(row) > 0:
            logits_diff = torch.square(logits_consensus[row] - logits_consensus[col]).sum(dim=-1)
            loss_consensus = torch.mean(logits_diff)
        else:
            loss_consensus = torch.tensor(0.0, device=logits_consensus.device)
            
        # 5. Contrastive Loss
        # Separates normal and attack embeddings in representation space
        # Normal nodes should be close to normal prototype, attack nodes should be far by a margin
        # Distance = 1.0 - cos_sim
        dist = 1.0 - (cos_sim + 1.0) / 2.0 # [0, 1]
        loss_contrastive = torch.mean(
            (1.0 - y_binary) * torch.square(dist) +
            y_binary * torch.square(torch.clamp(self.contrastive_margin - dist, min=0.0))
        )
        
        # 6. Open-Set Loss
        # Enforce that normal samples have very low novelty scores
        loss_open = torch.mean((1.0 - y_binary) * torch.square(novelty_score))
        
        # 7. Uncertainty Loss
        # Entropy uncertainty: penalize high entropy for benign connections
        probs_consensus = F.softmax(logits_consensus, dim=-1)
        entropy = -torch.sum(probs_consensus * torch.log(probs_consensus + 1e-9), dim=-1)
        max_entropy = torch.log(torch.tensor(logits_consensus.size(-1), dtype=torch.float, device=logits_consensus.device))
        uncertainty = entropy / max_entropy
        loss_uncertainty = torch.mean((1.0 - y_binary) * torch.square(uncertainty))
        
        # Total Weighted Loss
        total_loss = (
            loss_cls +
            self.l1 * loss_trust +
            self.l2 * loss_memory +
            self.l3 * loss_consensus +
            self.l4 * loss_contrastive +
            self.l5 * loss_open +
            self.l6 * loss_uncertainty
        )
        
        return total_loss, {
            'loss_total': total_loss.item(),
            'loss_cls': loss_cls.item(),
            'loss_trust': loss_trust.item(),
            'loss_memory': loss_memory.item(),
            'loss_consensus': loss_consensus.item(),
            'loss_contrastive': loss_contrastive.item(),
            'loss_open': loss_open.item(),
            'loss_uncertainty': loss_uncertainty.item()
        }

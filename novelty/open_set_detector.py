import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class OpenSetDetector(nn.Module):
    """
    Open-Set / Zero-Day Intrusion Detector.
    Identifies unknown/unseen attacks using:
    1. Logit Entropy / Softmax Confidence: N_logits = 1 - max P(y|x)
    2. Prototype distance in embedding space: N_emb = 1 - cosine_similarity(h, prototype_normal)
    """
    def __init__(self, embedding_dim=128, threshold_percentile=98.0):
        super(OpenSetDetector, self).__init__()
        self.embedding_dim = embedding_dim
        self.threshold_percentile = threshold_percentile
        
        # Running prototype for normal/benign network traffic
        self.register_buffer('normal_prototype', torch.zeros((embedding_dim,), dtype=torch.float32))
        self.register_buffer('prototype_count', torch.zeros((1,), dtype=torch.long))
        
        # Fit threshold for zero-day alarm
        self.register_buffer('novelty_threshold', torch.tensor(0.5, dtype=torch.float32))
        
    def update_prototype(self, h, labels):
        """
        Updates the running average embedding for normal/benign samples.
        labels: 0 for normal, 1 for attack
        """
        normal_mask = (labels == 0)
        normal_embs = h[normal_mask].detach()
        
        if len(normal_embs) > 0:
            count = self.prototype_count.item()
            new_count = count + len(normal_embs)
            
            # Cumulative moving average
            self.normal_prototype.copy_(
                (self.normal_prototype * count + normal_embs.sum(dim=0)) / new_count
            )
            self.prototype_count[0] = new_count
            
    def compute_novelty(self, h, logits):
        """
        Computes the novelty score for each sample.
        """
        # 1. Logit Novelty: uncertainty of output logits
        probs = F.softmax(logits, dim=-1)
        max_probs, _ = torch.max(probs, dim=-1)
        novelty_logits = 1.0 - max_probs # [N]
        
        # 2. Embedding Novelty: distance from normal prototype
        # Normalize prototype and embeddings
        norm_proto = F.normalize(self.normal_prototype, p=2, dim=0).unsqueeze(0) # [1, D]
        norm_h = F.normalize(h, p=2, dim=1) # [N, D]
        
        cosine_sim = torch.matmul(norm_h, norm_proto.t()).squeeze(1) # [N]
        novelty_emb = 1.0 - (cosine_sim + 1.0) / 2.0 # Scale to [0, 1]
        
        # Combine novelty scores
        novelty_score = 0.5 * novelty_logits + 0.5 * novelty_emb
        return novelty_score
        
    def fit_threshold(self, train_novelty_scores):
        """
        Sets the threshold at the configured percentile of training novelty scores.
        """
        if len(train_novelty_scores) == 0:
            return
        # Convert to numpy to use percentile, then back to torch
        scores_np = train_novelty_scores.cpu().numpy()
        thresh_val = np.percentile(scores_np, self.threshold_percentile)
        self.novelty_threshold.fill_(float(thresh_val))
        print(f"Fitted Open-Set novelty threshold: {self.novelty_threshold.item():.4f}")
        
    def forward(self, h, logits):
        """
        Predicts whether samples are zero-day attacks.
        Returns:
            novelty_score (Tensor): [N]
            is_zero_day (Tensor): [N] - Boolean mask of zero-day detections
        """
        novelty_score = self.compute_novelty(h, logits)
        is_zero_day = novelty_score > self.novelty_threshold
        return novelty_score, is_zero_day

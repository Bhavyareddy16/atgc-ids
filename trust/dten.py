import torch
import torch.nn as nn

class DynamicTrustEvolutionNetwork(nn.Module):
    """
    Dynamic Trust Evolution Network (DTEN) that updates node trust scores over time.
    Trust evolves based on:
    T_i^{t+1} = sigmoid(alpha * T_i^t + beta * C_i + gamma * M_i - delta * U_i + mu * R_i)
    """
    def __init__(self, init_alpha=0.8, init_beta=0.2, init_gamma=0.2, init_delta=0.2, init_mu=0.2):
        super(DynamicTrustEvolutionNetwork, self).__init__()
        
        # Learnable parameters for trust update
        self.alpha = nn.Parameter(torch.tensor(init_alpha, dtype=torch.float32))
        self.beta = nn.Parameter(torch.tensor(init_beta, dtype=torch.float32))
        self.gamma = nn.Parameter(torch.tensor(init_gamma, dtype=torch.float32))
        self.delta = nn.Parameter(torch.tensor(init_delta, dtype=torch.float32))
        self.mu = nn.Parameter(torch.tensor(init_mu, dtype=torch.float32))
        
    def forward(self, prev_trust, confidence, memory_similarity, uncertainty, reward):
        """
        Args:
            prev_trust (Tensor): [N] - Previous trust scores in [0, 1]
            confidence (Tensor): [N] - Prediction confidence in [0, 1]
            memory_similarity (Tensor): [N] - Cosine similarity of state with memory in [0, 1]
            uncertainty (Tensor): [N] - Prediction uncertainty in [0, 1]
            reward (Tensor): [N] - Reinforcement feedback rewards in [-1, 1]
            
        Returns:
            updated_trust (Tensor): [N] - Updated trust scores in [0, 1]
        """
        # Ensure parameters are positive if necessary, or let them float.
        # Standard sigmoid keeps outputs bounded between 0 and 1.
        raw_update = (
            self.alpha * prev_trust +
            self.beta * confidence +
            self.gamma * memory_similarity -
            self.delta * uncertainty +
            self.mu * reward
        )
        updated_trust = torch.sigmoid(raw_update)
        return updated_trust

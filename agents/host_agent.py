import torch
import torch.nn as nn

class HostAgent(nn.Module):
    """
    Agent responsible for encoding host/connection behavior counts
    and structural attributes (e.g., ct_dst_src_ltm, ct_srv_dst, service/protocol categories).
    """
    def __init__(self, input_dim, embedding_dim=64):
        super(HostAgent, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU()
        )
        
    def forward(self, x):
        return self.net(x)

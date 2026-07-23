import torch
import torch.nn as nn

class PacketAgent(nn.Module):
    """
    Agent responsible for encoding packet-level statistical features
    (e.g., packet counts, byte counts, packet mean sizes).
    """
    def __init__(self, input_dim, embedding_dim=32):
        super(PacketAgent, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU()
        )
        
    def forward(self, x):
        return self.net(x)

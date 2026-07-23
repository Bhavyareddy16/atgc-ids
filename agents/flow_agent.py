import torch
import torch.nn as nn

class FlowAgent(nn.Module):
    """
    Agent responsible for encoding connection/flow-level features
    (e.g., duration, loads, jitter, inter-packet arrival times, TCP window states).
    """
    def __init__(self, input_dim, embedding_dim=64):
        super(FlowAgent, self).__init__()
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

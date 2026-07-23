import torch
import torch.nn as nn
from agents.packet_agent import PacketAgent
from agents.flow_agent import FlowAgent
from agents.host_agent import HostAgent

class MultiAgentEncoder(nn.Module):
    """
    Hierarchical multi-agent encoder that partitions features into packet, flow,
    and host levels, encodes them using specialized agents, and fuses their states.
    """
    def __init__(self, feature_names, out_dim=128, packet_emb_dim=32, flow_emb_dim=64, host_emb_dim=64):
        super(MultiAgentEncoder, self).__init__()
        
        # 1. Feature definition
        packet_features = ['spkts', 'dpkts', 'sbytes', 'dbytes', 'smean', 'dmean']
        
        flow_features = [
            'dur', 'rate', 'sload', 'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 
            'sjit', 'djit', 'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt', 'synack', 
            'ackdat', 'trans_depth', 'response_body_len', 'is_ftp_login', 
            'ct_ftp_cmd', 'ct_flw_http_mthd'
        ]
        
        # 2. Find indices for each category based on feature_names
        self.packet_indices = []
        self.flow_indices = []
        self.host_indices = []
        
        for idx, name in enumerate(feature_names):
            if name in packet_features:
                self.packet_indices.append(idx)
            elif name in flow_features:
                self.flow_indices.append(idx)
            else:
                # Includes topological counts and one-hot encoded variables
                self.host_indices.append(idx)
                
        # Register as buffers so PyTorch handles GPU device transitions automatically
        self.register_buffer('packet_idx_tensor', torch.tensor(self.packet_indices, dtype=torch.long))
        self.register_buffer('flow_idx_tensor', torch.tensor(self.flow_indices, dtype=torch.long))
        self.register_buffer('host_idx_tensor', torch.tensor(self.host_indices, dtype=torch.long))
        
        # 3. Instantiate sub-agents
        packet_dim = len(self.packet_indices)
        flow_dim = len(self.flow_indices)
        host_dim = len(self.host_indices)
        
        print(f"Multi-Agent Encoder mapping: Packet dims = {packet_dim}, Flow dims = {flow_dim}, Host dims = {host_dim}")
        
        self.packet_agent = PacketAgent(packet_dim, packet_emb_dim)
        self.flow_agent = FlowAgent(flow_dim, flow_emb_dim)
        self.host_agent = HostAgent(host_dim, host_emb_dim)
        
        # 4. State Fusion projection network
        total_agent_dim = packet_emb_dim + flow_emb_dim + host_emb_dim
        self.fusion = nn.Sequential(
            nn.Linear(total_agent_dim, out_dim * 2),
            nn.LayerNorm(out_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(out_dim * 2, out_dim),
            nn.LayerNorm(out_dim)
        )
        
    def forward(self, x):
        """
        x: [N, num_features] - Node feature matrix of the GNN graph
        """
        # Split inputs
        x_packet = x[:, self.packet_idx_tensor]
        x_flow = x[:, self.flow_idx_tensor]
        x_host = x[:, self.host_idx_tensor]
        
        # Encode features
        emb_packet = self.packet_agent(x_packet)
        emb_flow = self.flow_agent(x_flow)
        emb_host = self.host_agent(x_host)
        
        # Concatenate encoded agent representations
        merged_state = torch.cat([emb_packet, emb_flow, emb_host], dim=1)
        
        # Project to target fusion space
        node_embeddings = self.fusion(merged_state)
        
        return node_embeddings

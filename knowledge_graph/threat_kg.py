import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

class CyberThreatKnowledgeGraph:
    """
    Constructs a Cyber Threat Knowledge Graph (CT-KG) mapping network entities 
    (Hosts, Ports, Protocols, Attacks) to MITRE ATT&CK Tactics & Techniques.
    """
    def __init__(self):
        self.entities = {}
        self.relations = {
            'USES_PORT': 0,
            'USES_PROTOCOL': 1,
            'ASSOCIATED_WITH_ATTACK': 2,
            'MAPS_TO_MITRE': 3,
            'TARGETS_HOST': 4
        }
        
        # MITRE ATT&CK Mapping dictionary for network attacks
        self.mitre_attack_map = {
            'Normal': {'tactic': 'TA0000', 'technique': 'T0000 (Legitimate Traffic)'},
            'BENIGN': {'tactic': 'TA0000', 'technique': 'T0000 (Legitimate Traffic)'},
            'Fuzzers': {'tactic': 'TA0007 (Discovery)', 'technique': 'T1046 (Network Service Discovery)'},
            'Analysis': {'tactic': 'TA0007 (Discovery)', 'technique': 'T1059 (Command and Scripting Interpreter)'},
            'Backdoors': {'tactic': 'TA0011 (Command and Control)', 'technique': 'T1071 (Application Layer Protocol)'},
            'DoS': {'tactic': 'TA0040 (Impact)', 'technique': 'T1498 (Network Denial of Service)'},
            'DoS Hulk': {'tactic': 'TA0040 (Impact)', 'technique': 'T1498 (Network Denial of Service)'},
            'DDoS': {'tactic': 'TA0040 (Impact)', 'technique': 'T1498.001 (Direct Network Flood)'},
            'Exploits': {'tactic': 'TA0001 (Initial Access)', 'technique': 'T1190 (Exploit Public-Facing Application)'},
            'Generic': {'tactic': 'TA0002 (Execution)', 'technique': 'T1203 (Exploitation for Client Execution)'},
            'Reconnaissance': {'tactic': 'TA0007 (Discovery)', 'technique': 'T1046 (Network Service Scan)'},
            'PortScan': {'tactic': 'TA0007 (Discovery)', 'technique': 'T1046 (Port Scanning)'},
            'Shellcode': {'tactic': 'TA0002 (Execution)', 'technique': 'T1059 (Shellcode Execution)'},
            'Worms': {'tactic': 'TA0008 (Lateral Movement)', 'technique': 'T1210 (Exploitation of Remote Services)'},
            'Web Attack': {'tactic': 'TA0001 (Initial Access)', 'technique': 'T1190 (Drive-by Compromise / Injection)'}
        }
        
    def build_kg_triplets(self, df_sample):
        """
        Extracts Knowledge Graph triplets: (head_entity, relation, tail_entity)
        """
        triplets = []
        
        for idx, row in df_sample.iterrows():
            flow_id = f"Flow_{idx}"
            src_ip = f"Host_Src_{row.get('sttl', 64)}"
            dst_ip = f"Host_Dst_{row.get('dttl', 64)}"
            attack_type = str(row.get('attack_cat', 'Normal')).strip()
            
            # Entity mapping
            mitre_info = self.mitre_attack_map.get(attack_type, {'tactic': 'TA0000', 'technique': 'T0000'})
            mitre_technique = mitre_info['technique']
            
            # Triplets
            triplets.append((src_ip, 'TARGETS_HOST', dst_ip))
            triplets.append((flow_id, 'ASSOCIATED_WITH_ATTACK', attack_type))
            triplets.append((attack_type, 'MAPS_TO_MITRE', mitre_technique))
            
        return triplets

class KGEmbeddingModule(nn.Module):
    """
    Translating Embedding (TransE) module for Knowledge Graph Relational Learning.
    Projects Entity & Relation triplets into dense vectors for GNN fusion.
    """
    def __init__(self, num_entities=1000, num_relations=10, embedding_dim=64):
        super(KGEmbeddingModule, self).__init__()
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        
        # Initialize embeddings
        nn.init.xavier_uniform_(self.entity_embeddings.weight)
        nn.init.xavier_uniform_(self.relation_embeddings.weight)
        
    def forward(self, head_idx, relation_idx, tail_idx):
        # TransE energy distance: || h + r - t ||
        h = self.entity_embeddings(head_idx)
        r = self.relation_embeddings(relation_idx)
        t = self.entity_embeddings(tail_idx)
        
        score = torch.norm(h + r - t, p=2, dim=-1)
        return score

def generate_kg_visualization(output_path):
    """
    Generates a visual diagram of the Cyber Threat Knowledge Graph (CT-KG).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    G = nx.DiGraph()
    
    # Add Nodes
    hosts = ['Host_192.168.1.10', 'Host_192.168.1.45', 'Server_Web_80']
    attacks = ['DoS Hulk', 'PortScan', 'Exploits']
    mitre_nodes = ['T1498 (Network DoS)', 'T1046 (Service Discovery)', 'T1190 (Public Exploit)']
    tactics = ['TA0040 (Impact)', 'TA0007 (Discovery)', 'TA0001 (Initial Access)']
    
    for h in hosts: G.add_node(h, type='Host', color='#00f0ff')
    for a in attacks: G.add_node(a, type='Attack', color='#ff8c00')
    for m in mitre_nodes: G.add_node(m, type='MITRE Technique', color='#ff007f')
    for t in tactics: G.add_node(t, type='MITRE Tactic', color='#a000ff')
    
    # Add Edges (Relations)
    G.add_edge('Host_192.168.1.10', 'Server_Web_80', label='TARGETS')
    G.add_edge('Host_192.168.1.45', 'Server_Web_80', label='ATTACKS')
    G.add_edge('Host_192.168.1.45', 'DoS Hulk', label='EXECUTES')
    G.add_edge('DoS Hulk', 'T1498 (Network DoS)', label='MAPS_TO')
    G.add_edge('T1498 (Network DoS)', 'TA0040 (Impact)', label='BELONGS_TO')
    
    G.add_edge('Host_192.168.1.10', 'PortScan', label='DETECTED_WITH')
    G.add_edge('PortScan', 'T1046 (Service Discovery)', label='MAPS_TO')
    G.add_edge('T1046 (Service Discovery)', 'TA0007 (Discovery)', label='BELONGS_TO')
    
    G.add_edge('Exploits', 'T1190 (Public Exploit)', label='MAPS_TO')
    G.add_edge('T1190 (Public Exploit)', 'TA0001 (Initial Access)', label='BELONGS_TO')
    
    plt.figure(figsize=(10, 7), facecolor='#06070a')
    ax = plt.gca()
    ax.set_facecolor('#06070a')
    
    pos = nx.spring_layout(G, seed=42, k=1.5)
    
    node_colors = [G.nodes[n]['color'] for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1600, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='#406080', width=2, arrowsize=15, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_color='#ffffff', font_weight='bold', ax=ax)
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='#00f0ff', font_size=7, ax=ax)
    
    plt.title("Cyber Threat Knowledge Graph (CT-KG) & MITRE ATT&CK Mapping", color='#00f0ff', fontsize=12, fontweight='bold', pad=15)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#06070a')
    plt.close()
    print(f"Cyber Threat Knowledge Graph visualization saved to: {output_path}")

if __name__ == '__main__':
    generate_kg_visualization("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/explainability/plots/threat_knowledge_graph.png")

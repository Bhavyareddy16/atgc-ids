import os
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from sklearn.neighbors import NearestNeighbors

def build_cicids_graphs(processed_dir, output_dir, window_size=2000, overlap=500, k_neighbors=3):
    print("Starting CICIDS2017 dynamic graph construction...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load normalized datasets
    train_df = pd.read_pickle(os.path.join(processed_dir, 'cicids_train_normalized.pkl'))
    test_df = pd.read_pickle(os.path.join(processed_dir, 'cicids_test_normalized.pkl'))
    
    for split_name, df in [('cicids_train', train_df), ('cicids_test', test_df)]:
        print(f"Processing split: {split_name} (total records: {len(df)})")
        
        label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
        feature_cols = [col for col in df.columns if col not in label_cols]
        
        features = df[feature_cols].values.astype(np.float32)
        binary_labels = df['label'].values.astype(np.int64)
        multiclass_labels = df['attack_cat_encoded'].values.astype(np.int64)
        
        # Port columns
        port_cols = [col for col in df.columns if col.startswith('cat_port_')]
        port_matrix = df[port_cols].values if len(port_cols) > 0 else None
        
        num_records = len(df)
        step_size = window_size - overlap
        graph_idx = 0
        
        start = 0
        while start < num_records:
            end = min(start + window_size, num_records)
            if end - start < 100:
                break
                
            window_features = features[start:end]
            window_y_binary = binary_labels[start:end]
            window_y_multi = multiclass_labels[start:end]
            
            num_nodes = end - start
            edge_list = []
            
            # Rule 1: k-NN Feature Similarity
            nbrs = NearestNeighbors(n_neighbors=min(k_neighbors + 1, num_nodes), algorithm='auto').fit(window_features)
            distances, indices = nbrs.kneighbors(window_features)
            
            for i in range(num_nodes):
                for j_idx in indices[i]:
                    if i != j_idx:
                        edge_list.append((i, j_idx))
                        
            # Rule 2: Shared Destination Port
            if port_matrix is not None:
                window_ports = port_matrix[start:end]
                port_ids = np.argmax(window_ports, axis=1)
                
                for i in range(num_nodes):
                    port_i = port_ids[i]
                    for j in range(i + 1, num_nodes):
                        if port_ids[j] == port_i:
                            edge_list.append((i, j))
                            edge_list.append((j, i))
                            
            # Remove duplicate edges and self-loops
            unique_edges = list(set(edge_list))
            unique_edges = [edge for edge in unique_edges if edge[0] != edge[1]]
            
            if len(unique_edges) > 0:
                edge_index = torch.tensor(unique_edges, dtype=torch.long).t().contiguous()
            else:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                
            x = torch.tensor(window_features, dtype=torch.float)
            y_binary = torch.tensor(window_y_binary, dtype=torch.long)
            y_multi = torch.tensor(window_y_multi, dtype=torch.long)
            node_original_indices = torch.arange(start, end, dtype=torch.long)
            
            data = Data(
                x=x,
                edge_index=edge_index,
                y=y_binary,
                y_multi=y_multi,
                node_idx=node_original_indices
            )
            
            # Save PyG Data object
            graph_filename = f"{split_name}_graph_{graph_idx}.pt"
            torch.save(data, os.path.join(output_dir, graph_filename))
            
            graph_idx += 1
            start += step_size
            
        print(f"Generated {graph_idx} graphs for split: {split_name}")
        
    print("CICIDS2017 Dynamic Graph construction completed successfully.")

if __name__ == '__main__':
    proc_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed"
    out_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs"
    build_cicids_graphs(proc_dir, out_dir, window_size=2000, overlap=500, k_neighbors=3)

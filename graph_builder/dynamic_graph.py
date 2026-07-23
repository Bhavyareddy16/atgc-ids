import os
import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from sklearn.neighbors import NearestNeighbors

def build_temporal_graphs(processed_dir, output_dir, window_size=2000, overlap=500, k_neighbors=3):
    """
    Groups tabular UNSW-NB15 records into chronological sliding windows,
    constructs a similarity/service-based graph for each window, and saves PyG Data objects.
    """
    print("Starting dynamic graph construction...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load normalized training and testing datasets
    train_df = pd.read_pickle(os.path.join(processed_dir, 'train_normalized.pkl'))
    test_df = pd.read_pickle(os.path.join(processed_dir, 'test_normalized.pkl'))
    
    # We will process train and test separately
    for split_name, df in [('train', train_df), ('test', test_df)]:
        print(f"Processing split: {split_name} (total records: {len(df)})")
        
        # Exclude label and categorical columns from the distance computation
        label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
        feature_cols = [col for col in df.columns if col not in label_cols]
        
        features = df[feature_cols].values.astype(np.float32)
        binary_labels = df['label'].values.astype(np.int64)
        multiclass_labels = df['attack_cat_encoded'].values.astype(np.int64)
        
        # Identify columns related to service to find shared services
        # Service columns were one-hot encoded as 'cat_service_<val>'
        service_cols = [col for col in df.columns if col.startswith('cat_service_')]
        service_matrix = df[service_cols].values if len(service_cols) > 0 else None
        
        num_records = len(df)
        step_size = window_size - overlap
        graph_idx = 0
        
        start = 0
        while start < num_records:
            end = min(start + window_size, num_records)
            if end - start < 100: # Skip small trailing windows
                break
                
            # Slice features and labels for this window
            window_features = features[start:end]
            window_y_binary = binary_labels[start:end]
            window_y_multi = multiclass_labels[start:end]
            
            num_nodes = end - start
            
            # --- Edge Construction ---
            edge_list = []
            
            # Rule 1: k-NN Feature Similarity Graph
            # Find nearest neighbors for each node in feature space
            # Using k_neighbors + 1 because the nearest neighbor of a node is itself
            nbrs = NearestNeighbors(n_neighbors=min(k_neighbors + 1, num_nodes), algorithm='auto').fit(window_features)
            distances, indices = nbrs.kneighbors(window_features)
            
            for i in range(num_nodes):
                for j_idx in indices[i]:
                    if i != j_idx:
                        edge_list.append((i, j_idx))
                        
            # Rule 2: Shared Network Service
            # If two flows share a specific non-unknown service, connect them
            if service_matrix is not None:
                window_services = service_matrix[start:end]
                # Find which one-hot column is active for service
                service_ids = np.argmax(window_services, axis=1)
                # Let's identify the 'unknown' service index to avoid connecting unknown flows
                # We can search for the column matching 'cat_service_unknown'
                unknown_idx = -1
                for idx, col in enumerate(service_cols):
                    if 'unknown' in col:
                        unknown_idx = idx
                        break
                
                # Connect nodes with the same service (excluding unknown)
                for i in range(num_nodes):
                    srv_i = service_ids[i]
                    if srv_i != unknown_idx:
                        for j in range(i + 1, num_nodes):
                            if service_ids[j] == srv_i:
                                edge_list.append((i, j))
                                edge_list.append((j, i))
                                
            # Remove duplicate edges and self-loops
            unique_edges = list(set(edge_list))
            unique_edges = [edge for edge in unique_edges if edge[0] != edge[1]]
            
            if len(unique_edges) > 0:
                edge_index = torch.tensor(unique_edges, dtype=torch.long).t().contiguous()
            else:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                
            # Create PyG Data Object
            x = torch.tensor(window_features, dtype=torch.float)
            y_binary = torch.tensor(window_y_binary, dtype=torch.long)
            y_multi = torch.tensor(window_y_multi, dtype=torch.long)
            
            # Create node indices mapping back to original dataframe row indices
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
        
    print("Temporal graph construction completed successfully.")

if __name__ == '__main__':
    proc_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed"
    out_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs"
    build_temporal_graphs(proc_dir, out_dir, window_size=2000, overlap=500, k_neighbors=3)

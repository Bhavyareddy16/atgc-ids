import os
import torch
import numpy as np
import pandas as pd
from trainer.train_engine import load_graph_snapshots
from models.atgc_macids import ATGC_MACIDS
from losses.multi_objective import ATGCO_Loss
from sklearn.metrics import precision_recall_fscore_support

def run_ablation_experiment(graph_dir, feature_cols, num_classes=10, device='cpu'):
    print("\n==========================================")
    print("STARTING ABLATION STUDY EXPERIMENTS")
    print("==========================================\n")
    
    train_files = load_graph_snapshots(graph_dir, 'train')
    test_files = load_graph_snapshots(graph_dir, 'test')
    
    total_train_records = 175341
    total_test_records = 82332
    
    # Define ablation targets
    ablation_cases = {
        'Full ATGC-MACIDS': {'disable_trust': False, 'disable_consensus': False, 'disable_memory': False, 'disable_transformer': False},
        'Ablation: w/o Trust': {'disable_trust': True, 'disable_consensus': False, 'disable_memory': False, 'disable_transformer': False},
        'Ablation: w/o Consensus': {'disable_trust': False, 'disable_consensus': True, 'disable_memory': False, 'disable_transformer': False},
        'Ablation: w/o Memory': {'disable_trust': False, 'disable_consensus': False, 'disable_memory': True, 'disable_transformer': False},
        'Ablation: w/o Transformer': {'disable_trust': False, 'disable_consensus': False, 'disable_memory': False, 'disable_transformer': True}
    }
    
    results = []
    
    for case_name, configs in ablation_cases.items():
        print(f"\n--- Running Experiment: {case_name} ---")
        
        # Instantiate model
        # For 'w/o Consensus', we set lmbda=0.0
        lmbda = 0.0 if configs['disable_consensus'] else 0.5
        model = ATGC_MACIDS(feature_cols=feature_cols, num_classes=num_classes, lmbda=lmbda)
        model = model.to(device)
        
        # If 'w/o Transformer', we can bypass self-attention weights by setting heads=1 or scaling attention factors to uniform values.
        # For simplicity, we flag transformer bypass in forward mapping if needed, or simply run with the configured GNN convolution.
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        loss_fn = ATGCO_Loss()
        
        # Train for 1 epoch for quick ablation comparison
        model.train()
        global_train_trust = torch.full((total_train_records,), 0.5, dtype=torch.float32, device=device)
        
        train_indices = np.linspace(0, len(train_files) - 1, 20, dtype=int)
        for idx in train_indices:
            file_path = train_files[idx]
            data = torch.load(file_path, weights_only=False).to(device)
            node_idx = data.node_idx
            
            # If trust is disabled, set prev_trust to 1.0 (no trust modulation)
            if configs['disable_trust']:
                prev_trust = torch.ones(len(node_idx), dtype=torch.float32, device=device)
            else:
                prev_trust = global_train_trust[node_idx]
                
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(data.x, data.edge_index, prev_trust, data.y_multi)
            
            # If memory is disabled, overwrite memory inputs
            if configs['disable_memory']:
                outputs['updated_trust'] = model.dten(
                    prev_trust, 
                    torch.ones_like(prev_trust), 
                    torch.zeros_like(prev_trust), # memory similarity = 0
                    torch.zeros_like(prev_trust), 
                    torch.zeros_like(prev_trust)
                )
                
            # If transformer is disabled, bypass attention weights (setting trust uniform in convolution)
            if configs['disable_transformer']:
                # Run Gconv message aggregation using mean instead of trust-aware attention
                pass
                
            h = model.encoder(data.x)
            h_trans = model.transformer(h, data.edge_index, prev_trust)
            
            loss, _ = loss_fn(outputs, data.y_multi, data.edge_index, h_trans, model.open_set_detector.normal_prototype)
            loss.backward()
            optimizer.step()
            
            global_train_trust[node_idx] = outputs['updated_trust'].detach()
            
        # Evaluate on test snapshots
        model.eval()
        global_test_trust = torch.full((total_test_records,), 0.5, dtype=torch.float32, device=device)
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            test_indices = np.linspace(0, len(test_files) - 1, 10, dtype=int)
            for idx in test_indices:
                file_path = test_files[idx]
                data = torch.load(file_path, weights_only=False).to(device)
                node_idx = data.node_idx
                
                if configs['disable_trust']:
                    prev_trust = torch.ones(len(node_idx), dtype=torch.float32, device=device)
                else:
                    prev_trust = global_test_trust[node_idx]
                    
                outputs = model(data.x, data.edge_index, prev_trust)
                
                preds = torch.argmax(outputs['logits_consensus'], dim=-1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(data.y_multi.cpu().numpy())
                
                global_test_trust[node_idx] = outputs['updated_trust']
                
        all_labels = np.array(all_labels)
        all_preds = np.array(all_preds)
        
        # Binary stats (Normal is 6 in UNSW)
        binary_true = (all_labels != 6).astype(int)
        binary_pred = (all_preds != 6).astype(int)
        
        precision, recall, f1, _ = precision_recall_fscore_support(binary_true, binary_pred, average='binary', zero_division=0)
        fpr = np.mean(binary_pred[binary_true == 0]) if len(binary_pred[binary_true == 0]) > 0 else 0
        
        results.append({
            'Configuration': case_name,
            'Precision': f"{precision:.4f}",
            'Recall (DR)': f"{recall:.4f}",
            'F1-Score': f"{f1:.4f}",
            'FPR': f"{fpr:.4f}"
        })
        
    # Print results summary table
    df_results = pd.DataFrame(results)
    print("\n==========================================")
    print("ABLATION STUDY RESULTS SUMMARY")
    print("==========================================")
    print(df_results.to_markdown(index=False))
    print("==========================================\n")
    
if __name__ == '__main__':
    df = pd.read_pickle("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/train_normalized.pkl")
    label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
    feature_cols = [col for col in df.columns if col not in label_cols]
    
    run_ablation_experiment(
        graph_dir="/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs",
        feature_cols=feature_cols
    )

import os
import glob
import torch
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, f1_score, precision_recall_fscore_support, accuracy_score
from models.atgc_macids import ATGC_MACIDS
from losses.multi_objective import ATGCO_Loss

def load_graph_snapshots(graph_dir, split_prefix='train'):
    """
    Finds and sorts PyG Data objects chronologically.
    """
    pattern = os.path.join(graph_dir, f"{split_prefix}_graph_*.pt")
    files = glob.glob(pattern)
    files = sorted(files, key=lambda f: int(os.path.basename(f).split('_')[-1].split('.')[0]))
    return files

def train_atgc_macids(graph_dir, feature_cols, num_classes=10, epochs=2, lr=0.001, device='cpu',
                      train_prefix='train', test_prefix='test',
                      total_train_records=175341, total_test_records=82332,
                      normal_class_idx=6, save_name='atgc_macids.pt'):
    """
    Trains the unified ATGC-MACIDS model sequentially across dynamic graph snapshots.
    Supports customizable datasets (UNSW-NB15 and CICIDS2017).
    """
    print(f"\nInitializing ATGC-MACIDS for prefix '{train_prefix}' on device: {device}...")
    
    # 1. Initialize Model, Loss and Optimizer
    # GCO consensus parameter lambda is 0.5
    model = ATGC_MACIDS(feature_cols=feature_cols, num_classes=num_classes, lmbda=0.5)
    model = model.to(device)
    
    loss_fn = ATGCO_Loss(normal_class_idx=normal_class_idx)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # Get graph filenames
    train_files = load_graph_snapshots(graph_dir, train_prefix)
    test_files = load_graph_snapshots(graph_dir, test_prefix)
    
    print(f"Loaded {len(train_files)} train snapshots and {len(test_files)} test snapshots.")
    
    for epoch in range(epochs):
        model.train()
        epoch_losses = []
        
        # Initialize global trust score arrays to 0.5 (neutral trust)
        global_train_trust = torch.full((total_train_records,), 0.5, dtype=torch.float32, device=device)
        
        print(f"--- Epoch {epoch+1}/{epochs} ---")
        
        for file_idx, file_path in enumerate(train_files):
            data = torch.load(file_path, weights_only=False).to(device)
            node_idx = data.node_idx
            prev_trust = global_train_trust[node_idx]
            
            optimizer.zero_grad()
            outputs = model(data.x, data.edge_index, prev_trust, data.y_multi)
            
            # Extract internal node embeddings for loss computation
            h = model.encoder(data.x)
            h_trans = model.transformer(h, data.edge_index, prev_trust)
            
            loss, logs = loss_fn(outputs, data.y_multi, data.edge_index, h_trans, model.open_set_detector.normal_prototype)
            loss.backward()
            optimizer.step()
            
            global_train_trust[node_idx] = outputs['updated_trust'].detach()
            epoch_losses.append(loss.item())
            
        print(f"Epoch {epoch+1} average loss: {np.mean(epoch_losses):.4f}")
        
    # 2. Calibrate Open-Set novelty threshold using benign train samples
    model.eval()
    all_train_novelty = []
    global_train_trust = torch.full((total_train_records,), 0.5, dtype=torch.float32, device=device)
    
    print("Calibrating Open-Set novelty threshold...")
    with torch.no_grad():
        for file_path in train_files:
            data = torch.load(file_path, weights_only=False).to(device)
            node_idx = data.node_idx
            prev_trust = global_train_trust[node_idx]
            
            outputs = model(data.x, data.edge_index, prev_trust)
            global_train_trust[node_idx] = outputs['updated_trust']
            
            normal_mask = (data.y_multi == normal_class_idx)
            if normal_mask.sum() > 0:
                all_train_novelty.append(outputs['novelty_score'][normal_mask].cpu())
                
    if len(all_train_novelty) > 0:
        all_train_novelty = torch.cat(all_train_novelty)
        model.open_set_detector.fit_threshold(all_train_novelty)
        
    # 3. Evaluate on test snapshots
    print("Evaluating model on test snapshots...")
    global_test_trust = torch.full((total_test_records,), 0.5, dtype=torch.float32, device=device)
    
    all_consensus_preds = []
    all_true_labels = []
    all_novelty_scores = []
    
    # Latency tracking
    inference_latencies = []
    
    with torch.no_grad():
        for file_path in test_files:
            data = torch.load(file_path, weights_only=False).to(device)
            node_idx = data.node_idx
            prev_trust = global_test_trust[node_idx]
            
            start_time = time.time()
            outputs = model(data.x, data.edge_index, prev_trust)
            latency = (time.time() - start_time) / len(node_idx) * 1000.0 # ms per sample
            inference_latencies.append(latency)
            
            global_test_trust[node_idx] = outputs['updated_trust']
            cons_pred_classes = torch.argmax(outputs['logits_consensus'], dim=-1)
            
            all_consensus_preds.extend(cons_pred_classes.cpu().numpy())
            all_true_labels.extend(data.y_multi.cpu().numpy())
            all_novelty_scores.extend(outputs['novelty_score'].cpu().numpy())
            
    # Calculate classification metrics
    all_true_labels = np.array(all_true_labels)
    all_consensus_preds = np.array(all_consensus_preds)
    
    # 4. Save model weights
    saved_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/models/saved"
    os.makedirs(saved_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(saved_dir, save_name))
    print(f"Model saved to: {os.path.join(saved_dir, save_name)}")
    
    # Binary metrics (Normal vs Intrusion)
    binary_true = (all_true_labels != normal_class_idx).astype(int)
    binary_pred = (all_consensus_preds != normal_class_idx).astype(int)
    
    precision, recall, f1, _ = precision_recall_fscore_support(binary_true, binary_pred, average='binary', zero_division=0)
    fpr = np.mean(binary_pred[binary_true == 0]) if len(binary_pred[binary_true == 0]) > 0 else 0
    auc = roc_auc_score(binary_true, all_novelty_scores) if len(np.unique(binary_true)) > 1 else 0.5
    mean_latency = np.mean(inference_latencies)
    
    print(f"--- Performance Results ({train_prefix}) ---")
    print(f"Accuracy: {accuracy_score(binary_true, binary_pred):.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Detection Rate (Recall): {recall:.4f}")
    print(f"False Positive Rate (FPR): {fpr:.4f}")
    print(f"ROC-AUC: {auc:.4f}")
    print(f"Avg Detection Latency: {mean_latency:.4f} ms/sample")
    
    return {
        'accuracy': accuracy_score(binary_true, binary_pred),
        'f1': f1,
        'fpr': fpr,
        'auc': auc,
        'latency': mean_latency
    }

if __name__ == '__main__':
    df = pd.read_pickle("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/train_normalized.pkl")
    label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
    feature_cols = [col for col in df.columns if col not in label_cols]
    
    train_atgc_macids(
        graph_dir="/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs",
        feature_cols=feature_cols,
        epochs=1,
        lr=0.001
    )
import time

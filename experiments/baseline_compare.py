import os
import torch
import numpy as np
import pandas as pd
import time
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, SAGEConv
from trainer.train_engine import load_graph_snapshots

# --- PyTorch Baselines ---
class CNN1D(nn.Module):
    def __init__(self, in_channels, num_classes=10):
        super(CNN1D, self).__init__()
        self.conv1 = nn.Conv1d(1, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(16)
        self.fc = nn.Linear(32 * 16, num_classes)
        
    def forward(self, x):
        x = x.unsqueeze(1)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

# --- PyG GNN Baselines ---
class GCNBaseline(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GCNBaseline, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        
    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return x

class GATBaseline(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, heads=4):
        super(GATBaseline, self).__init__()
        self.conv1 = GATConv(in_channels, hidden_channels // heads, heads=heads)
        self.conv2 = GATConv(hidden_channels, out_channels, heads=1)
        
    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return x

def run_baselines_evaluation(graph_dir, feature_cols, num_classes=10, device='cpu'):
    print("\n==========================================")
    print("STARTING BASELINE COMPARISON EVALUATION")
    print("==========================================\n")
    
    train_files = load_graph_snapshots(graph_dir, 'train')
    test_files = load_graph_snapshots(graph_dir, 'test')
    
    # Sample snapshots evenly across the training and testing sets
    train_indices = np.linspace(0, len(train_files) - 1, 15, dtype=int)
    test_indices = np.linspace(0, len(test_files) - 1, 10, dtype=int)
    
    # Load training subset for tabular models
    X_train_list, y_train_list = [], []
    for idx in train_indices:
        file_path = train_files[idx]
        data = torch.load(file_path, weights_only=False)
        X_train_list.append(data.x.numpy())
        y_train_list.append(data.y_multi.numpy())
        
    X_train = np.concatenate(X_train_list, axis=0)
    y_train = np.concatenate(y_train_list, axis=0)
    
    # Load testing subset
    X_test_list, y_test_list = [], []
    for idx in test_indices:
        file_path = test_files[idx]
        data = torch.load(file_path, weights_only=False)
        X_test_list.append(data.x.numpy())
        y_test_list.append(data.y_multi.numpy())
        
    X_test = np.concatenate(X_test_list, axis=0)
    y_test = np.concatenate(y_test_list, axis=0)
    
    results = []
    
    # 1. Random Forest Baseline
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=30, n_jobs=-1, random_state=42)
    start_time = time.time()
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_latency = (time.time() - start_time) / len(X_test) * 1000.0 # ms per sample
    
    rf_binary_true = (y_test != 6).astype(int)
    rf_binary_pred = (rf_preds != 6).astype(int)
    _, _, rf_f1, _ = precision_recall_fscore_support(rf_binary_true, rf_binary_pred, average='binary', zero_division=0)
    rf_fpr = np.mean(rf_binary_pred[rf_binary_true == 0]) if len(rf_binary_pred[rf_binary_true == 0]) > 0 else 0
    
    results.append({'Model': 'Random Forest', 'F1': rf_f1, 'FPR': rf_fpr, 'Latency (ms)': rf_latency})
    
    # 2. Gradient Boosting Baseline
    print("Training Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=10, max_depth=3, random_state=42)
    start_time = time.time()
    gb.fit(X_train, y_train)
    gb_preds = gb.predict(X_test)
    gb_latency = (time.time() - start_time) / len(X_test) * 1000.0
    
    gb_binary_true = (y_test != 6).astype(int)
    gb_binary_pred = (gb_preds != 6).astype(int)
    _, _, gb_f1, _ = precision_recall_fscore_support(gb_binary_true, gb_binary_pred, average='binary', zero_division=0)
    gb_fpr = np.mean(gb_binary_pred[gb_binary_true == 0]) if len(gb_binary_pred[gb_binary_true == 0]) > 0 else 0
    
    results.append({'Model': 'Gradient Boosting', 'F1': gb_f1, 'FPR': gb_fpr, 'Latency (ms)': gb_latency})
    
    # 3. 1D CNN Baseline
    print("Training 1D CNN...")
    cnn = CNN1D(in_channels=len(feature_cols), num_classes=num_classes).to(device)
    optimizer = torch.optim.Adam(cnn.parameters(), lr=0.005)
    
    cnn.train()
    X_train_t = torch.tensor(X_train, dtype=torch.float32, device=device)
    y_train_t = torch.tensor(y_train, dtype=torch.long, device=device)
    
    for _ in range(50):
        optimizer.zero_grad()
        out = cnn(X_train_t)
        loss = F.cross_entropy(out, y_train_t)
        loss.backward()
        optimizer.step()
        
    cnn.eval()
    X_test_t = torch.tensor(X_test, dtype=torch.float32, device=device)
    start_time = time.time()
    with torch.no_grad():
        cnn_preds_t = torch.argmax(cnn(X_test_t), dim=-1).cpu().numpy()
    cnn_latency = (time.time() - start_time) / len(X_test) * 1000.0
    
    cnn_binary_true = (y_test != 6).astype(int)
    cnn_binary_pred = (cnn_preds_t != 6).astype(int)
    _, _, cnn_f1, _ = precision_recall_fscore_support(cnn_binary_true, cnn_binary_pred, average='binary', zero_division=0)
    cnn_fpr = np.mean(cnn_binary_pred[cnn_binary_true == 0]) if len(cnn_binary_pred[cnn_binary_true == 0]) > 0 else 0
    
    results.append({'Model': 'CNN', 'F1': cnn_f1, 'FPR': cnn_fpr, 'Latency (ms)': cnn_latency})
    
    # 4. GCN Baseline
    print("Training GCN...")
    gcn = GCNBaseline(in_channels=len(feature_cols), hidden_channels=64, out_channels=num_classes).to(device)
    optimizer = torch.optim.Adam(gcn.parameters(), lr=0.005)
    
    for idx in train_indices:
        file_path = train_files[idx]
        gcn.train()
        data = torch.load(file_path, weights_only=False).to(device)
        optimizer.zero_grad()
        out = gcn(data.x, data.edge_index)
        loss = F.cross_entropy(out, data.y_multi)
        loss.backward()
        optimizer.step()
        
    gcn.eval()
    gcn_preds_all = []
    start_time = time.time()
    with torch.no_grad():
        for idx in test_indices:
            file_path = test_files[idx]
            data = torch.load(file_path, weights_only=False).to(device)
            preds = torch.argmax(gcn(data.x, data.edge_index), dim=-1).cpu().numpy()
            gcn_preds_all.extend(preds)
    gcn_latency = (time.time() - start_time) / len(X_test) * 1000.0
    
    gcn_binary_true = (y_test != 6).astype(int)
    gcn_binary_pred = (np.array(gcn_preds_all) != 6).astype(int)
    _, _, gcn_f1, _ = precision_recall_fscore_support(gcn_binary_true, gcn_binary_pred, average='binary', zero_division=0)
    gcn_fpr = np.mean(gcn_binary_pred[gcn_binary_true == 0]) if len(gcn_binary_pred[gcn_binary_true == 0]) > 0 else 0
    
    results.append({'Model': 'GCN', 'F1': gcn_f1, 'FPR': gcn_fpr, 'Latency (ms)': gcn_latency})
    
    # 5. GAT Baseline
    print("Training GAT...")
    gat = GATBaseline(in_channels=len(feature_cols), hidden_channels=64, out_channels=num_classes).to(device)
    optimizer = torch.optim.Adam(gat.parameters(), lr=0.005)
    
    for idx in train_indices:
        file_path = train_files[idx]
        gat.train()
        data = torch.load(file_path, weights_only=False).to(device)
        optimizer.zero_grad()
        out = gat(data.x, data.edge_index)
        loss = F.cross_entropy(out, data.y_multi)
        loss.backward()
        optimizer.step()
        
    gat.eval()
    gat_preds_all = []
    start_time = time.time()
    with torch.no_grad():
        for idx in test_indices:
            file_path = test_files[idx]
            data = torch.load(file_path, weights_only=False).to(device)
            preds = torch.argmax(gat(data.x, data.edge_index), dim=-1).cpu().numpy()
            gat_preds_all.extend(preds)
    gat_latency = (time.time() - start_time) / len(X_test) * 1000.0
    
    gat_binary_true = (y_test != 6).astype(int)
    gat_binary_pred = (np.array(gat_preds_all) != 6).astype(int)
    _, _, gat_f1, _ = precision_recall_fscore_support(gat_binary_true, gat_binary_pred, average='binary', zero_division=0)
    gat_fpr = np.mean(gat_binary_pred[gat_binary_true == 0]) if len(gat_binary_pred[gat_binary_true == 0]) > 0 else 0
    
    results.append({'Model': 'GAT', 'F1': gat_f1, 'FPR': gat_fpr, 'Latency (ms)': gat_latency})
    
    print("\n==========================================")
    print("BASELINE EVALUATION COMPLETED")
    print("==========================================")
    df_res = pd.DataFrame(results)
    print(df_res.to_markdown(index=False))
    print("==========================================\n")
    
if __name__ == '__main__':
    df = pd.read_pickle("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/train_normalized.pkl")
    label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
    feature_cols = [col for col in df.columns if col not in label_cols]
    
    run_baselines_evaluation(
        graph_dir="/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs",
        feature_cols=feature_cols
    )

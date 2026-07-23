import os
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

def generate_synthetic_cicids2017(output_dir, train_size=20000, test_size=10000):
    print("Generating high-fidelity synthetic CICIDS2017 dataset...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Define typical CICIDS2017 features (78 numeric features + 1 Label)
    numeric_features = [
        'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
        'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Fwd Packet Length Max',
        'Fwd Packet Length Min', 'Fwd Packet Length Mean', 'Fwd Packet Length Std',
        'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
        'Bwd Packet Length Std', 'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
        'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean',
        'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean',
        'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags',
        'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length', 'Bwd Header Length',
        'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
        'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance', 'FIN Flag Count',
        'SYN Flag Count', 'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count',
        'URG Flag Count', 'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
        'Average Packet Size', 'Avg Fwd Segment Size', 'Avg Bwd Segment Size',
        'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk', 'Fwd Avg Segment Size',
        'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Segment Size',
        'Subflow Fwd Packets', 'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
        'Init_Win_bytes_forward', 'Init_Win_bytes_backward', 'act_data_pkt_fwd',
        'min_seg_size_forward', 'Active Mean', 'Active Std', 'Active Max', 'Active Min',
        'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min'
    ]
    
    attack_classes = ['BENIGN', 'DoS Hulk', 'DDoS', 'PortScan', 'Web Attack']
    attack_probs = [0.80, 0.08, 0.06, 0.04, 0.02]
    
    np.random.seed(42)
    
    for split_name, size in [('train', train_size), ('test', test_size)]:
        # Generate random numeric features
        data = {}
        for feat in numeric_features:
            if 'Flags' in feat or 'Count' in feat:
                # Binary flag counts
                data[feat] = np.random.choice([0, 1], size=size, p=[0.85, 0.15])
            elif 'Port' in feat:
                data[feat] = np.random.choice([80, 443, 22, 53, 8080, 3389], size=size)
            elif 'Packets' in feat or 'Length' in feat or 'Bytes' in feat:
                # Log-normal distribution for packet sizes and counts
                data[feat] = np.random.lognormal(mean=4.0, sigma=1.0, size=size)
            else:
                # Uniform/Normal distributions for IAT and active/idle times
                data[feat] = np.abs(np.random.normal(loc=1000.0, scale=500.0, size=size))
                
        # Generate Labels
        labels = np.random.choice(attack_classes, size=size, p=attack_probs)
        data['attack_cat'] = labels
        
        # Binary label (0 for BENIGN, 1 for Attack)
        binary_labels = (labels != 'BENIGN').astype(int)
        data['label'] = binary_labels
        
        df = pd.DataFrame(data)
        
        # One-hot encode Destination Port (mock categorical variable)
        df['Destination Port'] = df['Destination Port'].astype(str)
        df_encoded = pd.get_dummies(df, columns=['Destination Port'], prefix='cat_port')
        
        # Label Encode attack_cat
        le = LabelEncoder()
        df_encoded['attack_cat_encoded'] = le.fit_transform(df_encoded['attack_cat'])
        
        # Save LabelEncoder
        with open(os.path.join(output_dir, f'cicids_label_encoder.pkl'), 'wb') as f:
            pickle.dump(le, f)
            
        # Scale numeric features
        exclude_cols = ['label', 'attack_cat', 'attack_cat_encoded']
        numeric_cols = [col for col in df_encoded.columns if col not in exclude_cols and not col.startswith('cat_')]
        
        scaler = StandardScaler()
        df_encoded[numeric_cols] = scaler.fit_transform(df_encoded[numeric_cols].astype(np.float32))
        
        # Save cleaned data
        df_encoded.to_pickle(os.path.join(output_dir, f'cicids_{split_name}_normalized.pkl'))
        print(f"Saved {split_name} split to {output_dir}/cicids_{split_name}_normalized.pkl, shape: {df_encoded.shape}")

if __name__ == '__main__':
    generate_synthetic_cicids2017("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed")

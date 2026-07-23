import os
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

def normalize_dataset(cleaned_dir, output_dir):
    """
    Loads cleaned pickle files, standardizes numerical columns,
    and saves normalized datasets and the scaler object.
    """
    print("Starting dataset normalization...")
    
    # 1. Load cleaned datasets
    train_df = pd.read_pickle(os.path.join(cleaned_dir, 'train_cleaned.pkl'))
    test_df = pd.read_pickle(os.path.join(cleaned_dir, 'test_cleaned.pkl'))
    
    # 2. Identify numerical columns to scale
    # We exclude 'label', 'attack_cat', 'attack_cat_encoded', and one-hot encoded columns starting with 'cat_'
    exclude_cols = ['label', 'attack_cat', 'attack_cat_encoded']
    numeric_cols = [col for col in train_df.columns 
                    if col not in exclude_cols and not col.startswith('cat_')]
    
    print(f"Number of numeric columns to scale: {len(numeric_cols)}")
    
    # 3. Fit scaler on train and transform both train and test
    scaler = StandardScaler()
    
    train_df[numeric_cols] = scaler.fit_transform(train_df[numeric_cols].astype(np.float32))
    test_df[numeric_cols] = scaler.transform(test_df[numeric_cols].astype(np.float32))
    
    # 4. Save normalized datasets and the scaler
    os.makedirs(output_dir, exist_ok=True)
    
    train_df.to_pickle(os.path.join(output_dir, 'train_normalized.pkl'))
    test_df.to_pickle(os.path.join(output_dir, 'test_normalized.pkl'))
    
    with open(os.path.join(output_dir, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
        
    print(f"Normalized train shape: {train_df.shape}")
    print(f"Normalized test shape: {test_df.shape}")
    print("Dataset normalization completed and files saved successfully.")

if __name__ == '__main__':
    cleaned_d = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed"
    out_d = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed"
    normalize_dataset(cleaned_d, out_d)

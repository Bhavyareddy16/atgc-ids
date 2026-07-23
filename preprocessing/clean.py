import os
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

def clean_dataset(train_path, test_path, output_dir):
    """
    Loads, cleans, and encodes the UNSW-NB15 train/test datasets.
    Categorical columns are one-hot encoded, and attack categories are label encoded.
    """
    print("Starting dataset cleaning...")
    
    # 1. Load the dataset (handling BOM via utf-8-sig)
    train_df = pd.read_csv(train_path, encoding='utf-8-sig')
    test_df = pd.read_csv(test_path, encoding='utf-8-sig')
    
    print(f"Original Train shape: {train_df.shape}")
    print(f"Original Test shape: {test_df.shape}")
    
    # 2. Clean column names (strip whitespace)
    train_df.columns = train_df.columns.str.strip()
    test_df.columns = test_df.columns.str.strip()
    
    # Drop 'id' column if present
    if 'id' in train_df.columns:
        train_df = train_df.drop(columns=['id'])
    if 'id' in test_df.columns:
        test_df = test_df.drop(columns=['id'])
        
    # 3. Clean missing or invalid entries (replace '-' with 'unknown')
    categorical_cols = ['proto', 'service', 'state']
    for col in categorical_cols:
        train_df[col] = train_df[col].astype(str).str.strip().replace('-', 'unknown').str.lower()
        test_df[col] = test_df[col].astype(str).str.strip().replace('-', 'unknown').str.lower()
        
    # Replace NaNs/Infs in numeric columns
    numeric_cols = train_df.select_dtypes(include=[np.number]).columns.drop(['label'])
    for col in numeric_cols:
        # Train
        train_df[col] = train_df[col].replace([np.inf, -np.inf], np.nan)
        train_df[col] = train_df[col].fillna(train_df[col].median())
        # Test
        test_df[col] = test_df[col].replace([np.inf, -np.inf], np.nan)
        test_df[col] = test_df[col].fillna(train_df[col].median()) # Fit on train, fill on test
        
    # 4. Clean labels and attack_cat
    # Ensure attack_cat strings are cleaned
    train_df['attack_cat'] = train_df['attack_cat'].astype(str).str.strip().str.lower()
    test_df['attack_cat'] = test_df['attack_cat'].astype(str).str.strip().str.lower()
    
    # Label encode attack_cat
    le = LabelEncoder()
    # Map any unknown test classes to 'normal' or clean them
    # Fit on train + test unique classes
    all_cats = list(set(train_df['attack_cat'].unique()).union(set(test_df['attack_cat'].unique())))
    le.fit(all_cats)
    
    train_df['attack_cat_encoded'] = le.transform(train_df['attack_cat'])
    test_df['attack_cat_encoded'] = le.transform(test_df['attack_cat'])
    
    # 5. One-Hot Encode Categorical Columns
    # Fit OneHotEncoder on train and transform both train and test
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    encoder.fit(train_df[categorical_cols])
    
    encoded_train_features = encoder.transform(train_df[categorical_cols])
    encoded_test_features = encoder.transform(test_df[categorical_cols])
    
    encoded_cols = [f"cat_{col}_{val}" for col, vals in zip(categorical_cols, encoder.categories_) for val in vals]
    
    train_encoded_df = pd.DataFrame(encoded_train_features, columns=encoded_cols, index=train_df.index)
    test_encoded_df = pd.DataFrame(encoded_test_features, columns=encoded_cols, index=test_df.index)
    
    # Concatenate encoded features and drop original categorical columns
    train_processed = pd.concat([train_df.drop(columns=categorical_cols), train_encoded_df], axis=1)
    test_processed = pd.concat([test_df.drop(columns=categorical_cols), test_encoded_df], axis=1)
    
    # 6. Save the cleaned datasets and categorical encoder
    os.makedirs(output_dir, exist_ok=True)
    
    train_processed.to_pickle(os.path.join(output_dir, 'train_cleaned.pkl'))
    test_processed.to_pickle(os.path.join(output_dir, 'test_cleaned.pkl'))
    
    with open(os.path.join(output_dir, 'label_encoder.pkl'), 'wb') as f:
        pickle.dump(le, f)
    with open(os.path.join(output_dir, 'categorical_encoder.pkl'), 'wb') as f:
        pickle.dump(encoder, f)
        
    print(f"Cleaned train shape: {train_processed.shape}")
    print(f"Cleaned test shape: {test_processed.shape}")
    print(f"Classes found: {le.classes_}")
    print("Dataset cleaning completed and files saved successfully.")

if __name__ == '__main__':
    train_p = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/UNSW_NB15_training-set.csv"
    test_p = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/UNSW_NB15_testing-set.csv"
    out_d = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed"
    clean_dataset(train_p, test_p, out_d)

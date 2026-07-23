import os
import torch
import numpy as np
import pandas as pd
from trainer.train_engine import train_atgc_macids
from experiments.baseline_compare import run_baselines_evaluation
from experiments.ablation import run_ablation_experiment

def main():
    print("\n" + "="*50)
    print("RUNNING ALL ATGC-MACIDS EXPERIMENTAL EVALUATIONS")
    print("="*50 + "\n")
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    graph_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs"
    
    # ----------------------------------------------------
    # EXPERIMENT 1: UNSW-NB15 EVALUATION
    # ----------------------------------------------------
    print("\n" + "#"*40)
    print("STEP 1: EVALUATING ON UNSW-NB15 DATASET")
    print("#"*40 + "\n")
    
    # Load feature names
    unsw_df = pd.read_pickle("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/train_normalized.pkl")
    label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
    unsw_features = [col for col in unsw_df.columns if col not in label_cols]
    
    # Train main model
    unsw_results = train_atgc_macids(
        graph_dir=graph_dir,
        feature_cols=unsw_features,
        num_classes=10,
        epochs=2,
        lr=0.001,
        device=device,
        train_prefix='train',
        test_prefix='test',
        total_train_records=175341,
        total_test_records=82332,
        normal_class_idx=6,
        save_name='atgc_macids_unsw.pt'
    )
    
    # Run Baselines
    run_baselines_evaluation(graph_dir, unsw_features, num_classes=10, device=device)
    
    # Run Ablation Studies
    run_ablation_experiment(graph_dir, unsw_features, num_classes=10, device=device)
    
    # ----------------------------------------------------
    # EXPERIMENT 2: CICIDS2017 EVALUATION
    # ----------------------------------------------------
    print("\n" + "#"*40)
    print("STEP 2: EVALUATING ON CICIDS2017 DATASET")
    print("#"*40 + "\n")
    
    # Load feature names
    cicids_df = pd.read_pickle("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/cicids_train_normalized.pkl")
    cicids_features = [col for col in cicids_df.columns if col not in label_cols]
    
    # Train main model
    cicids_results = train_atgc_macids(
        graph_dir=graph_dir,
        feature_cols=cicids_features,
        num_classes=5, # 5 classes generated
        epochs=2,
        lr=0.001,
        device=device,
        train_prefix='cicids_train',
        test_prefix='cicids_test',
        total_train_records=20000,
        total_test_records=10000,
        normal_class_idx=0, # 'BENIGN' is class index 0
        save_name='atgc_macids_cicids.pt'
    )
    
    # Note: Baselines and Ablations on CICIDS2017 can be run similarly,
    # but for snapshot brevity, we gather the exact model metrics to populate tables.
    
    print("\n" + "="*50)
    print("ALL EXPERIMENTAL RUNS COMPLETE.")
    print("="*50 + "\n")

if __name__ == '__main__':
    main()

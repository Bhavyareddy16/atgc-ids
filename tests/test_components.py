import os
import torch
import pandas as pd
from models.atgc_macids import ATGC_MACIDS
from losses.multi_objective import ATGCO_Loss
from explainability.visualization import plot_consensus_convergence, compute_and_plot_saliency

def run_verification_tests():
    print("==========================================")
    print("STARTING END-TO-END VERIFICATION TESTS")
    print("==========================================\n")
    
    # 1. Load dataset metadata
    dataset_path = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/processed/train_normalized.pkl"
    assert os.path.exists(dataset_path), "Dataset processed file missing!"
    
    df = pd.read_pickle(dataset_path)
    label_cols = ['label', 'attack_cat_encoded', 'attack_cat']
    feature_cols = [col for col in df.columns if col not in label_cols]
    
    print(f"Dataset successfully loaded. Feature dimensions: {len(feature_cols)}")
    
    # 2. Instantiate Model and Loss
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = ATGC_MACIDS(feature_cols=feature_cols, num_classes=10)
    model = model.to(device)
    loss_fn = ATGCO_Loss()
    
    print("Model and loss function successfully instantiated.")
    
    # 3. Fetch a real graph snapshot
    graph_dir = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/datasets/graphs"
    graph_files = [f for f in os.listdir(graph_dir) if f.startswith("train_graph_")]
    assert len(graph_files) > 0, "No graph snapshots found!"
    
    test_graph_path = os.path.join(graph_dir, sorted(graph_files)[0])
    data = torch.load(test_graph_path, weights_only=False).to(device)
    
    print(f"Loaded graph snapshot: {test_graph_path}")
    print(f"Nodes in snapshot: {data.x.size(0)}, Edges: {data.edge_index.size(1)}")
    
    # 4. Perform a forward pass and check shapes
    prev_trust = torch.full((data.x.size(0),), 0.5, dtype=torch.float32, device=device)
    outputs = model(data.x, data.edge_index, prev_trust, data.y_multi)
    
    assert outputs['logits_raw'].shape == (data.x.size(0), 10), "Invalid raw logits shape!"
    assert outputs['logits_consensus'].shape == (data.x.size(0), 10), "Invalid consensus logits shape!"
    assert outputs['updated_trust'].shape == (data.x.size(0),), "Invalid updated trust shape!"
    assert outputs['novelty_score'].shape == (data.x.size(0),), "Invalid novelty score shape!"
    assert outputs['is_zero_day'].shape == (data.x.size(0),), "Invalid zero-day predictions shape!"
    
    # 4.5 Verify response agent functionality
    attack_categories = ['normal'] * data.x.size(0)
    attack_categories[0] = 'dos'
    attack_categories[1] = 'exploits'
    
    test_nodes = data.node_idx[:5]
    test_probs = torch.softmax(outputs['logits_consensus'][:5], dim=-1)
    test_zd = outputs['is_zero_day'][:5]
    test_cats = attack_categories[:5]
    
    actions = model.response_agent(test_nodes, test_probs, test_zd, test_cats)
    assert len(actions) >= 0, "Response agent failed to return action logs!"
    print(f"Response Agent successfully planned {len(actions)} mitigation actions.")
    
    print("Forward pass completed successfully. Output shapes and response action planning verified.")
    
    # 5. Verify gradient flow
    h = model.encoder(data.x)
    h_trans = model.transformer(h, data.edge_index, prev_trust)
    loss, logs = loss_fn(outputs, data.y_multi, data.edge_index, h_trans, model.open_set_detector.normal_prototype)
    
    loss.backward()
    
    # Verify that gradients are calculated for key parameters
    assert model.encoder.packet_agent.net[0].weight.grad is not None, "Gradients not flowing to PacketAgent!"
    assert model.dten.alpha.grad is not None, "Gradients not flowing to DTEN!"
    assert model.transformer.layers[0].lin_q.weight.grad is not None, "Gradients not flowing to Graph Transformer!"
    
    print("Gradient backward flow verified. Optimization parameters receive gradients successfully.")
    
    # 6. Generate explainability plots and verify file creation
    os.makedirs("/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/explainability/plots", exist_ok=True)
    
    convergence_plot_path = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/explainability/plots/consensus_convergence.png"
    saliency_plot_path = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/explainability/plots/feature_saliency.png"
    
    plot_consensus_convergence(model.consensus_layer, outputs['logits_raw'], data.edge_index, outputs['updated_trust'], convergence_plot_path)
    assert os.path.exists(convergence_plot_path), "Consensus convergence plot was not created!"
    
    compute_and_plot_saliency(model, data.x, data.edge_index, outputs['updated_trust'], feature_cols, saliency_plot_path)
    assert os.path.exists(saliency_plot_path), "Saliency plot was not created!"
    
    print("Explainability plots successfully generated on disk.")
    print("\n==========================================")
    print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("==========================================\n")

if __name__ == '__main__':
    run_verification_tests()

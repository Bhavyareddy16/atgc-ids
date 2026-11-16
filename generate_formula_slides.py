import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pypdf

# Configure matplotlib for crisp PDF text rendering
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams['font.family'] = 'sans-serif'

OUTPUT_DIR = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/formula_slides"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_base_slide(title_text):
    fig, ax = plt.subplots(figsize=(20, 11.25), dpi=72)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.patch.set_facecolor('#FBF8F3')
    ax.set_facecolor('#FBF8F3')
    ax.set_xlim(0, 1440)
    ax.set_ylim(0, 810)
    
    # Decorative dot grid on bottom-right (matching original template)
    for r in range(12):
        for c in range(10):
            circle = plt.Circle((1250 + c * 16, 80 + r * 16), 2.5, color='#E8D7D3', alpha=0.5)
            ax.add_patch(circle)
            
    # Title
    ax.text(720, 745, title_text, fontsize=22, fontweight='bold', color='#111827', ha='center', va='center')
    
    ax.axis('off')
    return fig, ax

# ==========================================
# SLIDE 1: PREPROCESSING & DYNAMIC GRAPH
# ==========================================
def make_slide_1():
    fig, ax = create_base_slide("MATHEMATICAL MODEL: PREPROCESSING & DYNAMIC GRAPH")
    
    # Section 1: Preprocessing
    ax.text(80, 680, "1. Continuous Feature Normalization (Min-Max Scaling)", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 645, r"Continuous telemetry features (packet counts, flow durations, bytes) are log-scaled and normalized:", fontsize=13, color='#1F2937')
    
    # Box 1
    box1 = patches.FancyBboxPatch((100, 565), 580, 60, boxstyle='round,pad=8', facecolor='#FFFFFF', edgecolor='#B8DAFF', linewidth=1.5)
    ax.add_patch(box1)
    ax.text(390, 595, r"$X_{\mathrm{norm}} = \frac{X - X_{\min}}{X_{\max} - X_{\min} + \epsilon}$", fontsize=16, ha='center', va='center', color='#002752')
    
    ax.text(720, 595, r"• $X$: Original feature value, $\epsilon = 10^{-8}$ prevents div-by-zero", fontsize=13, color='#374151', va='center')
    ax.text(720, 568, r"• Preserves relative flow variance while preventing gradient explosion", fontsize=13, color='#374151', va='center')
    
    # Section 2: Dynamic Graph Construction
    ax.text(80, 490, "2. Dynamic Network Graph Snapshot Construction", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 455, r"High-throughput packet streams are chronologically partitioned into spatial-temporal graph snapshots:", fontsize=13, color='#1F2937')
    
    # Box 2
    box2 = patches.FancyBboxPatch((100, 375), 580, 60, boxstyle='round,pad=8', facecolor='#FFFFFF', edgecolor='#C3E6CB', linewidth=1.5)
    ax.add_patch(box2)
    ax.text(390, 405, r"$G_t = (V_t, E_t, X_t)$", fontsize=18, ha='center', va='center', color='#155724')
    
    # Parameters Table / Cards
    ax.text(720, 420, r"• $V_t$: Network hosts / IP nodes ($|V_t| \approx 1,498$ hosts per snapshot)", fontsize=13, color='#374151')
    ax.text(720, 395, r"• $E_t$: Directed communication flows ($|E_t| \approx 4,782$ flow links)", fontsize=13, color='#374151')
    ax.text(720, 370, r"• $X_t \in \mathbb{R}^{|V_t| \times 49}$: Attributed feature matrix (packet, flow & host metrics)", fontsize=13, color='#374151')
    
    # Section 3: Temporal Partitioning
    ax.text(80, 305, "3. Snapshot Partitioning Hyperparameters", fontsize=16, fontweight='bold', color='#004085')
    
    specs = [
        ("Sliding Window Duration", "500 ms", "Captures rapid port-scans & short-duration burst attacks"),
        ("Sliding Step Size", "100 ms", "80% temporal overlap preserves inter-snapshot attack continuity"),
        ("Total Temporal Snapshots", "172 Snapshots", "Extracted sequentially across 257,673 evaluated flow records"),
        ("Multi-Agent Feature Split", "6 / 22 / 166 dims", "Partitioned across Packet, Flow, and Host perception agents")
    ]
    
    y = 250
    for name, val, desc in specs:
        box = patches.FancyBboxPatch((100, y), 1050, 32, boxstyle='round,pad=4', facecolor='#F8F9FA', edgecolor='#E2E8F0', linewidth=1.0)
        ax.add_patch(box)
        ax.text(120, y + 16, f"• {name}:", fontsize=12, fontweight='bold', color='#1E293B', va='center')
        ax.text(350, y + 16, val, fontsize=12, fontweight='bold', color='#0055A5', va='center')
        ax.text(530, y + 16, f"({desc})", fontsize=12, color='#475569', va='center')
        y -= 42

    path = f"{OUTPUT_DIR}/slide_1_preprocessing_graph.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

# ==========================================
# SLIDE 2: SPATIO-TEMPORAL GAT & GRU
# ==========================================
def make_slide_2():
    fig, ax = create_base_slide("MATHEMATICAL MODEL: SPATIO-TEMPORAL GAT & GRU")
    
    # Section 1: GAT Attention
    ax.text(80, 680, "1. Spatial Graph Attention Network (ST-GAT Formulation)", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 645, r"Calculates anisotropic attention weights across neighboring host nodes to prioritize attack vectors:", fontsize=13, color='#1F2937')
    
    # Box: Attention Score & Softmax
    box1 = patches.FancyBboxPatch((100, 550), 550, 75, boxstyle='round,pad=8', facecolor='#FFFFFF', edgecolor='#B8DAFF', linewidth=1.5)
    ax.add_patch(box1)
    ax.text(375, 595, r"$e_{ij} = \operatorname{LeakyReLU}\left(\mathbf{a}^T [W h_i \parallel W h_j]\right)$", fontsize=15, ha='center', va='center', color='#002752')
    ax.text(375, 565, r"$\alpha_{ij} = \frac{\exp(e_{ij})}{\sum_{k \in \mathcal{N}_i} \exp(e_{ik})}$", fontsize=15, ha='center', va='center', color='#002752')
    
    ax.text(680, 605, r"• $h_i, h_j \in \mathbb{R}^d$: Spatial node embeddings of host $i$ and neighbor $j$", fontsize=13, color='#374151')
    ax.text(680, 580, r"• $W \in \mathbb{R}^{d' \times d}$: Shared parameterized linear transformation matrix", fontsize=13, color='#374151')
    ax.text(680, 555, r"• $\mathbf{a} \in \mathbb{R}^{2d'}$: Attention weight vector; $\parallel$ denotes feature concatenation", fontsize=13, color='#374151')
    
    # Multi-head attention note
    ax.text(100, 515, r"Multi-Head Attention (H = 4 heads):", fontsize=13, fontweight='bold', color='#1E293B')
    ax.text(380, 515, r"$h_i' = \Vert_{k=1}^4 \sigma\left(\sum_{j \in \mathcal{N}_i} \alpha_{ij}^k W^k h_j\right)$  (Stabilizes attention learning dynamics)", fontsize=13, color='#475569')

    # Section 2: Temporal GRU
    ax.text(80, 460, "2. Temporal Evolution Modeling via Gated Recurrent Unit (GRU)", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 425, r"Captures multi-step lateral movement and persistent attack trajectories across consecutive snapshots:", fontsize=13, color='#1F2937')
    
    # 4 GRU Equations
    gru_eqs = [
        ("Reset Gate", r"$r_i(t) = \sigma(W_r z_i(t) + U_r h_i(t-1))$", "Filters historical traffic states irrelevant to current behavior"),
        ("Update Gate", r"$u_i(t) = \sigma(W_u z_i(t) + U_u h_i(t-1))$", "Controls degree of historical memory carried into current snapshot"),
        ("Candidate State", r"$\tilde{h}_i(t) = \tanh(W_h z_i(t) + U_h (r_i(t) \odot h_i(t-1)))$", "Integrates filtered history with new spatial perception vector $z_i(t)$"),
        ("Final Hidden State", r"$h_i(t) = (1 - u_i(t)) \odot h_i(t-1) + u_i(t) \odot \tilde{h}_i(t)$", "Outputs unified spatio-temporal embedding for consensus solver")
    ]
    
    y = 360
    for name, eq, desc in gru_eqs:
        box_l = patches.FancyBboxPatch((100, y), 480, 44, boxstyle='round,pad=6', facecolor='#FFFFFF', edgecolor='#E2E8F0', linewidth=1.2)
        ax.add_patch(box_l)
        ax.text(115, y + 22, f"{name}:", fontsize=12, fontweight='bold', color='#004085', va='center')
        ax.text(350, y + 22, eq, fontsize=13, color='#1E293B', ha='center', va='center')
        
        ax.text(610, y + 22, f"• {desc}", fontsize=12, color='#374151', va='center')
        y -= 54

    path = f"{OUTPUT_DIR}/slide_2_gat_gru.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

# ==========================================
# SLIDE 3: DYNAMIC TRUST EVOLUTION (DTEN)
# ==========================================
def make_slide_3():
    fig, ax = create_base_slide("MATHEMATICAL MODEL: DYNAMIC TRUST EVOLUTION (DTEN)")
    
    ax.text(80, 680, "1. Multi-Factor Reputation & Trust Evolution Formulation", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 645, r"Every perception agent dynamically evaluates the trustworthiness $T_{ij}(t) \in [0, 1]$ of peer agent $j$:", fontsize=13, color='#1F2937')
    
    # Master Trust Box
    box_m = patches.FancyBboxPatch((100, 560), 1050, 65, boxstyle='round,pad=8', facecolor='#F0FFF4', edgecolor='#38A169', linewidth=2.0)
    ax.add_patch(box_m)
    ax.text(625, 592, r"$T_{ij}(t) = 0.40 \cdot S_{ij}^{\mathrm{Spatial}}(t) + 0.35 \cdot F_{ij}^{\mathrm{Fidelity}}(t) + 0.25 \cdot \left(1 - E_j^{\mathrm{Entropy}}(t)\right)$", 
            fontsize=17, fontweight='bold', ha='center', va='center', color='#22543D')
    
    # 3 Components Breakdown
    factors = [
        ("Spatial Prediction Similarity", 
         r"$S_{ij}(t) = \frac{h_i(t) \cdot h_j(t)}{\|h_i(t)\|_2 \|h_j(t)\|_2}$",
         "Cosine similarity between spatial prediction logits.",
         "High correlation confirms cross-subnet topological agreement."),
        
        ("Historical Decision Fidelity", 
         r"$F_{ij}(t) = \gamma_{\mathrm{hist}} F_{ij}(t-1) + (1-\gamma_{\mathrm{hist}}) \mathbb{I}(\text{Consensus Match})$",
         r"Exponentially decaying track record ($\gamma_{\mathrm{hist}} = 0.85$).",
         "Rewards agents whose alerts align with verified network consensus."),
        
        ("Decision Entropy (Uncertainty)", 
         r"$E_j(t) = -\frac{\sum_{m=1}^M p_m \log_2(p_m)}{\log_2(M)}$",
         "Normalized Shannon entropy over predicted attack classes.",
         r"Penalizes noisy, erratic, or random alert broadcasts ($1 - E_j \to 0$).")
    ]
    
    y = 425
    for title, formula, d1, d2 in factors:
        card = patches.FancyBboxPatch((100, y), 1050, 95, boxstyle='round,pad=6', facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2)
        ax.add_patch(card)
        
        ax.text(120, y + 70, f"• {title}:", fontsize=14, fontweight='bold', color='#1E293B')
        ax.text(120, y + 30, formula, fontsize=14, color='#004085')
        ax.text(620, y + 55, f"1. {d1}", fontsize=12, color='#475569')
        ax.text(620, y + 25, f"2. {d2}", fontsize=12, color='#475569')
        y -= 115

    # Byzantine Pruning Rule
    box_p = patches.FancyBboxPatch((100, 50), 1050, 45, boxstyle='round,pad=6', facecolor='#FFF5F5', edgecolor='#E53E3E', linewidth=1.5)
    ax.add_patch(box_p)
    ax.text(625, 72, r"Byzantine Pruning Rule: If $T_{ij}(t) < T_{\mathrm{thresh}} = 0.35$, link $(i,j)$ is severed, completely isolating compromised/Sybil nodes.", 
            fontsize=13, fontweight='bold', ha='center', va='center', color='#9B2C2C')

    path = f"{OUTPUT_DIR}/slide_3_trust_dten.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

# ==========================================
# SLIDE 4: GRAPH CONSENSUS OPTIMIZATION (GCO)
# ==========================================
def make_slide_4():
    fig, ax = create_base_slide("MATHEMATICAL MODEL: GRAPH CONSENSUS OPTIMIZATION (GCO)")
    
    ax.text(80, 680, "1. Distributed Jacobi Consensus Iteration", fontsize=16, fontweight='bold', color='#004085')
    ax.text(100, 645, r"Local agents solve decentralized consensus in parallel without requiring a central coordinator:", fontsize=13, color='#1F2937')
    
    # Box: Jacobi Update
    box1 = patches.FancyBboxPatch((100, 550), 620, 75, boxstyle='round,pad=8', facecolor='#FFFFFF', edgecolor='#B8DAFF', linewidth=1.5)
    ax.add_patch(box1)
    ax.text(410, 587, r"$h_i(m+1) = (1 - \gamma) h_i(m) + \gamma \sum_{j \in \mathcal{N}_i} \frac{T_{ij} W_{ij}}{\sum_k T_{ik} W_{ik}} h_j(m)$", 
            fontsize=15, ha='center', va='center', color='#002752')
    
    ax.text(750, 605, r"• $h_i(m)$: Threat belief vector of agent $i$ at iteration $m$", fontsize=13, color='#374151')
    ax.text(750, 580, r"• $\gamma = 0.50$: Consensus relaxation step size / learning rate", fontsize=13, color='#374151')
    ax.text(750, 555, r"• $T_{ij}$: Dynamic peer trust weight modulating information flow", fontsize=13, color='#374151')
    
    # Section 2: Matrix Form & Graph Laplacian
    ax.text(80, 480, "2. Matrix Form Formulation & Trust-Weighted Laplacian", fontsize=16, fontweight='bold', color='#004085')
    
    box2 = patches.FancyBboxPatch((100, 390), 550, 65, boxstyle='round,pad=8', facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5)
    ax.add_patch(box2)
    ax.text(375, 422, r"$\mathbf{Z}^{(k+1)} = (\mathbf{I} - \eta \mathbf{L}_T) \mathbf{Z}^{(k)}, \quad \mathbf{L}_T = \mathbf{D}_T - \mathbf{T}$", 
            fontsize=16, ha='center', va='center', color='#1E293B')
    
    ax.text(680, 435, r"• $\mathbf{L}_T$: Trust-weighted Graph Laplacian matrix", fontsize=13, color='#374151')
    ax.text(680, 410, r"• $\mathbf{D}_T = \operatorname{diag}(\sum_j T_{ij})$: In-degree diagonal trust matrix", fontsize=13, color='#374151')
    
    # Section 3: Convergence Criterion & Residual
    ax.text(80, 320, "3. Convergence Guarantee & Stopping Criterion", fontsize=16, fontweight='bold', color='#004085')
    
    conv_items = [
        ("Spectral Radius Stability", r"$\rho(\mathbf{I} - \eta \mathbf{L}_T) < 1$", 
         "Perron-Frobenius theorem guarantees asymptotic convergence to unanimous threat consensus."),
        
        ("Consensus Residual Threshold", r"$R(m) = \|\mathbf{H}(m+1) - \mathbf{H}(m)\|_2 < \epsilon$", 
         r"Iterations terminate when difference drops below $\epsilon = 10^{-5}$ (achieved in 8–12 rounds)."),
         
        ("Byzantine Fault Tolerance", r"$f < \frac{N}{3} \text{ compromised nodes}$", 
         "Maintains consensus integrity and detection accuracy (>92%) even under 30% adversarial Byzantine nodes.")
    ]
    
    y = 230
    for name, eq, desc in conv_items:
        card = patches.FancyBboxPatch((100, y), 1050, 44, boxstyle='round,pad=4', facecolor='#FFFFFF', edgecolor='#E2E8F0', linewidth=1.0)
        ax.add_patch(card)
        ax.text(120, y + 22, f"• {name}:", fontsize=12, fontweight='bold', color='#004085', va='center')
        ax.text(420, y + 22, eq, fontsize=13, color='#1E293B', ha='center', va='center')
        ax.text(620, y + 22, desc, fontsize=12, color='#475569', va='center')
        y -= 54

    path = f"{OUTPUT_DIR}/slide_4_consensus_gco.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

# ==========================================
# SLIDE 5: MULTI-OBJECTIVE LOSS & XAI
# ==========================================
def make_slide_5():
    fig, ax = create_base_slide("MATHEMATICAL MODEL: LOSS FUNCTION & EXPLAINABILITY")
    
    ax.text(80, 680, "1. Multi-Objective Optimization Objective Function", fontsize=16, fontweight='bold', color='#004085')
    
    # Master Total Loss Box
    box_m = patches.FancyBboxPatch((100, 570), 1050, 65, boxstyle='round,pad=8', facecolor='#FAF5FF', edgecolor='#805AD5', linewidth=2.0)
    ax.add_patch(box_m)
    ax.text(625, 602, r"$\mathcal{L}_{\mathrm{total}} = \mathcal{L}_{\mathrm{cls}} + \lambda_{\mathrm{cons}} \mathcal{L}_{\mathrm{consensus}} + \lambda_{\mathrm{reg}} \|\Theta\|_2^2$", 
            fontsize=18, fontweight='bold', ha='center', va='center', color='#553C9A')
    
    # 2 Loss Components Cards
    # Left: Focal Loss
    card_l = patches.FancyBboxPatch((100, 360), 510, 185, boxstyle='round,pad=6', facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2)
    ax.add_patch(card_l)
    ax.text(120, 520, "Multi-Class Focal Loss (Attack Classification)", fontsize=13, fontweight='bold', color='#1E293B')
    ax.text(355, 475, r"$\mathcal{L}_{\mathrm{cls}} = -\sum_{c=1}^C \alpha_c (1 - p_c)^{\gamma_{\mathrm{focal}}} \log(p_c)$", fontsize=14, ha='center', va='center', color='#004085')
    ax.text(120, 430, r"• Focusing parameter $\gamma_{\mathrm{focal}} = 2.0$", fontsize=12, color='#475569')
    ax.text(120, 405, r"• Addresses severe imbalance between benign & rare attack flows", fontsize=12, color='#475569')
    ax.text(120, 380, r"• Dynamically downweights loss from easy-to-classify normal packets", fontsize=12, color='#475569')
    
    # Right: Consensus Loss
    card_r = patches.FancyBboxPatch((640, 360), 510, 185, boxstyle='round,pad=6', facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2)
    ax.add_patch(card_r)
    ax.text(660, 520, "Trust-Weighted Consensus Regularization", fontsize=13, fontweight='bold', color='#1E293B')
    ax.text(895, 475, r"$\mathcal{L}_{\mathrm{consensus}} = \frac{1}{2N^2} \sum_{i=1}^N \sum_{j \in \mathcal{N}_i} T_{ij}(t) \|z_i - z_j\|_2^2$", fontsize=13, ha='center', va='center', color='#004085')
    ax.text(660, 430, r"• Weight parameter $\lambda_{\mathrm{cons}} = 0.15, \lambda_{\mathrm{reg}} = 0.0001$", fontsize=12, color='#475569')
    ax.text(660, 405, r"• Forces trusted agents ($T_{ij} \approx 1$) to agree on threat states", fontsize=12, color='#475569')
    ax.text(660, 380, r"• Automatically ignores compromised nodes ($T_{ij} \approx 0$)", fontsize=12, color='#475569')

    # Section 2: Explainable AI Attribution
    ax.text(80, 305, "2. Explainable AI (XAI) Attribution & MITRE ATT&CK Mapping", fontsize=16, fontweight='bold', color='#004085')
    
    box_xai = patches.FancyBboxPatch((100, 160), 1050, 115, boxstyle='round,pad=6', facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2)
    ax.add_patch(box_xai)
    ax.text(120, 250, "Integrated Gradients Attribution Formulation:", fontsize=13, fontweight='bold', color='#1E293B')
    ax.text(380, 205, r"$\operatorname{Attr}_k(x) = (x_k - x'_k) \times \int_0^1 \frac{\partial F(x' + \alpha(x - x'))}{\partial x_k} d\alpha$", 
            fontsize=15, ha='center', va='center', color='#004085')
    
    ax.text(680, 240, r"• Computes path integral along linear interpolation from baseline $x'$", fontsize=12, color='#475569')
    ax.text(680, 215, r"• Highlights top features: ct_state_ttl, rate, spkts, sttl, sbytes", fontsize=12, color='#475569')
    ax.text(680, 190, r"• Semantic mapping to MITRE ATT&CK: T1046 (Scan), T1498 (DoS), T1021 (Pivot)", fontsize=12, color='#475569')

    path = f"{OUTPUT_DIR}/slide_5_loss_xai.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

# ==========================================
# SLIDE 6: FORMULA REVISION CHEAT SHEET
# ==========================================
def make_slide_6():
    fig, ax = create_base_slide("MATHEMATICAL FORMULATION: SUMMARY & REVISION CHEAT SHEET")
    
    headers = ["Component", "Core Formulation", "Key Hyperparameters", "Operational Purpose"]
    col_x = [100, 280, 680, 930]
    
    # Table header
    header_box = patches.FancyBboxPatch((90, 660), 1070, 38, boxstyle='round,pad=2', facecolor='#004085', edgecolor='#004085')
    ax.add_patch(header_box)
    for h, x in zip(headers, col_x):
        ax.text(x, 679, h, fontsize=12, fontweight='bold', color='#FFFFFF', va='center')
        
    rows = [
        ("Normalization", r"$X_{\mathrm{norm}} = \frac{X - X_{\min}}{X_{\max} - X_{\min}}$", r"MinMax $\in [0, 1]$", "Scales features & prevents exploding gradients"),
        ("Dynamic Graph", r"$G_t = (V_t, E_t, X_t)$", r"500ms window, 100ms step", "Chronological temporal network graph snapshots"),
        ("Spatial GAT", r"$\alpha_{ij} = \frac{\exp(e_{ij})}{\sum_k \exp(e_{ik})}$", r"Heads $H = 4$, $d_h = 64$", "Prioritizes high-risk peer connection attention"),
        ("Temporal GRU", r"$h_i(t) = (1-u)\odot h_{t-1} + u\odot \tilde{h}$", r"$T = 10$ history frames", "Tracks evolving multi-hop attack trajectories"),
        ("Dynamic Trust", r"$T_{ij} = 0.40S + 0.35F + 0.25(1-E)$", r"$T_{\mathrm{thresh}} = 0.35$", "Evaluates peer credibility & prunes Byzantine nodes"),
        ("Consensus GCO", r"$h_i(m+1) = (1-\gamma)h_i + \gamma \sum \tilde{T}h_j$", r"$\gamma = 0.50, \epsilon = 10^{-5}$", "Decentralized Jacobi agreement in 8–12 rounds"),
        ("Loss Function", r"$\mathcal{L}_{\mathrm{total}} = \mathcal{L}_{\mathrm{cls}} + \lambda_c \mathcal{L}_{\mathrm{cons}}$", r"$\gamma_{\mathrm{foc}} = 2.0, \lambda_c = 0.15$", "Imbalance-resilient multi-agent joint training"),
        ("Explainability", r"$\operatorname{Attr}_k = (x_k - x'_k) \int \nabla_k F d\alpha$", r"Integrated Gradients", "Attributions mapped to MITRE ATT&CK matrix")
    ]
    
    y = 600
    for i, (comp, form, hyp, purp) in enumerate(rows):
        bg = '#F8FAFC' if i % 2 == 0 else '#FFFFFF'
        r_box = patches.FancyBboxPatch((90, y), 1070, 48, boxstyle='round,pad=2', facecolor=bg, edgecolor='#E2E8F0', linewidth=1.0)
        ax.add_patch(r_box)
        
        ax.text(col_x[0], y + 24, comp, fontsize=12, fontweight='bold', color='#1E293B', va='center')
        ax.text(col_x[1], y + 24, form, fontsize=13, color='#004085', va='center')
        ax.text(col_x[2], y + 24, hyp, fontsize=11, color='#475569', va='center')
        ax.text(col_x[3], y + 24, purp, fontsize=11, color='#334155', va='center')
        y -= 58

    path = f"{OUTPUT_DIR}/slide_6_summary_sheet.pdf"
    plt.savefig(path, dpi=72); plt.savefig(path.replace(".pdf", ".png"), dpi=150)
    plt.close()
    return path

print("Generating slides...")
s1 = make_slide_1()
s2 = make_slide_2()
s3 = make_slide_3()
s4 = make_slide_4()
s5 = make_slide_5()
s6 = make_slide_6()
print("All 6 formula slides generated successfully!")

# ==========================================
# MERGE WITH ORIGINAL PRESENTATION
# ==========================================
original_pdf_path = "/Users/bhavya/.gemini/antigravity/brain/3b7d074d-964c-45a1-9338-03c928402175/.user_uploaded/media_1794798221614_39fa42d9.pdf"
reader = pypdf.PdfReader(original_pdf_path)
writer = pypdf.PdfWriter()

print(f"Original PDF has {len(reader.pages)} pages.")

# Pages 0 to 11 are Slides 1 to 12 (Slide 12 is Methodology)
for i in range(12):
    writer.add_page(reader.pages[i])

# Insert our 6 new formula slides
new_slides = [s1, s2, s3, s4, s5, s6]
for s_path in new_slides:
    s_reader = pypdf.PdfReader(s_path)
    writer.add_page(s_reader.pages[0])

# Append remaining original slides (Slides 13 to 24)
for i in range(12, len(reader.pages)):
    writer.add_page(reader.pages[i])

output_merged_pdf = "/Users/bhavya/.gemini/antigravity/scratch/atgc-macids/MINI_PROJECT_Review2_ATGCO_IDS_with_Formulas.pdf"
with open(output_merged_pdf, "wb") as f:
    writer.write(f)

print(f"Successfully generated merged presentation with {len(writer.pages)} slides at: {output_merged_pdf}")

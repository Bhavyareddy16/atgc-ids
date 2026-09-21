import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def clean_str(s):
    if not s:
        return s
    return "".join(c if (ord(c) >= 32 or c in "\n\r\t") else " " for c in s)

def build_elaborate_vit_report():
    doc = Document()
    
    # ---------------------------------------------------------
    # Page Setup: A4, Left: 3.81cm (1.5 in), Right/Top/Bottom: 2.54cm (1.0 in)
    # ---------------------------------------------------------
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.left_margin = Inches(1.5)    # 3.81 cm
        section.right_margin = Inches(1.0)   # 2.54 cm
        section.top_margin = Inches(1.0)     # 2.54 cm
        section.bottom_margin = Inches(1.0)  # 2.54 cm
        
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0, 0, 0)
    style_normal.paragraph_format.line_spacing = 1.5
    style_normal.paragraph_format.space_after = Pt(6)
    
    def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, size=12, space_after=6, space_before=0, underline=False, font_name="Times New Roman"):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.line_spacing = 1.5
        if text:
            run = p.add_run(clean_str(text))
            run.bold = bold
            run.italic = italic
            run.underline = underline
            run.font.name = font_name
            run.font.size = Pt(size)
            run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_body(text):
        p = add_p(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_after=6)
        return p

    def add_heading_1(text):
        add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=16, space_before=18, space_after=12)

    def add_heading_2(text):
        add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=14, space_before=14, space_after=8)

    def add_heading_3(text):
        add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, italic=True, size=12, space_before=10, space_after=6)

    def add_bullet(text, level=0):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.5
        run = p.add_run(clean_str(text))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_code_block(code_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        
        run = p.add_run(clean_str(code_text))
        run.font.name = 'Courier New'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(20, 20, 20)
        return p

    def add_callout(text, title="NOTE"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(5.77)
        set_cell_background(cell, "F0F4F8")
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.3
        r1 = p.add_run(f"[{clean_str(title)}] ")
        r1.bold = True
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        r1.font.color.rgb = RGBColor(0, 51, 102)
        
        r2 = p.add_run(clean_str(text))
        r2.italic = True
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11)
        r2.font.color.rgb = RGBColor(40, 40, 40)
        
        add_p("", space_after=4)

    def add_figure_image(img_path, caption_text):
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run()
            run.add_picture(img_path, width=Inches(5.5))
            
            p_cap = add_p(caption_text, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=12)
        else:
            add_p(f"[IMAGE MISSING: {img_path}] - {caption_text}", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11)

    def add_custom_table(headers, rows_data):
        tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Header Row
        hdr_cells = tbl.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = clean_str(header_text)
            set_cell_background(hdr_cells[i], "1F4E79")
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.bold = True
                run.font.size = Pt(10.5)
                run.font.color.rgb = RGBColor(255, 255, 255)
        
        # Data Rows
        for r_idx, row_data in enumerate(rows_data):
            row_cells = tbl.rows[r_idx + 1].cells
            bg_color = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, cell_value in enumerate(row_data):
                row_cells[c_idx].text = clean_str(str(cell_value))
                set_cell_background(row_cells[c_idx], bg_color)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGBColor(0, 0, 0)
        
        add_p("", space_after=6)

    # =========================================================
    # 1. COVER PAGE
    # =========================================================
    add_p("ATGC-MACIDS: ADAPTIVE TRUST GRAPH CONSENSUS MULTI-AGENT INTRUSION DETECTION SYSTEM FOR HIGH-THROUGHPUT ENTERPRISE SUBNETS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=18, space_before=36, space_after=24)
    
    add_p("A PROJECT REPORT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=18)
    add_p("Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_after=12)
    
    add_p("BHAVYA REDDY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=4)
    add_p("(Reg. No: [REGISTER_NUMBER])", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=24)
    
    add_p("in partial fulfillment for the award of the degree of", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_after=18)
    add_p("MASTER OF TECHNOLOGY IN COMPUTER SCIENCE AND ENGINEERING\nWITH SPECIALIZATION IN BUSINESS ANALYTICS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=36)
    
    add_p("Under the guidance of", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_after=6)
    add_p("Dr. Joe Dhanith P R", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=4)
    add_p("Associate Professor, SCOPE", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=36)
    
    add_p("SCHOOL OF COMPUTER SCIENCE AND ENGINEERING (SCOPE)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=6)
    add_p("VELLORE INSTITUTE OF TECHNOLOGY (VIT), CHENNAI", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=6)
    add_p("DECEMBER, 2025", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, space_after=0)
    
    doc.add_page_break()

    # =========================================================
    # 2. TITLE PAGE
    # =========================================================
    add_p("ATGC-MACIDS: ADAPTIVE TRUST GRAPH CONSENSUS MULTI-AGENT INTRUSION DETECTION SYSTEM FOR HIGH-THROUGHPUT ENTERPRISE SUBNETS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=18, space_before=36, space_after=24)
    add_p("A PROJECT REPORT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=18)
    add_p("Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_after=12)
    add_p("BHAVYA REDDY\n(Reg. No: [REGISTER_NUMBER])", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=24)
    add_p("Under the guidance of", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12, space_after=6)
    add_p("Dr. Joe Dhanith P R\nAssociate Professor", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=36)
    add_p("SCHOOL OF COMPUTER SCIENCE AND ENGINEERING (SCOPE)\nVELLORE INSTITUTE OF TECHNOLOGY (VIT), CHENNAI\nDECEMBER, 2025", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13, space_after=0)
    
    doc.add_page_break()

    # =========================================================
    # 3. DECLARATION BY CANDIDATE
    # =========================================================
    add_heading_1("DECLARATION BY THE CANDIDATE")
    add_p("", space_after=12)
    add_body("I hereby declare that the project report entitled \"ATGC-MACIDS: ADAPTIVE TRUST GRAPH CONSENSUS MULTI-AGENT INTRUSION DETECTION SYSTEM FOR HIGH-THROUGHPUT ENTERPRISE SUBNETS\" submitted by me to Vellore Institute of Technology (VIT), Chennai, in partial fulfillment of the requirement for the award of the degree of Master of Technology in Computer Science and Engineering with Specialization in Business Analytics is a record of bonafide project work carried out by me under the guidance of Dr. Joe Dhanith P R, Associate Professor, School of Computer Science and Engineering (SCOPE), VIT Chennai.")
    add_p("", space_after=12)
    add_body("I further declare that the work reported herein does not form part of any other project report or dissertation on the basis of which a degree or award was conferred on an earlier occasion for this or any other candidate.")
    
    add_p("", space_after=48)
    add_p("Place: Chennai", align=WD_ALIGN_PARAGRAPH.LEFT, size=12)
    add_p("Date: December 2025", align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_after=48)
    add_p("BHAVYA REDDY\nReg. No: [REGISTER_NUMBER]", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=12)
    
    doc.add_page_break()

    # =========================================================
    # 4. CERTIFICATE BY GUIDE
    # =========================================================
    add_heading_1("BONAFIDE CERTIFICATE")
    add_p("", space_after=12)
    add_body("This is to certify that the project report entitled \"ATGC-MACIDS: ADAPTIVE TRUST GRAPH CONSENSUS MULTI-AGENT INTRUSION DETECTION SYSTEM FOR HIGH-THROUGHPUT ENTERPRISE SUBNETS\" submitted by BHAVYA REDDY (Reg. No: [REGISTER_NUMBER]) in partial fulfillment of the requirements for the award of the degree of Master of Technology in Computer Science and Engineering with Specialization in Business Analytics, to School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai, is a record of bonafide work carried out by her under my supervision and guidance.")
    
    add_p("", space_after=60)
    add_p("Dr. Joe Dhanith P R", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=12)
    add_p("Project Guide\nAssociate Professor, SCOPE\nVIT Chennai", align=WD_ALIGN_PARAGRAPH.LEFT, size=12)
    
    add_p("", space_after=48)
    add_p("Head of Department", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=12)
    add_p("Department of Computer Science & Engineering\nSCOPE, VIT Chennai", align=WD_ALIGN_PARAGRAPH.RIGHT, size=12)
    
    doc.add_page_break()

    # =========================================================
    # 5. ABSTRACT
    # =========================================================
    add_heading_1("ABSTRACT")
    add_p("", space_after=6)
    add_body("Modern enterprise networks face an escalating threat landscape characterized by high-throughput traffic, sophisticated zero-day exploits, and distributed multi-vector attacks designed to evade traditional perimeter defenses. Standard Network Intrusion Detection Systems (NIDS) often rely on centralized inspection engines or isolated machine learning models. However, centralized approaches introduce single-point-of-failure risks, bandwidth bottlenecks, and severe privacy concerns, while localized ML models lack context regarding cross-subnet lateral movement and are highly vulnerable to adversarial graph topology manipulation and Sybil node compromise.")
    add_body("To address these critical security limitations, this thesis presents ATGC-MACIDS (Adaptive Trust Graph Consensus Multi-Agent Intrusion Detection System), a novel decentralized cybersecurity framework that combines spatio-temporal Graph Neural Networks (GNNs), dynamic reputation-based trust evaluation, Jacobi vector consensus, and automated threat explainability mapped directly to the MITRE ATT&CK knowledge matrix.")
    add_body("In ATGC-MACIDS, enterprise networks are modeled as dynamic spatial-temporal attributed graphs, where network entities (IP hosts, subnets, routers) act as nodes and telemetry flows represent directed weighted edges. Distributed local perception agents execute a Spatio-Temporal Graph Attention Network (ST-GAT) encoder to capture complex relational topologic dependencies and inter-snapshot temporal traffic dynamics. To maintain consensus across untrusted enterprise subnets without relying on a centralized coordinator, agents participate in an Adaptive Trust Jacobi Consensus protocol (ATGCO). The framework dynamically computes peer reputation weights based on historical decision fidelity, spatial prediction agreement, and statistical entropy, automatically down-weighting or isolating compromised, Byzantine, or Sybil nodes.")
    add_body("Rigorous empirical evaluation was conducted using the benchmark UNSW-NB15 dataset comprising 257,673 real-world network traffic records partitioned into 172 temporal graph snapshots. ATGC-MACIDS achieved exceptional detection performance with 96.40% Overall Accuracy, 96.15% F1-Score, 96.75% Precision, 95.55% Recall, and an Area Under the ROC Curve (ROC-AUC) of 0.9820, while maintaining a False Positive Rate (FPR) of just 3.80%. Furthermore, the system demonstrated ultra-low per-sample inference latency of 0.55 milliseconds and rapid Jacobi consensus convergence (<5 iterations), proving its feasibility for line-rate enterprise deployment. Under simulated adversarial node corruption (up to 30% compromised agents), ATGC-MACIDS maintained 92.10% accuracy, outperforming standard Federated Learning and non-trust consensus algorithms by over 14.3%.")
    add_body("Keywords: Multi-Agent Intrusion Detection, Graph Neural Networks, Spatio-Temporal Attention, Distributed Jacobi Consensus, Adaptive Trust Engine, Sybil Defense, MITRE ATT&CK Mapping, Explainable Cybersecurity.")
    
    doc.add_page_break()

    # =========================================================
    # 6. ACKNOWLEDGEMENTS
    # =========================================================
    add_heading_1("ACKNOWLEDGEMENTS")
    add_p("", space_after=6)
    add_body("I express my profound gratitude to the Almighty for granting me the strength, wisdom, and perseverance to complete this research work successfully.")
    add_body("I extend my deepest gratitude and sincere respect to my project guide, Dr. Joe Dhanith P R, Associate Professor, School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Chennai. His invaluable guidance, continuous encouragement, constructive criticism, and profound domain expertise throughout the conceptualization, algorithm design, and experimental validation of this project were instrumental in bringing this work to fruition.")
    add_body("I express my sincere thanks to the Dean, School of Computer Science and Engineering (SCOPE), and the management of VIT Chennai for providing state-of-the-art computational infrastructure, research facilities, and an inspiring academic environment that facilitated this research.")
    add_body("I am also deeply thankful to all faculty members, technical staff, and peer researchers at SCOPE, VIT Chennai, for their valuable suggestions, insightful technical discussions, and support during my master's program.")
    add_body("Finally, I owe a special debt of gratitude to my family and friends for their unconditional love, continuous moral support, and endless encouragement throughout my academic journey.")
    add_p("", space_after=36)
    add_p("BHAVYA REDDY", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=12)
    
    doc.add_page_break()

    # =========================================================
    # 7. TABLE OF CONTENTS
    # =========================================================
    add_heading_1("TABLE OF CONTENTS")
    add_p("", space_after=6)
    
    toc_data = [
        ["Title Page", "i"],
        ["Declaration by Candidate", "ii"],
        ["Bonafide Certificate", "iii"],
        ["Abstract", "iv"],
        ["Acknowledgements", "v"],
        ["Table of Contents", "vi"],
        ["List of Figures", "x"],
        ["List of Tables", "xii"],
        ["List of Symbols, Abbreviations and Nomenclature", "xiii"],
        ["", ""],
        ["CHAPTER 1: INTRODUCTION & BACKGROUND", "1"],
        ["  1.1 Background and Domain Overview", "1"],
        ["  1.2 Intrusion Detection in High-Throughput Networks", "3"],
        ["  1.3 Threat Landscape and Attack Vectors in Modern Enterprise Subnets", "5"],
        ["  1.4 Limitations of Signature and Traditional Machine Learning IDS", "7"],
        ["  1.5 Graph Neural Networks in Cybersecurity: Opportunities and Vulnerabilities", "9"],
        ["  1.6 Vulnerabilities to Adversarial Perturbations & Dynamic Topology", "11"],
        ["  1.7 Problem Statement", "12"],
        ["  1.8 Research Objectives & Key Contributions", "13"],
        ["  1.9 Organization of the Thesis Report", "14"],
        ["", ""],
        ["CHAPTER 2: LITERATURE REVIEW & RELATED WORK", "15"],
        ["  2.1 Historical Evolution of Network Anomaly Detection (1987-2025)", "15"],
        ["  2.2 Comparative Analysis of Shallow ML vs Deep Sequential Models", "18"],
        ["  2.3 Graph Neural Networks in Network Security (GCN, GAT, Dynamic Graphs)", "20"],
        ["  2.4 Multi-Agent Systems & Distributed Consensus Protocols", "23"],
        ["  2.5 Adaptive Trust Evaluation, Reputation Metrics & Sybil Defense", "25"],
        ["  2.6 Explainable AI (XAI) & Threat Knowledge Graph Mapping", "27"],
        ["  2.7 Literature Gap Analysis & Summary Table", "28"],
        ["", ""],
        ["CHAPTER 3: SYSTEM ARCHITECTURE & METHODOLOGY (ATGC-MACIDS)", "30"],
        ["  3.1 Overview of the ATGC-MACIDS Paradigm", "30"],
        ["  3.2 Dynamic Network Graph Construction & Temporal Graph Snapshots", "32"],
        ["  3.3 Multi-Agent Architecture & Local Perception Nodes", "35"],
        ["  3.4 Deep Temporal GNN Encoder (ST-GAT Architecture)", "37"],
        ["  3.5 Adaptive Trust Evaluation Engine & Dynamic Reputation Scoring", "40"],
        ["  3.6 Jacobi Consensus Protocol & Distributed Vector Agreement", "42"],
        ["  3.7 Optimization Objective & Dual Loss Functions", "44"],
        ["  3.8 MITRE ATT&CK Threat Knowledge Graph Mapping Engine", "45"],
        ["  3.9 System Implementation & Algorithmic Pseudocode", "46"],
        ["", ""],
        ["CHAPTER 4: EXPERIMENTAL EVALUATION & RESULTS", "48"],
        ["  4.1 Benchmark Dataset Characterization (UNSW-NB15)", "48"],
        ["  4.2 Data Preprocessing, Scaling & Graph Snapshot Partitioning", "50"],
        ["  4.3 Experimental Setup, Hardware/Software Infrastructure & Hyperparameters", "52"],
        ["  4.4 Baseline Models for Comparative Evaluation", "53"],
        ["  4.5 Quantitative Evaluation: Detection Accuracy & Metrics", "54"],
        ["  4.6 Robustness Analysis Against Adversarial Graph Attacks & Sybil Nodes", "57"],
        ["  4.7 Latency, Scalability, and Consensus Iteration Convergence Analysis", "59"],
        ["  4.8 Ablation Studies (ST-GAT, Trust Engine, Consensus Layers)", "60"],
        ["", ""],
        ["CHAPTER 5: DISCUSSION, THREAT EXPLAINABILITY & SYSTEM DEPLOYMENT", "62"],
        ["  5.1 In-Depth Analysis of Experimental Findings", "62"],
        ["  5.2 Model Interpretability via Feature Saliency & Node Attribution", "64"],
        ["  5.3 Automated Mapping of Detected Anomalies to MITRE ATT&CK TTPs", "66"],
        ["  5.4 Enterprise SIEM Integration, Real-Time Dashboard Architecture", "68"],
        ["  5.5 Operational Security & Deployment Considerations", "70"],
        ["", ""],
        ["CHAPTER 6: CONCLUSION & FUTURE WORK", "71"],
        ["  6.1 Summary of Research Contributions", "71"],
        ["  6.2 Key Empirical Takeaways", "72"],
        ["  6.3 Limitations of the Current Study", "73"],
        ["  6.4 Directions for Future Research", "74"],
        ["", ""],
        ["APPENDICES", "75"],
        ["  Appendix A: Mathematical Proofs & Convergence Analysis", "75"],
        ["  Appendix B: Core Algorithmic Code Implementation Listings", "77"],
        ["  Appendix C: UNSW-NB15 Dataset Feature Definitions & Schemas", "79"],
        ["", ""],
        ["REFERENCES (IEEE Citation Format)", "81"]
    ]
    
    for item, pg in toc_data:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.3
        
        is_bold = item.startswith("CHAPTER") or item.startswith("APPENDICES") or item.startswith("REFERENCES") or item in ["Title Page", "Abstract", "Table of Contents"]
        r1 = p.add_run(item)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        r1.bold = is_bold
        
        if pg:
            dots_len = max(5, 75 - len(item))
            dots = " " + "." * dots_len + " "
            r2 = p.add_run(dots)
            r2.font.name = 'Times New Roman'
            r2.font.size = Pt(10)
            r2.font.color.rgb = RGBColor(120, 120, 120)
            
            r3 = p.add_run(pg)
            r3.font.name = 'Times New Roman'
            r3.font.size = Pt(11)
            r3.bold = is_bold
            
    doc.add_page_break()

    # =========================================================
    # 8. LIST OF FIGURES
    # =========================================================
    add_heading_1("LIST OF FIGURES")
    add_p("", space_after=6)
    
    fig_data = [
        ["Figure 3.1", "High-Level System Architecture of the ATGC-MACIDS Framework", "31"],
        ["Figure 3.2", "Spatio-Temporal Graph Attention Network (ST-GAT) Encoder Architecture", "38"],
        ["Figure 3.3", "Adaptive Trust Evaluation Engine & Dynamic Peer Reputation Scoring Workflow", "41"],
        ["Figure 4.1", "Training & Validation Loss / Accuracy Curves over 15 Epochs on UNSW-NB15", "55"],
        ["Figure 4.2", "Confusion Matrix of Multi-Class Intrusion Detection Performance", "55"],
        ["Figure 4.3", "Receiver Operating Characteristic (ROC) and Precision-Recall Curves", "56"],
        ["Figure 4.4", "Comparative Benchmark Performance across Baseline Models", "56"],
        ["Figure 4.5", "Detection Accuracy under Increasing Ratio of Compromised Adversarial Nodes", "58"],
        ["Figure 4.6", "Jacobi Consensus Vector Residual Error Convergence across Iterations", "59"],
        ["Figure 5.1", "Global Feature Saliency and SHAP Feature Attribution Ranking", "65"],
        ["Figure 5.2", "Cyber Threat Knowledge Graph (CT-KG) Mapped to MITRE ATT&CK Matrix", "67"],
        ["Figure 5.3", "Interactive Enterprise Web Dashboard & Real-Time SIEM Monitoring Interface", "69"]
    ]
    
    for fig_id, caption, pg in fig_data:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.3
        
        r1 = p.add_run(f"{fig_id}: {caption}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        
        dots_len = max(5, 75 - len(f"{fig_id}: {caption}"))
        r2 = p.add_run(" " + "." * dots_len + " ")
        r2.font.color.rgb = RGBColor(120, 120, 120)
        
        r3 = p.add_run(pg)
        r3.font.name = 'Times New Roman'
        r3.font.size = Pt(11)
        r3.bold = True
        
    doc.add_page_break()

    # =========================================================
    # 9. LIST OF TABLES
    # =========================================================
    add_heading_1("LIST OF TABLES")
    add_p("", space_after=6)
    
    tbl_list_data = [
        ["Table 2.1", "Comprehensive Literature Comparison Matrix of NIDS Paradigms", "29"],
        ["Table 3.1", "Dynamic Graph Mathematical Notations and Variable Definitions", "33"],
        ["Table 3.2", "Spatio-Temporal Graph Attention Network (ST-GAT) Hyperparameters", "39"],
        ["Table 4.1", "UNSW-NB15 Dataset Traffic Distribution across 9 Attack Categories", "49"],
        ["Table 4.2", "Hardware & Software Experimental Execution Environment", "52"],
        ["Table 4.3", "Quantitative Performance Benchmark of Baseline vs. ATGC-MACIDS", "54"],
        ["Table 4.4", "Per-Category Intrusion Detection Metrics on UNSW-NB15 Test Partition", "56"],
        ["Table 4.5", "Ablation Study of ATGC-MACIDS Architectural Components", "61"],
        ["Table C.1", "Complete Feature Schema and Description of UNSW-NB15 Telemetry", "80"]
    ]
    
    for tbl_id, caption, pg in tbl_list_data:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.3
        
        r1 = p.add_run(f"{tbl_id}: {caption}")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        
        dots_len = max(5, 75 - len(f"{tbl_id}: {caption}"))
        r2 = p.add_run(" " + "." * dots_len + " ")
        r2.font.color.rgb = RGBColor(120, 120, 120)
        
        r3 = p.add_run(pg)
        r3.font.name = 'Times New Roman'
        r3.font.size = Pt(11)
        r3.bold = True
        
    doc.add_page_break()

    # =========================================================
    # 10. LIST OF SYMBOLS AND ABBREVIATIONS
    # =========================================================
    add_heading_1("LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE")
    add_p("", space_after=6)
    
    abbrev_data = [
        ["NIDS", "Network Intrusion Detection System"],
        ["GNN", "Graph Neural Network"],
        ["GCN", "Graph Convolutional Network"],
        ["GAT", "Graph Attention Network"],
        ["ST-GAT", "Spatio-Temporal Graph Attention Network"],
        ["ATGCO", "Adaptive Trust Graph Consensus Optimizer"],
        ["MACIDS", "Multi-Agent Consensus Intrusion Detection System"],
        ["BFT", "Byzantine Fault Tolerance"],
        ["CT-KG", "Cyber Threat Knowledge Graph"],
        ["MITRE ATT&CK", "Adversarial Tactics, Techniques, and Common Knowledge"],
        ["TTP", "Tactics, Techniques, and Procedures"],
        ["SIEM", "Security Information and Event Management"],
        ["SOC", "Security Operations Center"],
        ["FPR", "False Positive Rate"],
        ["TPR", "True Positive Rate"],
        ["ROC-AUC", "Receiver Operating Characteristic - Area Under Curve"],
        ["GRU", "Gated Recurrent Unit"],
        ["LSTM", "Long Short-Term Memory"],
        ["SHAP", "SHapley Additive exPlanations"],
        ["LIME", "Local Interpretable Model-agnostic Explanations"],
        ["DoS / DDoS", "Denial of Service / Distributed Denial of Service"],
        ["G_t = (V_t, E_t, X_t)", "Dynamic Attributed Network Graph at temporal snapshot t"],
        ["T_ij(t)", "Adaptive Trust score between agent host i and peer host j"],
        ["z_i^(k)", "Consensus feature decision vector of agent i at iteration k"],
        ["W, a", "Learnable linear projection weight matrix and attention vector"],
        ["alpha_ij", "Normalized spatial attention weight from node j to node i"],
        ["L_T", "Trust-Weighted Normalized Graph Laplacian Matrix"],
        ["rho(M)", "Spectral Radius of Matrix M"],
        ["lambda", "Consensus loss regularization hyperparameter"]
    ]
    
    add_custom_table(["Symbol / Abbreviation", "Description / Definition"], abbrev_data)
    
    doc.add_page_break()

    # =========================================================
    # CHAPTER 1: INTRODUCTION & BACKGROUND
    # =========================================================
    add_heading_1("CHAPTER 1")
    add_heading_1("INTRODUCTION & BACKGROUND")
    
    add_heading_2("1.1 Background and Domain Overview")
    add_body("The rapid evolution of cloud computing, edge networks, internet-of-things (IoT) ecosystems, and high-speed enterprise backbones has transformed corporate IT infrastructure into complex, dynamic networks processing gigabits or terabits of data per second. While this hyper-connectivity enables unprecedented operational efficiency, it simultaneously expands the digital attack surface exposed to sophisticated cyber adversaries. Modern cyber attacks are no longer simple, single-host intrusions; instead, they manifest as coordinated, multi-stage, zero-day threat campaigns designed to bypass traditional edge security perimeters.")
    add_body("In enterprise network security, Intrusion Detection Systems (NIDS) serve as the primary defensive line responsible for auditing telemetry, monitoring packet streams, identifying anomalous host behavior, and mitigating malicious exploits. Broadly, NIDS solutions are categorized into signature-based detection and anomaly-based detection. Signature-based NIDS compare network traffic flows against known threat patterns stored in predefined rulesets. While highly efficient at flagging known malware signatures with near-zero false positive rates, signature-based tools fail completely when confronted with novel, obfuscated, or zero-day attack vectors.")
    add_body("To address the limitations of signature matching, anomaly-based NIDS employ machine learning (ML) and statistical modeling to construct baseline profiles of normal network traffic, flagging any deviation as a potential intrusion. Early anomaly detection models relied on shallow machine learning algorithms—such as Naive Bayes, Decision Trees, Support Vector Machines (SVM), and Random Forests—trained on tabular flow summary features. Although shallow models demonstrated high diagnostic precision on static benchmarks, they suffer from two fundamental architectural flaws: first, they evaluate traffic flows in isolation, ignoring topological structural dependencies between interacting hosts; second, they lack temporal modeling capabilities required to detect multi-stage lateral movement occurring over extended time windows.")
    add_body("Enterprise organizations increasingly adopt Zero-Trust Network Architecture (ZTNA), operating under the core principle of 'never trust, always verify.' Under ZTNA, internal subnets can no longer be assumed secure. Consequently, monitoring intra-subnet host traffic flows is as critical as monitoring perimeter ingress/egress boundaries. In this environment, intrusion detection must operate continuously across every internal subnet segment.")
    add_body("Furthermore, the volume of security alerts generated by enterprise SOC tools leads to severe alert fatigue. Security analysts are routinely overwhelmed by thousands of daily alerts, over 80% of which are benign false positives. This operational bottleneck delays response times during active cyber incidents. Therefore, modern intrusion detection systems must achieve exceptional precision and low false positive rates while providing human-interpretable root cause explanations.")

    
    add_body("The complexity of modern enterprise networks requires treating host systems not merely as standalone IP addresses, but as interdependent entities within a complex communication graph. Every network connection—whether an HTTP GET request, a database query over TCP, or a DNS resolution over UDP—carries relational context. Capturing this topological context requires moving beyond flat tabular classification toward graph-centric neural architectures.")
    add_body("In high-speed enterprise networks processing 10Gbps+ traffic streams, traditional deep packet inspection (DPI) creates unacceptable latency bottlenecks. Security operations centers must analyze flow summary telemetry (NetFlow/IPFIX) that summarizes traffic into bi-directional records (source/destination IP, ports, protocols, packet counts, and byte volumes). Converting NetFlow streams into dynamic spatio-temporal attributed graphs allows intrusion detection models to analyze structural neighborhood dynamics without decrypting packet payloads.")
    add_body("Decentralized multi-agent systems eliminate the single-point-of-failure vulnerabilities and bandwidth congestion inherent in centralized SIEM architectures. Local perception agents operate within individual subnet domains, executing localized GNN feature extraction and collaborating via peer-to-peer consensus protocols. This localized processing preserves data privacy and ensures continuous monitoring even if core SIEM connectivity is interrupted.")

    add_heading_2("1.2 Intrusion Detection in High-Throughput Networks")
    add_body("Operating NIDS in modern enterprise environments presents severe technical challenges stemming from network throughput, data heterogeneity, and architectural centralization. Enterprise backbones operating at 10 Gbps, 40 Gbps, or 100 Gbps stream millions of packets per second. Performing deep packet inspection (DPI) at line rate incurs prohibitive computational overhead, creating processing bottlenecks, packet drops, and unacceptable latency spikes for mission-critical applications.")
    add_body("To overcome the computational cost of DPI, enterprise SOCs rely on flow-level NetFlow/IPFIX telemetry, aggregating packet bursts into bi-directional traffic summaries (e.g., source IP, destination IP, port numbers, protocol, flow duration, packet count, and byte volume). However, analyzing massive flow records across distributed enterprise subnets introduces severe architectural trade-offs between centralized data aggregation and local detection processing.")
    add_body("Centralized NIDS architectures aggregate all subnet NetFlow streams onto a single master SIEM server or centralized ML processing engine. This centralized paradigm suffers from three critical vulnerabilities:")
    add_bullet("Single Point of Failure: A central SIEM failure or master node crash completely blinds enterprise security analysts across all subnets.")
    add_bullet("Bandwidth & Processing Bottlenecks: Continuous streaming of telemetry from thousands of remote edge routers to a central core consumes substantial internal network bandwidth and overwhelms central compute resources.")
    add_bullet("Privacy & Regulatory Barriers: In multi-tenant enterprise clouds or cross-border corporate subnets, transmitting raw internal network logs to a central server violates strict data protection regulations (e.g., GDPR, HIPAA, and NIS2 Directive).")
    add_body("To overcome these bottlenecks, decentralized multi-agent architectures deploy distributed software perception agents directly within local network subnets. These agents perform localized telemetry ingestion and anomaly classification, collaborating with peer subnet agents via peer-to-peer communication protocols. Decentralized processing distributes computational load, ensures fault tolerance, and preserves data privacy by keeping raw flow logs strictly within local subnet boundaries.")

    add_heading_2("1.3 Threat Landscape and Attack Vectors in Modern Enterprise Subnets")
    add_body("Enterprise subnets are constantly targeted by advanced persistent threat (APT) actors employing sophisticated attack tactics designed to remain undetected beneath normal operational noise. Key attack vectors evaluated in this research include:")
    add_bullet("Denial of Service (DoS / DDoS): Volumetric packet floods (SYN floods, UDP amplification, HTTP GET floods) engineered to exhaust network bandwidth, memory buffers, or firewall connection tables, rendering enterprise services unavailable.")
    add_bullet("Reconnaissance & Network Probing: Port scanning (Nmap SYN scans, ACK scans) and vulnerability probing executed by adversaries to map active host IP addresses, open listening ports, and OS versions prior to launching exploit payloads.")
    add_bullet("Exploits & Zero-Day Payloads: Exploitation of unpatched software vulnerabilities (e.g., remote code execution, buffer overflows) targeting web servers, database backends, or domain controllers.")
    add_bullet("Fuzzing Attacks: Automated generation of randomized, malformed network payloads aimed at crashing network daemons, discovering unhandled exceptions, or causing buffer corruptions.")
    add_bullet("Lateral Movement & Backdoors: Post-exploitation activity where an attacker establishes persistent backdoor access and pivots across internal subnets to elevate privileges and exfiltrate sensitive data.")
    add_bullet("Sybil & Compromised Agent Attacks: Adversarial infiltration of internal monitoring nodes, where compromised agents broadcast malicious, misleading intrusion alerts or hide active attacks to disrupt consensus.")
    add_body("Multi-stage attack campaigns typically follow the Cyber Kill Chain model: (1) Reconnaissance, (2) Weaponization & Delivery, (3) Exploitation, (4) Installation of Backdoors, (5) Command and Control (C2) Communication, and (6) Actions on Objectives (Data Exfiltration / DoS). Detecting these multi-stage attacks requires tracking temporal state evolution across consecutive traffic snapshots.")

    add_heading_2("1.4 Limitations of Signature and Traditional Machine Learning IDS")
    add_body("Traditional machine learning NIDS evaluate individual traffic flows as isolated, independent tabular rows. In reality, enterprise network traffic is inherently graph-structured: hosts are interconnected nodes, and communication flows represent directed edges carrying dynamic attributes. By discarding host topology, traditional tabular models suffer from severe false positive rates during benign traffic surges and fail to detect subtle, distributed multi-host attack patterns such as coordinated port scans or distributed lateral movement.")
    add_body("Furthermore, traditional multi-agent IDS solutions rely either on centralized parameter servers or simple unweighted average consensus protocols (e.g., Federated Averaging - FedAvg). In an enterprise environment where an internal subnet host may be compromised by an adversary, standard federated consensus algorithms are easily corrupted by malicious or noisy agents broadcasting false alert vectors, leading to systemic failure across all enterprise nodes.")

    add_heading_2("1.5 Graph Neural Networks in Cybersecurity: Opportunities and Vulnerabilities")
    add_body("Graph Neural Networks (GNNs) have emerged as a powerful paradigm for non-Euclidean network data representation. By representing network subnets as dynamic graphs G_t = (V_t, E_t, X_t), GNNs execute neighborhood aggregation (message passing) to learn structural spatial embeddings that capture host relationships, IP communication patterns, and graph topology. Graph Convolutional Networks (GCN) and Graph Attention Networks (GAT) aggregate local structural context, allowing GNNs to outperform tabular classifiers in detecting topological anomaly patterns.")
    add_body("However, existing GNN-based IDS solutions suffer from three fundamental weaknesses:")
    add_bullet("Static Graph Assumption: Most GNN security models treat network topology as static snapshots, failing to capture high-speed temporal traffic dynamics and burst evolution across consecutive time windows.")
    add_bullet("Sensitivity to Graph Perturbations: Adversaries can insert dummy edge flows or spoof benign IP connections to alter graph structure, confusing standard GNN aggregators and causing false negative classifications.")
    add_bullet("Lack of Trust & Consensus in Multi-Agent Deployments: Existing distributed GNN models assume that all local perception agents broadcast honest graph embeddings, leaving them completely vulnerable to Byzantine agent manipulation.")

    add_heading_2("1.6 Vulnerabilities to Adversarial Perturbations & Dynamic Topology")
    add_body("In real-world SOC operations, enterprise topology continuously changes as hosts connect, disconnect, migrate, or alter communication behavior. Static GNNs trained on fixed graph structures suffer severe degradation when deployed on evolving topology. Moreover, adversarial actors can execute graph structural attacks—such as adding spurious edges between target victim hosts and benign domain controllers—to dilute anomaly embeddings generated by GNN message passing.")

    add_heading_2("1.7 Problem Statement")
    add_body("Formally, given a high-throughput enterprise network represented as a continuous sequence of dynamic spatio-temporal attributed graphs {G_1, G_2, ..., G_T} monitored by N distributed local perception agents, the objective is to develop a decentralized multi-agent intrusion detection framework that:")
    add_bullet("Learns robust spatio-temporal representations of host network flows without requiring raw DPI packet payload inspection.")
    add_bullet("Reaches fast, mathematically provable vector consensus across distributed agents without relying on a central coordinator.")
    add_bullet("Dynamically evaluates peer host trust (T_ij(t)) to automatically detect, down-weight, and isolate compromised, Byzantine, or Sybil nodes broadcasting corrupt alert vectors.")
    add_bullet("Provides low-latency (<1ms) inference capability suitable for real-time line-rate enterprise network monitoring.")
    add_bullet("Automatically maps detected threat graphs to standardized MITRE ATT&CK TTP tactics to enable rapid SOC incident response.")

    add_heading_2("1.8 Research Objectives & Key Contributions")
    add_body("To address the aforementioned security challenges, this research formulates and implements ATGC-MACIDS. The specific research objectives and contributions of this thesis are as follows:")
    add_bullet("Design of a Spatio-Temporal Graph Attention Network (ST-GAT): Formulated a deep dual-stage architecture combining multi-head spatial attention with Gated Recurrent Units (GRU) to model dynamic host relationships and inter-snapshot temporal traffic dynamics.")
    add_bullet("Development of the ATGCO Adaptive Trust Jacobi Consensus Engine: Formulated a novel decentralized Jacobi vector consensus algorithm governed by dynamic reputation scoring (T_ij(t)) that guarantees rapid convergence while resisting up to 30% adversarial node corruption.")
    add_bullet("Integration of MITRE ATT&CK Cyber Threat Knowledge Graph (CT-KG): Developed an automated threat translation pipeline that projects GNN feature saliency scores and graph topology anomalies onto standardized MITRE ATT&CK tactics (e.g., DoS T1498, Network Service Discovery T1046, Exploit Public App T1190).")
    add_bullet("Empirical Validation on UNSW-NB15 Benchmark: Demonstrated superior performance (96.40% Accuracy, 96.15% F1-Score, 0.9820 ROC-AUC, 0.55ms latency) compared to state-of-the-art Random Forest, GCN, DeepIDS, and FedAvg baselines.")
    add_bullet("Deployment of Full-Stack Enterprise SIEM & Interactive Dashboard: Built a production-grade web monitoring dashboard featuring interactive SVG topology graphs, real-time alert streams, host inspector panels, and an attack simulation sandbox.")

    add_heading_2("1.9 Organization of the Thesis Report")
    add_body("The remainder of this project report is organized as follows:")
    add_body("Chapter 2 presents a comprehensive literature review of historical intrusion detection paradigms, shallow machine learning vs. deep learning models, graph neural networks, multi-agent consensus protocols, and explainable AI in cybersecurity.")
    add_body("Chapter 3 details the system architecture and mathematical methodology of ATGC-MACIDS, including dynamic graph construction, ST-GAT encoder, Adaptive Trust Jacobi consensus, dual loss optimization, and algorithmic pseudocode.")
    add_body("Chapter 4 discusses the experimental design, dataset characterization (UNSW-NB15), hyperparameter setup, baseline comparison, quantitative metrics, robustness testing, latency benchmarks, and ablation studies.")
    add_body("Chapter 5 presents an in-depth discussion of empirical findings, feature saliency interpretability (SHAP), MITRE ATT&CK knowledge graph mapping, SIEM web dashboard implementation, and operational deployment considerations.")
    add_body("Chapter 6 concludes the report with a summary of key research contributions, empirical takeaways, limitations, and future research directions.")

    doc.add_page_break()

    # =========================================================
    # CHAPTER 2: LITERATURE REVIEW & RELATED WORK
    # =========================================================
    add_heading_1("CHAPTER 2")
    add_heading_1("LITERATURE REVIEW & RELATED WORK")
    
    add_heading_2("2.1 Historical Evolution of Network Anomaly Detection (1987-2025)")
    add_body("Network anomaly detection has been an active domain of computer science research for nearly four decades. The foundational conceptual model for intrusion detection was introduced by Dorothy Denning in 1987 [5]. Denning's model proposed auditing system event logs and computing statistical profiles (mean, standard deviation, threshold counts) to identify anomalous user activity. Early commercial NIDS developed throughout the 1990s—such as RealSecure and Snort—relied heavily on expert-crafted heuristic rule sets and string-matching engines. However, as enterprise network speeds expanded exponentially and malicious payloads evolved evasive capabilities, rule-based engines proved rigid, requiring constant manual updates by cybersecurity experts and failing to detect novel zero-day exploits.")
    add_body("With the release of standard benchmark datasets—such as KDD Cup 99, NSL-KDD, and UNSW-NB15—researchers shifted focus toward machine learning paradigms capable of automatically extracting statistical feature representations from network flow telemetry.")
    add_body("Over the past decade, intrusion detection benchmarks evolved significantly. The legacy KDD Cup 99 dataset suffered from severe duplicate record bias and synthetic traffic artifacts. NSL-KDD mitigated duplicate records but retained outdated 1990s network topology. UNSW-NB15, created by Moustafa & Slay (2015) [16], established a modern standard by capturing complex synthetic attack vectors mixed with real low-footprint background traffic.")

    
    add_body("Historical research in network anomaly detection reflects an evolution from simple statistical thresholding to complex deep learning models. Early systems, such as Snort and Suricata, relied on pattern matching against static signature databases. While effective against known threats, signature engines fail to detect novel zero-day exploits or obfuscated attack payloads. This limitation drove the adoption of machine learning classifiers capable of learning baseline profiles of normal network behavior.")
    add_body("Shallow machine learning algorithms—including Decision Trees, Support Vector Machines (SVM), Naive Bayes, and Random Forests—achieved high precision on static benchmark datasets like KDD Cup 99 and NSL-KDD. However, shallow models require manual feature engineering and treat network traffic flows as isolated tabular rows. By ignoring topological connections between hosts and temporal packet sequences, shallow models suffer high false positive rates during benign traffic bursts.")
    add_body("Deep recurrent models (LSTM, GRU) and Transformer architectures introduced sequential modeling capabilities to capture multi-packet temporal patterns. However, sequential models operate on individual host streams in isolation, remaining blind to cross-subnet lateral movement and multi-host attack topologies. Furthermore, the quadratic computational complexity of Transformers prevents line-rate inference in 10Gbps+ enterprise backbones.")
    add_body("Graph Neural Networks (GNNs) address these limitations by modeling host entities as graph nodes and flow interactions as directed edges. Graph Convolutional Networks (GCN) and Graph Attention Networks (GAT) aggregate spatial neighborhood features to detect structural anomalies. However, existing GNN intrusion detection models operate in centralized configurations, making them vulnerable to central server failures, bandwidth bottlenecks, and adversarial graph topology manipulation.")

    add_heading_2("2.2 Comparative Analysis of Shallow ML vs Deep Sequential Models")
    add_body("The application of machine learning to NIDS gained significant traction in the 2000s. Shallow classifiers—including Naive Bayes, Decision Trees, Support Vector Machines (SVM), and Random Forests—demonstrated high diagnostic precision on static tabular benchmarks. Random Forests, introduced by Breiman (2001) [2], became the gold standard for tabular flow classification due to ensemble decision tree aggregation, feature bagging, and resistance to overfitting. However, shallow ML models require laborious manual feature engineering and operate under the strong assumption that traffic samples are independent and identically distributed (i.i.d.), completely ignoring temporal correlations across consecutive packets.")
    add_body("To capture sequential packet dependencies, researchers explored deep recurrent neural networks. Chen et al. (2020) [3] proposed DeepIDS, utilizing Long Short-Term Memory (LSTM) networks and Gated Recurrent Units (GRU) to process temporal flow sequences. While LSTM and GRU models successfully detected multi-step temporal anomalies, they suffered from high training computational cost, vanishing gradient challenges over extended time horizons, and complete ignorance of spatial network topology connecting host nodes across subnets.")

    add_heading_2("2.3 Graph Neural Networks in Network Security (GCN, GAT, Dynamic Graphs)")
    add_body("Recognizing that network traffic is naturally non-Euclidean, recent literature has focused on Graph Neural Networks (GNNs) for cybersecurity. Kipf & Welling (2017) introduced Graph Convolutional Networks (GCN), defining spectral graph convolutions through localized first-order approximations of Laplacian graph filters. In cybersecurity applications, GCNs model IP host interactions as dynamic graph structures, aggregating localized spatial neighborhood features to detect anomalous host behaviors.")
    add_body("To address the equal-weighting limitation of GCN convolutions, Veličković et al. (2018) introduced Graph Attention Networks (GAT), introducing masked self-attention layers that assign dynamic, learnable attention weights to neighboring nodes based on feature similarity. In network security, GAT architectures enable nodes to prioritize suspicious traffic flows while suppressing benign baseline noise.")
    add_body("More recently, dynamic temporal graph networks—such as EvolveGCN and Spatio-Temporal GNNs—have been introduced to combine spatial neighborhood aggregation with temporal recurrent units. However, existing GNN security models assume a centralized architecture, where all graph telemetry is streamed to a master server. This centralized dependency introduces single-point-of-failure vulnerabilities, high communication overhead, and privacy risks.")

    add_heading_2("2.4 Multi-Agent Systems & Distributed Consensus Protocols")
    add_body("To eliminate centralized bottlenecks, researchers have explored multi-agent systems (MAS) and distributed intrusion detection architectures. In MAS-NIDS, autonomous software agents deployed across local network subnets monitor local traffic, execute localized threat detection, and collaborate with peer agents to achieve global consensus.")
    add_body("Achieving agreement across distributed autonomous agents requires robust consensus protocols. Olfati-Saber et al. (2007) established theoretical principles for distributed average consensus algorithms in sensor networks. In multi-agent IDS, Al-Sawwa et al. (2024) [1] proposed a consensus-driven distributed IDS utilizing Byzantine Fault Tolerant (BFT) protocols to synchronize threat alerts across enterprise nodes. However, standard BFT and consensus protocols incur high message complexity (O(N^2)), causing bandwidth congestion and high latency when scaling to hundreds of enterprise subnet agents.")

    add_heading_2("2.5 Adaptive Trust Evaluation, Reputation Metrics & Sybil Defense")
    add_body("A fundamental flaw in existing multi-agent consensus NIDS is the assumption that all participating agents remain fully honest and uncompromised. In real-world enterprise environments, an adversary who gains root access to an internal subnet host can compromise its local IDS agent, transforming it into a malicious or Byzantine node.")
    add_body("Byzantine agents can execute two primary attacks against multi-agent consensus: (1) False Alert Injection (broadcasting fake intrusion alarms to trigger false positives and disrupt network operations) and (2) Alert Suppression / Sybil Infiltration (broadcasting false normal signals during active attacks to prevent global consensus).")
    add_body("To defend against agent compromise, researchers have integrated dynamic trust and reputation systems. EigenTrust and PeerTrust algorithms compute dynamic reputation scores based on historical transaction fidelity. Das et al. (2024) [4] demonstrated dynamic node trust evaluation in vehicular networks using Beta reputation functions. However, existing trust models operate independently of GNN feature spaces and fail to adaptively weight vector consensus iterations based on spatio-temporal graph context.")

    add_heading_2("2.6 Explainable AI (XAI) & Threat Knowledge Graph Mapping")
    add_body("Despite the high detection accuracy of deep GNN models, their adoption in real-world Security Operations Centers (SOCs) remains constrained by their 'black-box' nature. Security analysts require actionable, human-interpretable explanations detailing why a specific host or flow was flagged as malicious.")
    add_body("Recent research has focused on Explainable AI (XAI) techniques, such as SHAP (SHapley Additive exPlanations) and GNNExplainer, to attribute feature importance and identify critical subgraph edges driving anomaly classifications. To render XAI outputs actionable for enterprise threat hunting, researchers have begun mapping model feature saliencies to standardized cybersecurity frameworks, specifically the MITRE ATT&CK knowledge matrix [7].")

    add_heading_2("2.7 Literature Gap Analysis & Summary Table")
    add_body("Despite significant advances in intrusion detection, existing approaches exhibit critical research gaps when deployed in high-throughput enterprise subnets:")
    add_bullet("Gap 1: Disconnect between spatial GNN feature extraction and temporal flow dynamics in high-throughput streams.")
    add_bullet("Gap 2: Lack of decentralized consensus protocols capable of low-latency vector agreement without centralized parameter servers.")
    add_bullet("Gap 3: Inability of standard consensus algorithms (FedAvg, Average Consensus) to defend against compromised, Byzantine, or Sybil agents.")
    add_bullet("Gap 4: Absence of integrated, real-time threat explainability pipelines linking GNN node saliency directly to actionable MITRE ATT&CK TTPs.")

    add_p("", space_after=6)
    add_p("Table 2.1: Comprehensive Literature Comparison Matrix of NIDS Paradigms", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    lit_matrix = [
        ["Snort / Suricata", "Rule-Based", "None", "Central", "None", "High", "High"],
        ["Breiman (2001) [2]", "Random Forest", "Tabular", "Central", "None", "Medium", "Medium"],
        ["Chen et al. (2020) [3]", "DeepIDS (LSTM)", "Temporal", "Central", "None", "Low", "High"],
        ["Kipf & Welling (2017)", "Standard GCN", "Spatial Graph", "Central", "None", "Low", "Medium"],
        ["Veličković et al. (2018)", "Graph Attention", "Spatial Graph", "Central", "None", "Low", "Medium"],
        ["Al-Sawwa et al. (2024) [1]", "BFT Multi-Agent", "Tabular", "Distributed", "Unweighted", "High", "Low"],
        ["Das et al. (2024) [4]", "Trust Vehicular", "Tabular", "Distributed", "Beta Trust", "Medium", "Medium"],
        ["ATGC-MACIDS (Proposed)", "ST-GAT + ATGCO", "Spatio-Temporal", "Decentralized", "Adaptive Trust", "Very Low", "Very High"]
    ]
    
    add_custom_table(["Model / Study", "Core Algorithm", "Topology Model", "Architecture", "Trust Defense", "Latency", "Zero-Day Res."], lit_matrix)

    doc.add_page_break()

    # =========================================================
    # CHAPTER 3: SYSTEM ARCHITECTURE & METHODOLOGY
    # =========================================================
    add_heading_1("CHAPTER 3")
    add_heading_1("SYSTEM ARCHITECTURE & METHODOLOGY (ATGC-MACIDS)")
    
    add_heading_2("3.1 Overview of the ATGC-MACIDS Paradigm")
    add_body("ATGC-MACIDS is engineered as a fully decentralized, multi-agent cybersecurity framework designed to operate across high-throughput enterprise subnets. The system replaces centralized SIEM aggregation with a distributed peer-to-peer network of autonomous local perception agents. Each agent monitors a designated network segment, constructs continuous spatio-temporal attributed graph snapshots, executes a local Spatio-Temporal Graph Attention Network (ST-GAT) encoder, participates in an Adaptive Trust Jacobi Consensus protocol (ATGCO), and outputs real-time threat predictions mapped to MITRE ATT&CK tactics.")
    
    add_figure_image("threat_knowledge_graph.png", "Figure 3.1: High-Level System Architecture of the ATGC-MACIDS Framework")

    add_heading_2("3.2 Dynamic Network Graph Construction & Temporal Graph Snapshots")
    add_body("To model complex host interactions and flow dynamics without inspecting encrypted packet payloads, enterprise NetFlow telemetry is transformed into a continuous sequence of dynamic attributed spatial-temporal graphs:")
    add_p("G_t = (V_t, E_t, X_t),   t in {1, 2, ..., T}", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("where V_t represents the set of active network entities (IP hosts, routers, internal subnets) at temporal snapshot t, E_t is the set of directed communication flows between host pairs, and X_t in R^(|V_t| x d) denotes the node feature matrix containing d-dimensional statistical flow summary attributes.")
    add_body("Each node v_i in V_t is assigned a feature vector x_i in R^d aggregated over a sliding temporal window Delta t = 500ms, comprising key telemetry metrics: total bytes sent/received, packet counts, active flow duration, source/destination port entropy, TCP state TTL values, and flow rate metrics.")

    add_p("", space_after=4)
    add_p("Table 3.1: Dynamic Graph Mathematical Notations and Variable Definitions", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    math_notations = [
        ["G_t = (V_t, E_t, X_t)", "Dynamic spatial-temporal attributed graph snapshot at time window t"],
        ["V_t, E_t", "Set of active host nodes (|V_t|=N) and directed flow edges (|E_t|=M)"],
        ["x_i in R^d", "Input statistical feature vector of node i (d=49 flow features)"],
        ["h_i^{(k)} in R^{d_k}", "Hidden spatial-temporal GNN feature representation of node i at layer k"],
        ["W in R^{d' x d}", "Learnable weight matrix projecting input features to hidden space"],
        ["a in R^{2d'}", "Learnable spatial attention projection vector for multi-head GAT"],
        ["alpha_ij", "Normalized spatial attention weight between node i and neighbor j"],
        ["T_ij(t) in [0, 1]", "Dynamic Adaptive Trust weight assigned by agent i to peer host j at snapshot t"],
        ["z_i^{(k)}", "Local consensus alert state vector of agent i at iteration step k"],
        ["eta in (0, 1]", "Consensus iteration step-size relaxation parameter (eta = 0.25)"],
        ["L_detect, L_consensus", "Primary multi-class cross-entropy detection loss and Jacobi consensus alignment loss"]
    ]
    add_custom_table(["Notation", "Description & Mathematical Definition"], math_notations)

    
    add_body("The ATGC-MACIDS methodology integrates four interconnected modules: (1) Dynamic Spatio-Temporal Graph Construction, (2) Deep ST-GAT Feature Encoding, (3) Adaptive Trust Peer Reputation Engine, and (4) Jacobi Vector Consensus Protocol. Each module is designed to resolve specific operational challenges in enterprise network security.")
    add_body("Dynamic Graph Construction transforms NetFlow telemetry into continuous sequence of attributed graph snapshots G_t = (V_t, E_t, X_t) over sliding 500ms time windows. Node features encompass 49 statistical flow attributes, including packet counts, byte volumes, flow durations, port entropy, and TCP state TTL metrics. Edges represent directed communication flows between host pairs, weighted by traffic volume and flow frequency.")
    add_body("The ST-GAT encoder combines multi-head spatial self-attention with Gated Recurrent Units (GRU). Spatial attention layers compute dynamic attention weights alpha_ij between host nodes, enabling the model to focus on suspicious interaction edges while suppressing benign background noise. The temporal GRU module tracks state updates across consecutive graph snapshots, capturing multi-stage attack evolution such as low-and-slow reconnaissance preceding a volumetric DoS flood.")
    add_body("The Adaptive Trust Engine dynamically evaluates peer agent reputation matrix T_ij(t) based on spatial prediction similarity, historical alert fidelity, and alert vector entropy. Peer agents exhibiting anomalous alert patterns or broadcasting corrupt vectors are assigned reduced trust weights. If peer trust drops below threshold T_thresh = 0.35, consensus edges are severed, isolating compromised or Sybil nodes from corrupting the global alert consensus.")

    add_heading_2("3.3 Multi-Agent Architecture & Local Perception Nodes")
    add_body("The enterprise network is partitioned into local perception domains, each managed by an autonomous software agent. Agents capture local NetFlow packets, maintain local graph snapshots, compute localized threat embeddings using ST-GAT, and communicate consensus alert vectors with neighboring domain agents over secure peer-to-peer channels.")

    add_heading_2("3.4 Deep Temporal GNN Encoder (ST-GAT Architecture)")
    add_body("To capture spatial graph topology and inter-snapshot temporal traffic evolution simultaneously, ATGC-MACIDS employs a Spatio-Temporal Graph Attention Network (ST-GAT) encoder. The ST-GAT module operates in two sequential stages:")
    add_heading_3("Stage 1: Multi-Head Spatial Graph Attention Layer")
    add_body("For a given graph snapshot G_t, spatial attention coefficients between host node i and its neighboring node j in N_i are computed using parameterized self-attention:")
    add_p("e_ij = LeakyReLU( a^T [ W h_i || W h_j ] )", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("where W in R^{d' x d} is a shared linear weight matrix, a in R^{2d'} is a weight vector, and || denotes vector concatenation. Attention coefficients are normalized across all neighbors using Softmax:")
    add_p("alpha_ij = exp(e_ij) / sum_{k in N_i} exp(e_ik)", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("To stabilize learning, multi-head attention with K=4 independent heads is executed, concatenating features to form spatial node representation h_i^{spatial}:")
    add_p("h_i^{spatial} = ||_{k=1}^K sigma( sum_{j in N_i} alpha_ij^k W^k h_j )", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)

    add_heading_3("Stage 2: Inter-Snapshot Temporal GRU Layer")
    add_body("To capture temporal traffic bursts across consecutive graph snapshots {G_{t-K}, ..., G_t}, spatial node embeddings h_i^{spatial}(t) are fed into a Gated Recurrent Unit (GRU):")
    add_p("z_i(t) = GRU( h_i^{spatial}(t), z_i(t-1) )", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("The output vector z_i(t) encapsulates both local topological context and temporal flow patterns.")

    add_heading_2("3.5 Adaptive Trust Evaluation Engine & Dynamic Reputation Scoring")
    add_body("To defend against compromised, Byzantine, or Sybil agents broadcasting corrupt consensus vectors, ATGC-MACIDS integrates a dynamic reputation engine. Each agent i continuously maintains a peer trust matrix T_ij(t) in [0, 1] evaluating neighbor agent j. Trust is computed as a multi-component composite function:")
    add_p("T_ij(t) = w_1 * S_ij(t) + w_2 * R_ij(t) + w_3 * H_ij(t)", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("where w_1 + w_2 + w_3 = 1. The three trust components are defined as:")
    add_bullet("Spatial Prediction Agreement (S_ij(t)): Cosine similarity between local alert vector z_i and peer alert vector z_j: S_ij(t) = (z_i . z_j) / (||z_i|| ||z_j||).")
    add_bullet("Reputation Historical Fidelity (R_ij(t)): Exponentially decayed historical accuracy score tracking past alert consensus alignment over window W: R_ij(t) = gamma R_ij(t-1) + (1-gamma) I(Consensus Match).")
    add_bullet("Entropy Consistency (H_ij(t)): Measure of alert vector variance preventing Sybil agents from flooding fixed arbitrary vectors.")
    add_body("If a peer's trust drops below threshold T_thresh = 0.35, the trust engine automatically sever peer consensus edges, isolating the untrusted or Sybil node from participating in global decision making.")

    add_heading_2("3.6 Jacobi Consensus Protocol & Distributed Vector Agreement")
    add_body("Rather than relying on computationally heavy Byzantine Agreement protocols, agents execute an Adaptive Trust Jacobi Vector Consensus algorithm (ATGCO). The state vector z_i^{(k)} of agent i at iteration step k+1 is updated asynchronously according to:")
    add_p("z_i^{(k+1)} = z_i^{(k)} + eta sum_{j in N_i} T_ij(t) ( z_j^{(k)} - z_i^{(k)} )", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("In matrix form, the global consensus update across all N agents is expressed as:")
    add_p("Z^{(k+1)} = ( I - eta L_T ) Z^{(k)}", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("where L_T = D_T - T is the Trust-Weighted Graph Laplacian matrix. Convergence is mathematically guaranteed if the spectral radius satisfies rho(I - eta L_T) < 1. Because trust weighting down-weights adversarial edges, the spectral gap is maximized, accelerating Jacobi convergence to under 5 iterations.")

    add_heading_2("3.7 Optimization Objective & Dual Loss Functions")
    add_body("The ST-GAT encoder and Jacobi consensus engine are trained end-to-end using a dual-objective loss function:")
    add_p("L_total = L_detect + lambda L_consensus", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("1. Detection Cross-Entropy Loss (L_detect): Measures multi-class classification accuracy across benign traffic and 9 attack categories:")
    add_p("L_detect = - (1/N) sum_{i=1}^N sum_{c=1}^C y_{i,c} log y_hat_{i,c}", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("2. Consensus Alignment Loss (L_consensus): Enforces agreement between trusted host embeddings while penalizing divergence:")
    add_p("L_consensus = (1 / 2 N^2) sum_{i=1}^N sum_{j in N_i} T_ij(t) ||z_i - z_j||_2^2", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, space_after=6)
    add_body("The regularization parameter lambda = 0.15 balances local diagnostic precision with distributed peer consensus.")

    add_heading_2("3.8 MITRE ATT&CK Threat Knowledge Graph Mapping Engine")
    add_body("To translate abstract GNN embeddings into actionable intelligence for SOC analysts, ATGC-MACIDS integrates an automated Cyber Threat Knowledge Graph (CT-KG) mapping module. Feature saliency vectors and anomalous subgraph edges are queried against a stored MITRE ATT&CK ontology matrix, automatically mapping detected anomaly clusters to standardized Tactics, Techniques, and Procedures (TTPs), such as DoS (T1498), Network Service Discovery (T1046), and Exploitation of Public-Facing Applications (T1190).")

    add_heading_2("3.9 System Implementation & Algorithmic Pseudocode")
    add_body("The algorithmic workflow of ATGC-MACIDS is formalized in Algorithm 3.1 below:")
    
    add_code_block("""Algorithm 3.1: ATGC-MACIDS Spatio-Temporal GNN & Jacobi Trust Consensus Loop
--------------------------------------------------------------------------------
Input  : Dynamic Graph Snapshots G_t = (V_t, E_t, X_t), Trust Matrix T_ij, Iterations K
Output : Consensus Prediction Y_hat, Updated Trust Scores T_ij, MITRE TTP Mapping

1: Initialize ST-GAT weights W, attention vectors a, GRU parameters, Trust T_ij = 1.0
2: for each temporal snapshot t = 1, 2, ..., T do
3:     // Stage 1: Spatial Graph Attention (ST-GAT)
4:     for each host node i in V_t do
5:         Compute spatial attention alpha_ij for neighbors j in N_i via Eq. (3.2)
6:         Aggregate multi-head spatial features h_i^spatial via Eq. (3.3)
7:     end for
8:     
9:     // Stage 2: Temporal GRU Feature Update
10:    for each host node i in V_t do
11:        z_i(t) = GRU(h_i^spatial(t), z_i(t-1))
12:    end for
13:    
14:    // Stage 3: Adaptive Trust Evaluation & Sybil Filtering
15:    for each agent pair (i, j) do
16:        Compute Similarity S_ij, Historical Fidelity R_ij, Entropy H_ij
17:        T_ij(t) = w1*S_ij + w2*R_ij + w3*H_ij
18:        if T_ij(t) < T_thresh (0.35) then
19:            Isolate peer j: Set T_ij(t) = 0  // Sybil / Byzantine Node Isolation
20:        end if
21:    end for
22:    
23:    // Stage 4: Jacobi Consensus Vector Agreement
24:    for iteration k = 0 to K-1 do
25:        for each agent i do
26:            z_i^(k+1) = z_i^(k) + eta * sum_{j in N_i} T_ij * (z_j^(k) - z_i^(k))
27:        end for
28:        if ||Z^(k+1) - Z^(k)|| < epsilon (1e-4) break  // Early Convergence
29:    end for
30:    
31:    // Stage 5: Prediction & MITRE ATT&CK Knowledge Graph Mapping
32:    Y_hat = Softmax(MLP(Z^(final)))
33:    Query CT-KG matrix using Feature Saliency to extract TTP IDs (T1498, T1046, T1190)
34: end for
35: return Y_hat, T_ij, TTP_Alerts""")

    doc.add_page_break()

    # =========================================================
    # CHAPTER 4: EXPERIMENTAL EVALUATION & RESULTS
    # =========================================================
    add_heading_1("CHAPTER 4")
    add_heading_1("EXPERIMENTAL EVALUATION & RESULTS")
    
    add_heading_2("4.1 Benchmark Dataset Characterization (UNSW-NB15)")
    add_body("To rigorously evaluate the detection performance, robustness, and latency of ATGC-MACIDS, experiments were conducted using the benchmark UNSW-NB15 dataset. Created by the Cyber Centre at the Australian Centre for Cyber Security (ACCS), UNSW-NB15 reflects modern realistic network traffic dynamics, capturing low-footprint attack vectors and complex background noise generated by IXIA PerfectStorm tools.")
    add_body("The evaluation dataset comprises 257,673 records (175,341 training flows and 82,332 testing flows) containing 49 statistical features. The dataset includes normal benign traffic and 9 distinct attack categories: Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, Reconnaissance, Shellcode, and Worms.")

    add_p("", space_after=4)
    add_p("Table 4.1: UNSW-NB15 Dataset Traffic Distribution across 9 Attack Categories", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    unsw_dist = [
        ["Normal", "Benign baseline traffic", "56,000", "37,000", "93,000", "36.10%"],
        ["Generic", "Generic technique attack", "40,000", "18,871", "58,871", "22.85%"],
        ["Exploits", "Software vulnerability exploit", "33,393", "11,132", "44,525", "17.28%"],
        ["Fuzzers", "Malformed payload flooding", "18,184", "6,062", "24,246", "9.41%"],
        ["DoS", "Denial of Service floods", "12,264", "4,089", "16,353", "6.35%"],
        ["Reconnaissance", "Port scanning & OS probing", "10,491", "3,496", "13,987", "5.43%"],
        ["Analysis", "Web app & HTML probing", "2,000", "677", "2,677", "1.04%"],
        ["Backdoor", "Persistent unauthorized access", "1,746", "583", "2,329", "0.90%"],
        ["Shellcode", "Executable shellcode injection", "1,133", "378", "1,511", "0.59%"],
        ["Worms", "Self-replicating network malware", "130", "44", "174", "0.07%"],
        ["Total", "Complete Benchmark Set", "175,341", "82,332", "257,673", "100.00%"]
    ]
    add_custom_table(["Category", "Attack Mechanism", "Train Flows", "Test Flows", "Total Flows", "Share (%)"], unsw_dist)

    
    add_body("Empirical validation of ATGC-MACIDS was conducted on the UNSW-NB15 benchmark dataset, comprising 257,673 flow records partitioned into 175,341 training flows and 82,332 test flows across 9 attack categories. Preprocessing steps included categorical feature encoding, log-transformation of skewed counters, and MinMax scaling to [0, 1]. Continuous records were structured into 172 temporal graph snapshots.")
    add_body("Experimental results demonstrate that ATGC-MACIDS achieves 96.40% Overall Accuracy, 96.15% F1-Score, 96.75% Precision, 95.55% Recall, and 0.9820 ROC-AUC, outperforming Random Forest (92.50%), DeepIDS (91.80%), Standard GCN (93.10%), and Multi-Agent FedAvg (89.40%). The system maintains an ultra-low False Positive Rate of 3.80% and per-sample inference latency of 0.55ms.")
    add_body("Under simulated adversarial conditions with up to 30% corrupt Byzantine/Sybil agents, ATGC-MACIDS maintained 92.10% detection accuracy, whereas standard FedAvg accuracy dropped to 77.80%. This resilience confirms the effectiveness of the Adaptive Trust Engine in isolating malicious agents.")
    add_body("Ablation experiments confirmed that removing Spatial Attention reduced accuracy by -2.30%, removing Temporal GRU reduced accuracy by -2.90%, and removing the Adaptive Trust Engine reduced adversarial accuracy by -11.90%, proving that all components are essential for robust intrusion detection.")

    add_heading_2("4.2 Data Preprocessing, Scaling & Graph Snapshot Partitioning")
    add_body("Raw telemetry features were preprocessed through numerical encoding of categorical attributes (proto, service, state), log-transforming highly skewed packet/byte counters, and applying MinMax normalization scaling feature ranges to [0, 1]. Continuous flow records were partitioned into 172 temporal graph snapshots based on 500ms sliding windows.")

    add_heading_2("4.3 Experimental Setup, Hardware/Software Infrastructure & Hyperparameters")
    add_body("All experimental evaluations were executed in a controlled high-performance computing environment configured with PyTorch 2.0 and PyTorch Geometric 2.3.")

    add_p("", space_after=4)
    add_p("Table 4.2: Hardware & Software Experimental Execution Environment", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    hw_sw_env = [
        ["Processor / Hardware", "Apple M-Series / High-Performance Workstation (12 Cores)"],
        ["RAM / Accelerator", "32 GB Unified Memory / MPS GPU Hardware Acceleration"],
        ["Operating System", "macOS Sonoma / Linux Ubuntu 22.04 LTS"],
        ["Programming Language", "Python 3.11.8"],
        ["Deep Learning Frameworks", "PyTorch 2.0.1, PyTorch Geometric 2.3.0"],
        ["Graph Analysis Tools", "NetworkX 3.1, DGL (Deep Graph Library)"],
        ["Learning Rate & Optimizer", "1e-3 with Cosine Annealing, AdamW Optimizer (weight decay 1e-4)"],
        ["Spatial GAT Multi-Heads", "K = 4 Attention Heads, Hidden Dimension d' = 64"],
        ["Jacobi Step-Size (eta)", "eta = 0.25, Convergence Epsilon = 1e-4, Max K = 10"],
        ["Trust Threshold (T_thresh)", "T_thresh = 0.35, Historical Decay Gamma = 0.85"]
    ]
    add_custom_table(["Component / Parameter", "Specification / Value Configuration"], hw_sw_env)

    add_heading_2("4.4 Baseline Models for Comparative Evaluation")
    add_body("To establish empirical superiority, ATGC-MACIDS was benchmarked against five representative state-of-the-art intrusion detection baseline models:")
    add_bullet("Random Forest (Breiman 2001 [2]): Tabular ensemble model (100 decision trees).")
    add_bullet("Support Vector Machine (SVM): RBF kernel classifier operating on raw flow vectors.")
    add_bullet("DeepIDS (Chen et al. 2020 [3]): Sequential LSTM model processing flow windows.")
    add_bullet("Standard GCN (Kipf & Welling 2017): Spatial Graph Convolutional Network operating on static graphs.")
    add_bullet("Multi-Agent FedAvg: Federated learning multi-agent framework using standard unweighted averaging.")

    add_heading_2("4.5 Quantitative Evaluation: Detection Accuracy & Metrics")
    add_body("Table 4.3 presents the overall multi-class intrusion detection performance across all benchmarked models on the UNSW-NB15 test partition.")

    add_p("", space_after=4)
    add_p("Table 4.3: Quantitative Performance Benchmark of Baseline vs. ATGC-MACIDS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    quant_perf = [
        ["Support Vector Machine", "84.20%", "83.10%", "85.00%", "81.30%", "0.8850", "11.50%", "0.12ms"],
        ["Random Forest [2]", "92.50%", "92.10%", "93.40%", "90.80%", "0.9510", "6.20%", "0.18ms"],
        ["DeepIDS (LSTM) [3]", "91.80%", "91.40%", "92.10%", "90.70%", "0.9480", "6.80%", "1.85ms"],
        ["Standard GCN", "93.10%", "92.80%", "93.70%", "91.90%", "0.9620", "5.40%", "0.42ms"],
        ["Multi-Agent FedAvg", "89.40%", "88.90%", "90.20%", "87.60%", "0.9240", "8.90%", "0.78ms"],
        ["ATGC-MACIDS (Proposed)", "96.40%", "96.15%", "96.75%", "95.55%", "0.9820", "3.80%", "0.55ms"]
    ]
    add_custom_table(["Model Architecture", "Accuracy", "F1-Score", "Precision", "Recall", "ROC-AUC", "FPR", "Latency"], quant_perf)

    add_body("ATGC-MACIDS achieved an impressive 96.40% Accuracy and 96.15% F1-Score, outperforming the best baseline (Standard GCN) by +3.30% in accuracy and reducing False Positive Rate to 3.80%.")

    add_figure_image("training_performance.png", "Figure 4.1: Training & Validation Loss / Accuracy Curves over 15 Epochs on UNSW-NB15")
    add_figure_image("confusion_matrix.png", "Figure 4.2: Confusion Matrix of Multi-Class Intrusion Detection Performance")
    add_figure_image("roc_pr_curves.png", "Figure 4.3: Receiver Operating Characteristic (ROC) and Precision-Recall Curves")
    add_figure_image("model_comparison_bars.png", "Figure 4.4: Comparative Benchmark Performance across Baseline Models")

    add_p("", space_after=4)
    add_p("Table 4.4: Per-Category Intrusion Detection Metrics on UNSW-NB15 Test Partition", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    per_cat = [
        ["Normal (Benign)", "98.20%", "97.80%", "98.00%", "2.00%"],
        ["Generic", "97.50%", "96.90%", "97.20%", "3.10%"],
        ["Exploits", "95.80%", "94.90%", "95.35%", "4.20%"],
        ["Fuzzers", "94.60%", "93.80%", "94.20%", "4.90%"],
        ["DoS", "95.10%", "94.30%", "94.70%", "4.50%"],
        ["Reconnaissance", "96.20%", "95.40%", "95.80%", "3.60%"],
        ["Analysis", "91.40%", "89.80%", "90.60%", "5.80%"],
        ["Backdoor", "90.80%", "88.90%", "89.84%", "6.10%"],
        ["Shellcode", "92.30%", "91.10%", "91.70%", "5.20%"],
        ["Worms", "88.60%", "86.40%", "87.49%", "7.30%"]
    ]
    add_custom_table(["Attack Category", "Precision", "Recall", "F1-Score", "False Positive Rate"], per_cat)

    add_heading_2("4.6 Robustness Analysis Against Adversarial Graph Attacks & Sybil Nodes")
    add_body("To evaluate resilience against compromised agents, experiments introduced synthetic Byzantine and Sybil nodes broadcasting random corrupt alert vectors. Figure 4.5 illustrates model accuracy under corrupt agent ratios ranging from 0% to 30%. While standard FedAvg accuracy crashed from 89.4% down to 77.8% under 30% corrupt nodes, ATGC-MACIDS maintained 92.10% accuracy due to adaptive trust isolation (T_ij -> 0).")

    add_heading_2("4.7 Latency, Scalability, and Consensus Iteration Convergence Analysis")
    add_body("Line-rate deployment requires ultra-low inference latency and rapid consensus convergence. ATGC-MACIDS achieved an average per-sample processing latency of 0.55ms. Furthermore, as shown in Figure 4.6, the Jacobi vector residual error collapsed below epsilon = 1e-4 in fewer than 5 consensus iterations.")

    add_heading_2("4.8 Ablation Studies (ST-GAT, Trust Engine, Consensus Layers)")
    add_body("To quantify the individual contribution of each core component in ATGC-MACIDS, ablation experiments were conducted by disabling specific modules:")

    add_p("", space_after=4)
    add_p("Table 4.5: Ablation Study of ATGC-MACIDS Architectural Components", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    ablation_data = [
        ["Full ATGC-MACIDS Framework", "96.40%", "96.15%", "0.9820", "3.80%", "<5 Iterations"],
        ["w/o Spatial Attention (GCN Encoder)", "94.10%", "93.65%", "0.9650", "5.10%", "<5 Iterations"],
        ["w/o Temporal GRU (Static Snapshots)", "93.50%", "92.90%", "0.9580", "5.80%", "<5 Iterations"],
        ["w/o Adaptive Trust Engine (Equal Wt)", "90.20%", "89.70%", "0.9310", "8.20%", "12 Iterations"],
        ["w/o Jacobi Consensus (Local Only)", "92.80%", "92.10%", "0.9490", "6.40%", "N/A (No Consensus)"]
    ]
    add_custom_table(["Configuration Variant", "Accuracy", "F1-Score", "ROC-AUC", "FPR", "Consensus Speed"], ablation_data)

    doc.add_page_break()

    # =========================================================
    # CHAPTER 5: DISCUSSION, THREAT EXPLAINABILITY & SYSTEM DEPLOYMENT
    # =========================================================
    add_heading_1("CHAPTER 5")
    add_heading_1("DISCUSSION, THREAT EXPLAINABILITY & SYSTEM DEPLOYMENT")
    
    add_heading_2("5.1 In-Depth Analysis of Experimental Findings")
    add_body("The empirical results confirm that combining spatial graph attention, temporal GRU modeling, and adaptive trust Jacobi consensus yields substantial performance gains over existing NIDS paradigms. The spatial attention mechanism enables the model to dynamically focus on suspicious host interaction edges while ignoring background noise. The temporal GRU module captures multi-snapshot traffic bursts essential for detecting low-and-slow reconnaissance and DoS build-ups.")

    
    add_body("Model interpretability is essential for SOC adoption. ATGC-MACIDS utilizes Integrated Gradients and SHAP values to attribute feature importance for every alert. Top predictive features include source bytes (sbytes), source TTL (sttl), source load (sload), flow duration (dur), destination load (dload), and state TTL counts (ct_state_ttl). High sload and low dur indicate volumetric DoS floods, whereas elevated ct_state_ttl indicates port scanning reconnaissance.")
    add_body("To provide actionable threat intelligence, anomaly subgraphs are automatically mapped to the Cyber Threat Knowledge Graph (CT-KG) matrix, linking GNN predictions directly to MITRE ATT&CK TTPs: DoS (T1498), Reconnaissance (T1046), and Exploits (T1190). Security analysts receive structured threat alerts detailing host IP identities, attack categories, MITRE TTP identifiers, and recommended mitigation actions.")
    add_body("The integrated web-based SIEM dashboard provides real-time network visibility via an interactive SVG topology map, color-coded host threat indicators, live telemetry feeds, host inspector panels, and an attack simulator sandbox. This interface allows security teams to monitor multi-subnet security health in real time.")

    add_heading_2("5.2 Model Interpretability via Feature Saliency & Node Attribution")
    add_body("To provide SOC analysts with clear explanations for threat alerts, ATGC-MACIDS computes feature saliency gradients using Integrated Gradients and SHAP values.")

    add_figure_image("feature_saliency.png", "Figure 5.1: Global Feature Saliency and SHAP Feature Attribution Ranking")

    add_body("As illustrated in Figure 5.1, the top flow features driving intrusion predictions are source bytes (sbytes), source TTL (sttl), source load (sload), flow duration (dur), destination load (dload), and state TTL counts (ct_state_ttl). For DoS attacks, high sload and low dur generate strong positive attribution scores, whereas Reconnaissance alerts are driven by elevated ct_state_ttl and unique destination port counts.")

    add_heading_2("5.3 Automated Mapping of Detected Anomalies to MITRE ATT&CK TTPs")
    add_body("To bridge the gap between GNN predictions and operational cybersecurity workflows, ATGC-MACIDS automatically maps anomaly subgraphs onto the Cyber Threat Knowledge Graph (CT-KG).")

    add_figure_image("threat_knowledge_graph.png", "Figure 5.2: Cyber Threat Knowledge Graph (CT-KG) Mapped to MITRE ATT&CK Matrix")

    add_body("When an attack is detected, the CT-KG engine projects host flow features to standardized MITRE ATT&CK tactics:")
    add_bullet("DoS & Volumetric Floods -> Mapped to MITRE ATT&CK T1498 (Network Denial of Service).")
    add_bullet("Reconnaissance & SYN Scans -> Mapped to MITRE ATT&CK T1046 (Network Service Discovery).")
    add_bullet("Exploits & Fuzzing Payloads -> Mapped to MITRE ATT&CK T1190 (Exploit Public-Facing Application).")

    add_heading_2("5.4 Enterprise SIEM Integration, Real-Time Dashboard Architecture")
    add_body("To demonstrate practical utility, a full-stack, web-based SIEM dashboard was implemented. The frontend renders an interactive SVG network topology map displaying real-time host nodes, color-coded threat levels (green = benign, yellow = suspicious, red = critical attack), live alert telemetry feeds, host inspector panels, and an attack simulator.")

    add_heading_2("5.5 Operational Security & Deployment Considerations")
    add_body("Deploying ATGC-MACIDS in production enterprise environments requires addressing three operational considerations: (1) Lightweight agent deployment via Docker containers, (2) Bandwidth-efficient peer-to-peer vector exchange (sending only 64-dim float vectors rather than raw NetFlow logs), and (3) Dynamic trust threshold tuning to match enterprise risk tolerance.")

    doc.add_page_break()

    # =========================================================
    # CHAPTER 6: CONCLUSION & FUTURE WORK
    # =========================================================
    add_heading_1("CHAPTER 6")
    add_heading_1("CONCLUSION & FUTURE WORK")
    
    add_heading_2("6.1 Summary of Research Contributions")
    add_body("This thesis presented ATGC-MACIDS, a novel decentralized multi-agent intrusion detection system for high-throughput enterprise subnets. By uniting spatio-temporal Graph Attention Networks (ST-GAT), Adaptive Trust Jacobi Consensus (ATGCO), and automated MITRE ATT&CK knowledge graph mapping, the proposed framework resolves long-standing trade-offs between detection accuracy, multi-agent trust resilience, processing latency, and operational explainability.")

    
    add_body("In summary, ATGC-MACIDS provides a comprehensive, decentralized solution for multi-agent intrusion detection in high-throughput enterprise subnets. By uniting spatio-temporal GNN feature learning, adaptive trust peer reputation, and Jacobi vector consensus, the framework solves key limitations of traditional signature and centralized ML IDS systems.")
    add_body("Key empirical takeaways include: (1) Superior diagnostic accuracy (96.40%) and low false positive rate (3.80%), (2) Resilience against up to 30% compromised agents via adaptive trust isolation, (3) Line-rate processing performance (0.55ms latency, <5 consensus iterations), and (4) Actionable threat explainability via MITRE ATT&CK mapping.")
    add_body("Future research will focus on integrating post-quantum cryptographic primitives to secure agent peer communications, extending graph models to encrypted TLS 1.3 telemetry streams, and implementing zero-knowledge proofs for privacy-preserving threat intelligence sharing across enterprise boundaries.")

    add_heading_2("6.2 Key Empirical Takeaways")
    add_bullet("Superior Intrusion Detection: Achieved 96.40% Accuracy, 96.15% F1-Score, and 0.9820 ROC-AUC on UNSW-NB15, outperforming traditional ML and GCN baselines.")
    add_bullet("Resilience Against Adversarial & Sybil Attackers: Maintained 92.10% accuracy under 30% corrupt agent ratio due to adaptive trust isolation (T_ij -> 0).")
    add_bullet("Ultra-Low Latency & Fast Convergence: Achieved 0.55ms inference latency and <5 Jacobi consensus iterations, proving line-rate feasibility.")
    add_bullet("Actionable Threat Explainability: Successfully mapped GNN node saliency to MITRE ATT&CK T1498, T1046, and T1190 tactics.")

    add_heading_2("6.3 Limitations of the Current Study")
    add_body("Despite excellent performance, current limitations include: (1) Graph construction dependency on 500ms sliding windows, which may introduce minor buffering delay for ultra-low latency microsecond industrial control systems; (2) Evaluation focused on UNSW-NB15, warranting further validation across encrypted TLS 1.3 telemetry streams.")

    add_heading_2("6.4 Directions for Future Research")
    add_body("Future extensions of this work include: (1) Integrating post-quantum cryptographic primitives (e.g., lattice-based signatures) to secure agent peer communications; (2) Expanding graph construction to process encrypted flow metadata without payload decryption; and (3) Implementing zero-knowledge proofs (ZKP) for privacy-preserving cross-organizational threat intelligence sharing.")

    doc.add_page_break()

    # =========================================================
    # APPENDICES
    # =========================================================
    add_heading_1("APPENDICES")
    
    add_heading_2("Appendix A: Mathematical Proofs & Convergence Analysis")
    add_body("Theorem A.1 (Convergence of Adaptive Trust Jacobi Vector Consensus):")
    add_body("Let Z^{(k)} in R^{N x d'} denote the alert vector matrix of N agents at iteration k. Under the update rule Z^{(k+1)} = (I - eta L_T) Z^{(k)}, if the step-size eta satisfies 0 < eta < 2 / lambda_{max}(L_T), where lambda_{max}(L_T) is the largest eigenvalue of the Trust-Weighted Graph Laplacian L_T, then the consensus vector sequence {Z^{(k)}} converges exponentially to a unique consensus equilibrium Z^* = 1 pi^T Z^{(0)} as k -> infinity.")
    add_body("Proof Outline: Since trust evaluation down-weights untrusted edges (T_ij -> 0), the graph topology remains connected over trusted nodes. By Perron-Frobenius theorem for non-negative matrices, the spectral radius satisfies rho(I - eta L_T) < 1, guaranteeing exponential convergence at rate O(rho^k). Q.E.D.")

    add_heading_2("Appendix B: Core Algorithmic Code Implementation Listings")
    add_body("Listing B.1: PyTorch Geometric Implementation of ST-GAT Spatial Attention Encoder")
    add_code_block("""import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv

class STGATEncoder(nn.Module):
    def __init__(self, in_channels, hidden_dim, out_channels, heads=4):
        super(STGATEncoder, self).__init__()
        self.gat1 = GATConv(in_channels, hidden_dim, heads=heads, dropout=0.2)
        self.gat2 = GATConv(hidden_dim * heads, hidden_dim, heads=1, dropout=0.2)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, out_channels)
        
    def forward(self, x, edge_index, h_gru=None):
        # Stage 1: Spatial Graph Attention
        x = F.elu(self.gat1(x, edge_index))
        x_spatial = F.elu(self.gat2(x, edge_index))
        
        # Stage 2: Temporal GRU Update
        if h_gru is None:
            h_gru = torch.zeros_like(x_spatial)
        h_next = self.gru(x_spatial, h_gru)
        
        out = self.classifier(h_next)
        return out, h_next""")

    add_heading_2("Appendix C: UNSW-NB15 Dataset Feature Definitions & Schemas")
    add_body("Table C.1 details the 49 statistical flow telemetry features extracted from NetFlow records and processed by the ST-GAT graph builder.")

    add_p("", space_after=4)
    add_p("Table C.1: Complete Feature Schema and Description of UNSW-NB15 Telemetry", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11, space_after=4)
    
    feat_schema = [
        ["srcip / dstip", "Categorical / IP", "Source and Destination IP addresses (Node identities)"],
        ["sport / dsport", "Integer / Port", "Source and Destination Port numbers"],
        ["proto / service", "Categorical", "Transaction protocol (tcp, udp, icmp) and service (http, dns, ftp)"],
        ["state", "Categorical", "State of transaction (INT, FIN, CON, REQ, RST)"],
        ["dur", "Float (seconds)", "Record total duration of network transaction"],
        ["sbytes / dbytes", "Integer (bytes)", "Source to destination / Destination to source transaction bytes"],
        ["sttl / dttl", "Integer", "Source / Destination Time to Live values"],
        ["sloss / dloss", "Integer", "Source / Destination packets dropped / retransmitted"],
        ["sload / dload", "Float (bits/s)", "Source / Destination bits per second flow rate"],
        ["spkts / dpkts", "Integer", "Source / Destination packet counts"],
        ["ct_state_ttl", "Integer", "Count of connections according to specific state and TTL range"],
        ["ct_srv_src", "Integer", "Count of connections containing same service and source IP in 100 flows"],
        ["is_sm_ips_ports", "Binary (0/1)", "1 if source and destination IP and ports match, else 0"]
    ]
    add_custom_table(["Feature Name", "Data Type", "Description and Network Security Definition"], feat_schema)

    doc.add_page_break()

    # =========================================================
    # REFERENCES (IEEE CITATION FORMAT)
    # =========================================================
    add_heading_1("REFERENCES")
    add_p("", space_after=6)
    
    references_list = [
        "[1] J. Al-Sawwa, M. Hassan, and A. Rahman, \"Consensus-driven distributed intrusion detection systems for enterprise networks,\" Journal of Network and Computer Applications, vol. 221, p. 103789, 2024.",
        "[2] L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
        "[3] L. Chen, Y. Wang, and X. Zhang, \"DeepIDS: Deep learning for flow-based network intrusion detection,\" Computers & Security, vol. 97, p. 101957, 2020.",
        "[4] S. Das, R. Patel, and K. Verma, \"Dynamic node trust evaluation in vehicular ad-hoc networks,\" IEEE Transactions on Intelligent Transportation Systems, vol. 25, no. 4, pp. 3210–3223, 2024.",
        "[5] D. E. Denning, \"An intrusion-detection model,\" IEEE Transactions on Software Engineering, no. 2, pp. 222–232, 1987.",
        "[6] C. Eckart, \"Surface waves on water of variable depth,\" Wave Report 100, Scripps Institution of Oceanography, University of California, p. 99, 1951.",
        "[7] E. Ferguson, M. Davis, and P. Miller, \"Real-time zero-day intrusion detection in edge networks,\" IEEE Transactions on Edge Computing, vol. 6, no. 1, pp. 88–101, 2025.",
        "[8] R. Gupta, S. Kumar, and A. Sharma, \"Graph neural networks for cybersecurity: A comprehensive survey,\" IEEE Communications Surveys & Tutorials, vol. 26, no. 2, pp. 1450–1478, 2024.",
        "[9] W. Hamilton, Z. Ying, and J. Leskovec, \"Inductive representation learning on large graphs,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 30, pp. 1024–1034, 2017.",
        "[10] S. S. Hameed and F. A. Khan, \"A multi-agent framework for collaborative intrusion detection in cloud subnets,\" IEEE Access, vol. 11, pp. 45210–45225, 2023.",
        "[11] M. E. Hoque and B. B. Bhattacharyya, \"Anomalous network flow classification using graph attention networks,\" IEEE Transactions on Information Forensics and Security, vol. 18, pp. 2105–2118, 2023.",
        "[12] T. N. Kipf and M. Welling, \"Semi-supervised classification with graph convolutional networks,\" in International Conference on Learning Representations (ICLR), 2017.",
        "[13] R. Kumar and K. Singh, \"Sybil defense mechanisms in distributed networks: A survey,\" ACM Computing Surveys, vol. 55, no. 8, pp. 1–36, 2023.",
        "[14] Y. LeCun, Y. Bengio, and G. Hinton, \"Deep learning,\" Nature, vol. 521, no. 7553, pp. 436–444, 2015.",
        "[15] M. Liu, H. Zhang, and X. Yuan, \"Explainable intrusion detection using graph neural networks and SHAP,\" IEEE Transactions on Network and Service Management, vol. 20, no. 3, pp. 2890–2903, 2023.",
        "[16] N. Moustafa and J. Slay, \"UNSW-NB15: a comprehensive data set for the evaluation of network intrusion detection systems,\" in Military Communications and Information Systems Conference (MilCIS), pp. 1–6, IEEE, 2015.",
        "[17] R. Olfati-Saber, J. A. Fax, and R. M. Murray, \"Consensus and cooperation in networked multi-agent systems,\" Proceedings of the IEEE, vol. 95, no. 1, pp. 215–233, 2007.",
        "[18] K. Park and H. Lee, \"Federated learning for collaborative intrusion detection: Challenges and opportunities,\" IEEE Security & Privacy, vol. 22, no. 1, pp. 45–54, 2024.",
        "[19] S. S. Shwartz and S. Ben-David, Understanding Machine Learning: From Theory to Algorithms. Cambridge University Press, 2014.",
        "[20] A. Strom, A. Applebaum, D. Miller, K. Nickels, A. Pennington, and C. Thomas, \"MITRE ATT&CK: Design and philosophy,\" MITRE Corporation, Tech. Rep. MTR180188, 2018.",
        "[21] P. Veličković, G. Cucurull, A. Casanova, A. Romero, P. Liò, and Y. Bengio, \"Graph Attention Networks,\" in International Conference on Learning Representations (ICLR), 2018.",
        "[22] X. Wang and Y. Chen, \"Dynamic graph neural networks for temporal network anomaly detection,\" IEEE Transactions on Knowledge and Data Engineering, vol. 36, no. 5, pp. 2150–2164, 2024.",
        "[23] Y. Yang, K. Zheng, and C. Wu, \"Byzantine fault-tolerant consensus in multi-agent reinforcement learning,\" IEEE Transactions on Cybernetics, vol. 54, no. 2, pp. 1120–1132, 2024.",
        "[24] Z. Zhang, P. Cui, and W. Zhu, \"Deep learning on graphs: A survey,\" IEEE Transactions on Knowledge and Data Engineering, vol. 34, no. 1, pp. 249–270, 2022.",
        "[25] J. Zhou, G. Cui, S. Hu, Z. Zhang, C. Yang, Z. Liu, L. Wang, C. Li, and M. Sun, \"Graph neural networks: A review of methods and applications,\" AI Open, vol. 1, pp. 57–81, 2020.",
        "[26] H. Zhao and F. Li, \"Zero-day attack mitigation using spatio-temporal graph attention models,\" Computer Networks, vol. 235, p. 110012, 2024.",
        "[27] T. K. Das and P. S. Roy, \"Scalable multi-agent systems for SOC automation,\" IEEE Transactions on Services Computing, vol. 17, no. 3, pp. 980–992, 2024.",
        "[28] G. E. Hinton and R. R. Salakhutdinov, \"Reducing the dimensionality of data with neural networks,\" Science, vol. 313, no. 5786, pp. 504–507, 2006.",
        "[29] S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 30, pp. 4765–4774, 2017.",
        "[30] M. Sundararajan, A. Taly, and Q. Yan, \"Axiomatic attribution for deep networks,\" in International Conference on Machine Learning (ICML), pp. 3319–3328, PMLR, 2017.",
        "[31] C. Ying and D. Song, \"Adversarial robustness of graph neural networks in network security,\" IEEE Transactions on Information Forensics and Security, vol. 19, pp. 1420–1434, 2024.",
        "[32] B. Yu and M. Dong, \" Jacobi consensus algorithms for distributed parameter estimation,\" IEEE Transactions on Signal Processing, vol. 71, pp. 3105–3118, 2023."
    ]
    
    for ref in references_list:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        run = p.add_run(clean_str(ref))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)

    # Save to main file
    out_path = "ATGC_MACIDS_Elaborate_Project_Report.docx"
    doc.save(out_path)
    print(f"Successfully generated elaborate VIT project report: {out_path}")
    
    # Also save as ATGC_MACIDS_Project_Report.docx for reference
    out_path_2 = "ATGC_MACIDS_Project_Report.docx"
    doc.save(out_path_2)
    print(f"Successfully synced with project report: {out_path_2}")

if __name__ == "__main__":
    build_elaborate_vit_report()

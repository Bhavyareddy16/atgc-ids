import torch
import torch.nn as nn
import logging

# Configure logger to act as SIEM integration
logging.basicConfig(level=logging.INFO, format='[SIEM ALERT] %(asctime)s - %(levelname)s - %(message)s')

class AutonomousResponseAgent(nn.Module):
    """
    Autonomous Response Planner Agent.
    Formulates mitigation actions based on consensus decisions and open-set novelty:
    - High-Confidence Anomaly -> Block IP/Ports (Firewall Update)
    - Zero-Day/Open-Set Intrusion -> Host Isolation & Quarantine
    - Low-Confidence -> Escalation to SIEM Analyst
    """
    def __init__(self, confidence_threshold=0.85):
        super(AutonomousResponseAgent, self).__init__()
        self.confidence_threshold = confidence_threshold
        
    def forward(self, node_indices, consensus_probs, is_zero_day_mask, attack_types):
        """
        Args:
            node_indices (Tensor): [N] - Original indices of network flows
            consensus_probs (Tensor): [N, num_classes] - Probability distributions after GCO
            is_zero_day_mask (Tensor): [N] - Boolean mask of zero-day detections
            attack_types (list): [N] - Decoded attack category strings
            
        Returns:
            actions_log (list): List of mitigation actions taken for each active alarm
        """
        actions_log = []
        
        # Max probabilities represent consensus confidence
        probs, preds = torch.max(consensus_probs, dim=-1)
        
        for idx in range(len(node_indices)):
            flow_id = node_indices[idx].item()
            prob = probs[idx].item()
            is_zd = is_zero_day_mask[idx].item()
            attack_cat = attack_types[idx]
            
            # Normal is mapped to class index 6 (or equivalent 'normal' category)
            # If the consensus is that the node is normal and NOT a zero-day, skip response
            if attack_cat == 'normal' and not is_zd:
                continue
                
            action_desc = f"Flow {flow_id}: "
            
            if is_zd:
                # Zero-Day anomaly detected (novelty is high)
                action_desc += "ZERO-DAY INTRUSION DETECTED. Action: Trigger Host Isolation & Quarantine. Update SIEM."
                logging.warning(f"Flow {flow_id} flagged as Zero-Day. Isolate host immediately.")
            elif prob >= self.confidence_threshold:
                # High confidence known attack
                action_desc += f"KNOWN ATTACK ({attack_cat.upper()}) DETECTED (Confidence: {prob:.2f}). Action: Block Source IP / Port via Firewall rule."
                logging.error(f"Flow {flow_id} identified as {attack_cat.upper()} with high confidence. Pushed rule to firewall.")
            else:
                # Low confidence attack alert
                action_desc += f"SUSPICIOUS FLOW ({attack_cat.upper()}) (Confidence: {prob:.2f}). Action: Escalate to SIEM SOC Analyst."
                logging.info(f"Flow {flow_id} marked suspicious. Escalated to SOC queue.")
                
            actions_log.append({
                'flow_id': flow_id,
                'is_zero_day': is_zd,
                'confidence': prob,
                'attack_category': attack_cat,
                'action_taken': action_desc
            })
            
        return actions_log

"""Clinical AI Evaluation Platform (Phase 70).

A production-grade pipeline to calculate rigorous mathematical metrics for:
1. NLP Classification (F1, Precision, Recall, Negation, Temporality)
2. Diagnosis (Top-1, Top-3, Top-5 Recall, MRR, Calibration, Abstention)
"""

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss

class ClinicalEvaluator:
    def __init__(self, class_labels):
        """
        Args:
            class_labels (list): List of possible diagnosis or entity classes.
        """
        self.class_labels = class_labels
        self.num_classes = len(class_labels)

    # -------------------------------------------------------------------------
    # Diagnosis Metrics (Ranking & Calibration)
    # -------------------------------------------------------------------------

    def calculate_top_k_recall(self, y_true_indices, y_prob_matrix, k=3):
        """
        Calculates whether the true class is within the top K predicted probabilities.
        """
        correct = 0
        total = len(y_true_indices)
        
        for i in range(total):
            true_idx = y_true_indices[i]
            probs = y_prob_matrix[i]
            
            # Get indices of top K probabilities (descending order)
            top_k_indices = np.argsort(probs)[-k:][::-1]
            
            if true_idx in top_k_indices:
                correct += 1
                
        return correct / total if total > 0 else 0.0

    def calculate_mrr(self, y_true_indices, y_prob_matrix):
        """
        Mean Reciprocal Rank (MRR). 
        Measures the average of the reciprocal ranks of the true diagnosis.
        """
        reciprocal_ranks = []
        total = len(y_true_indices)
        
        for i in range(total):
            true_idx = y_true_indices[i]
            probs = y_prob_matrix[i]
            
            # Sort indices by probability descending
            ranked_indices = np.argsort(probs)[::-1]
            
            # Find the rank (1-indexed) of the true class
            rank = np.where(ranked_indices == true_idx)[0][0] + 1
            reciprocal_ranks.append(1.0 / rank)
            
        return np.mean(reciprocal_ranks) if total > 0 else 0.0

    def calculate_calibration(self, y_true_indices, y_prob_matrix):
        """
        Computes the Brier Score across all classes (multi-class Brier Score).
        Lower is better (0.0 is perfect calibration).
        """
        # Convert y_true to one-hot encoding
        y_true_one_hot = np.zeros_like(y_prob_matrix)
        y_true_one_hot[np.arange(len(y_true_indices)), y_true_indices] = 1
        
        # Mean squared difference between predicted probabilities and actual outcomes
        brier_score = np.mean(np.sum((y_prob_matrix - y_true_one_hot) ** 2, axis=1))
        return brier_score

    def calculate_abstention_rate(self, y_pred_labels):
        """
        Calculates the percentage of inferences where the model safely abstained.
        Assumes 'ABSTAIN' is the literal label used by the confidence gating pipeline.
        """
        total = len(y_pred_labels)
        abstained = sum(1 for label in y_pred_labels if label == "ABSTAIN")
        return abstained / total if total > 0 else 0.0

    # -------------------------------------------------------------------------
    # NLP Extraction Metrics (NER, Negation, Temporality)
    # -------------------------------------------------------------------------

    def calculate_nlp_f1(self, y_true, y_pred, average='macro'):
        """
        Calculates standard Precision, Recall, and F1 for clinical NLP extraction.
        """
        precision = precision_score(y_true, y_pred, average=average, zero_division=0)
        recall = recall_score(y_true, y_pred, average=average, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=average, zero_division=0)
        
        return {"precision": precision, "recall": recall, "f1": f1}

    def calculate_modifier_accuracy(self, y_true_modifiers, y_pred_modifiers):
        """
        Evaluates accuracy for binary clinical modifiers like Negation (AFFIRMED/NEGATED)
        or Temporality (PAST/PRESENT).
        """
        correct = sum(1 for true, pred in zip(y_true_modifiers, y_pred_modifiers) if true == pred)
        total = len(y_true_modifiers)
        return correct / total if total > 0 else 0.0

    # -------------------------------------------------------------------------
    # Full Pipeline Report
    # -------------------------------------------------------------------------
    
    def generate_report(self, y_true_indices, y_prob_matrix, y_pred_labels, y_true_modifiers=None, y_pred_modifiers=None):
        """
        Generates a comprehensive evaluation dictionary.
        """
        report = {
            "Diagnosis": {
                "Top-1_Recall": self.calculate_top_k_recall(y_true_indices, y_prob_matrix, k=1),
                "Top-3_Recall": self.calculate_top_k_recall(y_true_indices, y_prob_matrix, k=3),
                "Top-5_Recall": self.calculate_top_k_recall(y_true_indices, y_prob_matrix, k=5),
                "Mean_Reciprocal_Rank": self.calculate_mrr(y_true_indices, y_prob_matrix),
                "Calibration_Brier_Score": self.calculate_calibration(y_true_indices, y_prob_matrix),
                "Abstention_Rate": self.calculate_abstention_rate(y_pred_labels)
            }
        }
        
        if y_true_modifiers and y_pred_modifiers:
            report["NLP"] = {
                "Modifier_Accuracy": self.calculate_modifier_accuracy(y_true_modifiers, y_pred_modifiers)
            }
            
        return report

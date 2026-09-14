"""DocAssistIQ ML Evaluation Metrics.

Computes standard clinical evaluation metrics including Top-K recall,
abstention rates, and class-wise precision/recall/F1.
"""

import numpy as np
from sklearn.metrics import classification_report, precision_recall_fscore_support


def compute_top_k_recall(y_true, y_pred_proba, k=3, classes=None):
    """
    Compute Top-K recall.
    A prediction is considered correct if the true class is among the top K predicted probabilities.

    Args:
        y_true: Array of true class labels.
        y_pred_proba: Array of shape (n_samples, n_classes) with predicted probabilities.
        k: The number of top predictions to consider.
        classes: Array of class labels matching the columns of y_pred_proba.

    Returns:
        float: Top-K recall score.
    """
    if classes is None:
        raise ValueError("Must provide classes array.")
    
    correct = 0
    for i, true_label in enumerate(y_true):
        # Get indices of top K probabilities
        top_k_indices = np.argsort(y_pred_proba[i])[-k:][::-1]
        top_k_classes = classes[top_k_indices]
        if true_label in top_k_classes:
            correct += 1
            
    return correct / len(y_true)


def evaluate_model(y_true, y_pred, y_pred_proba, classes, confidence_threshold=0.3):
    """
    Evaluate the model on standard metrics and compute abstention.
    
    Args:
        y_true: Array of true class labels.
        y_pred: Array of predicted class labels.
        y_pred_proba: Array of predicted probabilities.
        classes: Array of class labels.
        confidence_threshold: Probability below which the model abstains from predicting.
    
    Returns:
        dict: A dictionary of evaluation metrics.
    """
    # Calculate Abstention
    max_probs = np.max(y_pred_proba, axis=1)
    abstained = max_probs < confidence_threshold
    abstention_rate = np.mean(abstained)
    
    # Calculate metrics only on non-abstained samples
    y_true_confident = y_true[~abstained]
    y_pred_confident = y_pred[~abstained]
    y_proba_confident = y_pred_proba[~abstained]

    if len(y_true_confident) == 0:
        return {"abstention_rate": abstention_rate, "error": "Model abstained on all samples."}

    top_1 = compute_top_k_recall(y_true_confident, y_proba_confident, k=1, classes=classes)
    top_3 = compute_top_k_recall(y_true_confident, y_proba_confident, k=3, classes=classes)
    top_5 = compute_top_k_recall(y_true_confident, y_proba_confident, k=5, classes=classes)

    # Class-wise metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_confident, y_pred_confident, average="weighted", zero_division=0
    )
    
    report = classification_report(y_true_confident, y_pred_confident, zero_division=0)

    return {
        "abstention_rate": abstention_rate,
        "top_1_recall": top_1,
        "top_3_recall": top_3,
        "top_5_recall": top_5,
        "weighted_precision": precision,
        "weighted_recall": recall,
        "weighted_f1": f1,
        "classification_report": report
    }

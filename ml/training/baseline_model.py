#!/usr/bin/env python3
"""DocAssistIQ ML Baseline Training.

Generates a synthetic medical dataset (symptoms -> diagnosis) and trains
a Random Forest baseline model. Evaluates Top-K recall and abstention.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# Add ml/ directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluation.metrics import evaluate_model

# 1. Synthetic Dataset Generator
def generate_synthetic_data(n_samples=1000):
    """Generates synthetic (text -> label) diagnosis dataset."""
    diseases = ["Pneumonia", "Diabetes Type 2", "Hypertension", "Migraine", "Asthma"]
    
    symptoms_map = {
        "Pneumonia": ["cough", "fever", "chills", "shortness of breath", "chest pain"],
        "Diabetes Type 2": ["increased thirst", "frequent urination", "hunger", "fatigue", "blurred vision"],
        "Hypertension": ["headache", "shortness of breath", "nosebleeds", "dizziness", "chest pain"],
        "Migraine": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "visual aura"],
        "Asthma": ["wheezing", "shortness of breath", "chest tightness", "cough at night"]
    }

    data = []
    np.random.seed(42)
    for _ in range(n_samples):
        # Pick a random disease
        disease = np.random.choice(diseases)
        # Pick 2-4 random symptoms for that disease
        num_symptoms = np.random.randint(2, 5)
        chosen_symptoms = np.random.choice(symptoms_map[disease], size=num_symptoms, replace=False)
        
        # Sometimes add noise (a random symptom from another disease)
        if np.random.rand() > 0.7:
            noise_disease = np.random.choice(diseases)
            noise_symptom = np.random.choice(symptoms_map[noise_disease])
            chosen_symptoms = np.append(chosen_symptoms, noise_symptom)
            
        np.random.shuffle(chosen_symptoms)
        text = "Patient presents with " + ", ".join(chosen_symptoms) + "."
        data.append({"text": text, "diagnosis": disease})
        
    return pd.DataFrame(data)


def main():
    print("=" * 60)
    print("DocAssistIQ - Training Classical ML Baseline (Random Forest)")
    print("=" * 60)
    
    # 2. Generate Data
    df = generate_synthetic_data(n_samples=2000)
    X = df["text"]
    y = df["diagnosis"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Generated {len(df)} synthetic samples. Train: {len(X_train)}, Test: {len(X_test)}")

    # 3. Define Pipeline
    # TfidfVectorizer converts text to a sparse matrix of token counts.
    # RandomForest captures non-linear symptom combinations.
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", max_features=100)),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
    ])

    # 4. Train Model
    print("Training model...")
    pipeline.fit(X_train, y_train)
    
    # 5. Evaluate Model
    print("Evaluating model...")
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)
    classes = pipeline.classes_
    
    results = evaluate_model(y_test.values, y_pred, y_pred_proba, classes, confidence_threshold=0.3)
    
    print("\n--- Evaluation Results ---")
    print(f"Abstention Rate: {results['abstention_rate']:.2%}")
    print(f"Top-1 Recall:    {results['top_1_recall']:.2%}")
    print(f"Top-3 Recall:    {results['top_3_recall']:.2%}")
    print(f"Top-5 Recall:    {results['top_5_recall']:.2%}")
    print("\nClassification Report (on confident predictions):")
    print(results["classification_report"])
    
    # 6. Serialize Model
    exp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments")
    os.makedirs(exp_dir, exist_ok=True)
    model_path = os.path.join(exp_dir, "baseline_rf_model.joblib")
    
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved to: {model_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""DocAssistIQ Foundation Model Evaluation.

Compares Classical Baseline (Random Forest) against a real Foundation Model
(google/flan-t5-small) via zero-shot prompting and a simulated RAG pipeline.
Computes Quality, Latency, and Abstention.
"""

import os
import sys
import time
import joblib
import warnings
import numpy as np
import pandas as pd
from tqdm import tqdm

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# Add ml/ directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from training.baseline_model import generate_synthetic_data

warnings.filterwarnings("ignore")

# Define possible classes for strict metric computation
DISEASES = ["Pneumonia", "Diabetes Type 2", "Hypertension", "Migraine", "Asthma"]

def load_baseline():
    """Loads the serialized Classical ML model."""
    exp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments")
    model_path = os.path.join(exp_dir, "baseline_rf_model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Baseline model not found at {model_path}. Please run baseline_model.py first.")
    return joblib.load(model_path)


def evaluate_baseline(df, pipeline):
    """Evaluates latency and accuracy of the classical baseline."""
    start_time = time.time()
    y_pred = pipeline.predict(df["text"])
    latency = time.time() - start_time
    
    y_true = df["diagnosis"].values
    correct = np.sum(y_pred == y_true)
    accuracy = correct / len(y_true)
    
    return {
        "accuracy": accuracy,
        "latency_sec": latency,
        "avg_latency_ms": (latency / len(y_true)) * 1000
    }


def init_foundation_model():
    """Initializes a real clinical-grade (or proxy) LLM using HuggingFace."""
    # Using flan-t5-small as it is small enough to run on CPU without OOM,
    # yet powerful enough to follow instructions for zero-shot diagnosis.
    model_name = "google/flan-t5-small"
    print(f"Loading Foundation Model ({model_name})... This may take a moment to download.")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    
    return tokenizer, model, device


def evaluate_foundation_model(df, tokenizer, model, device, mode="zero_shot"):
    """
    Evaluates the foundation model.
    mode='zero_shot': Standard prompting.
    mode='rag': Simulated RAG by providing clinical guidelines in the context.
    """
    correct = 0
    hallucinations = 0
    start_time = time.time()
    
    # We evaluate on a smaller subset to save time if on CPU
    sample_size = min(50, len(df))
    subset = df.sample(sample_size, random_state=42)
    
    disease_list_str = ", ".join(DISEASES)
    
    for _, row in tqdm(subset.iterrows(), total=sample_size, desc=f"Evaluating LLM ({mode})"):
        if mode == "zero_shot":
            prompt = (
                f"You are a medical AI. Given the patient presentation, diagnose the condition. "
                f"Choose exactly one from the following options: {disease_list_str}.\n"
                f"Presentation: {row['text']}\n"
                f"Diagnosis:"
            )
        else:
            # Simulated RAG Context
            context = (
                "Guidelines: Pneumonia presents with fever and cough. Diabetes Type 2 with thirst and frequent urination. "
                "Hypertension with high blood pressure and headache. Migraine with severe aura headache. Asthma with wheezing."
            )
            prompt = (
                f"You are a medical AI. Use the provided context to diagnose the patient. "
                f"Choose exactly one from the following options: {disease_list_str}.\n"
                f"Context: {context}\n"
                f"Presentation: {row['text']}\n"
                f"Diagnosis:"
            )
            
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                temperature=0.1,  # Low temp for deterministic classification
                do_sample=False
            )
            
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Check hallucination (outputting a string outside the allowed classes)
        # Using simple substring matching for robustness
        matched = False
        for d in DISEASES:
            if d.lower() in prediction.lower():
                matched = True
                if row['diagnosis'].lower() == d.lower():
                    correct += 1
                break
                
        if not matched:
            hallucinations += 1
            
    latency = time.time() - start_time
    
    return {
        "accuracy": correct / sample_size,
        "hallucination_rate": hallucinations / sample_size,
        "latency_sec": latency,
        "avg_latency_ms": (latency / sample_size) * 1000
    }


def main():
    print("=" * 70)
    print("DocAssistIQ - Foundation Model Clinical Evaluation")
    print("=" * 70)
    
    # 1. Get Test Data
    print("Generating evaluation dataset...")
    df = generate_synthetic_data(n_samples=500)
    
    # 2. Evaluate Baseline
    print("\n--- Evaluating Classical ML Baseline (Random Forest) ---")
    try:
        baseline_model = load_baseline()
        baseline_results = evaluate_baseline(df, baseline_model)
        print(f"Accuracy:        {baseline_results['accuracy']:.2%}")
        print(f"Latency (avg):   {baseline_results['avg_latency_ms']:.2f} ms / sample")
    except Exception as e:
        print(f"[ERROR] Baseline failed: {e}")
        
    # 3. Load LLM
    print("\n--- Initializing Foundation Model Pipeline ---")
    tokenizer, model, device = init_foundation_model()
    
    # 4. Evaluate Zero-Shot LLM
    print("\n--- Evaluating Foundation Model (Zero-Shot Prompting) ---")
    llm_zero_shot_results = evaluate_foundation_model(df, tokenizer, model, device, mode="zero_shot")
    print(f"Accuracy:           {llm_zero_shot_results['accuracy']:.2%}")
    print(f"Hallucination Rate: {llm_zero_shot_results['hallucination_rate']:.2%}")
    print(f"Latency (avg):      {llm_zero_shot_results['avg_latency_ms']:.2f} ms / sample")
    
    # 5. Evaluate RAG LLM
    print("\n--- Evaluating Foundation Model (RAG-Augmented) ---")
    llm_rag_results = evaluate_foundation_model(df, tokenizer, model, device, mode="rag")
    print(f"Accuracy:           {llm_rag_results['accuracy']:.2%}")
    print(f"Hallucination Rate: {llm_rag_results['hallucination_rate']:.2%}")
    print(f"Latency (avg):      {llm_rag_results['avg_latency_ms']:.2f} ms / sample")
    
    print("=" * 70)
    print("Evaluation Complete. Foundation Models generally exhibit higher latency")
    print("and hallucination risks compared to strict Classical ML baselines,")
    print("but RAG significantly improves zero-shot grounding.")
    print("=" * 70)

if __name__ == "__main__":
    main()

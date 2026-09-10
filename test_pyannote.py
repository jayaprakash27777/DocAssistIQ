import os
import torch
from pyannote.audio import Pipeline
from dotenv import load_dotenv

# Load the environment variables to get the HF_TOKEN
load_dotenv(".env")
hf_token = os.getenv("HF_TOKEN")

if not hf_token:
    print("Error: HF_TOKEN is not set in .env")
    exit(1)

print(f"HF_TOKEN found: {hf_token[:8]}...")
print("Loading pyannote/speaker-diarization-3.1 ...")
try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )
    if pipeline is None:
        print("Failed to load pipeline (possibly missing agreement or bad token).")
        exit(1)
        
    print("Model loaded successfully!")
    
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
        print("Model moved to GPU successfully!")
    else:
        print("Running on CPU.")
        
    print("SUCCESS")
except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)

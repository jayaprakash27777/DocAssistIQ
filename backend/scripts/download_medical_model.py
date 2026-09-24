import os
import sys
import subprocess
import time
import requests

URL = "https://huggingface.co/Intelligent-Internet/II-Medical-8B-1706-GGUF/resolve/main/II-Medical-8B-1706.Q4_K_M.gguf"
DEST = r"c:\Users\User\Downloads\DocAssistIQ\backend\model_cache\II-Medical-8B-1706.Q4_K_M.gguf"
CACHE_DIR = r"c:\Users\User\Downloads\DocAssistIQ\backend\model_cache"
MODEL_NAME = "ii-medical:8b"
TOKEN = os.getenv("HF_TOKEN", "")

def main():
    print("===============================================================", flush=True)
    print("STEP 1: Starting High-Speed Streamed Download with HF Token", flush=True)
    print("===============================================================", flush=True)
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    existing_size = os.path.getsize(DEST) if os.path.exists(DEST) else 0

    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"
        mode = "ab"
        print(f"Resuming download from existing {existing_size // (1024*1024)} MB...", flush=True)
    else:
        mode = "wb"

    t0 = time.time()
    with requests.get(URL, headers=headers, stream=True, timeout=30) as r:
        if r.status_code not in (200, 206):
            print(f"Failed to connect to Hugging Face: {r.status_code} {r.text}", flush=True)
            sys.exit(1)

        total_size = int(r.headers.get("content-length", 0)) + existing_size
        downloaded = existing_size
        last_print = time.time()
        last_bytes = downloaded

        with open(DEST, mode) as f:
            for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_print >= 4.0:
                      speed_mb = (
                          (downloaded - last_bytes)
                          / (now - last_print)
                          / (1024 * 1024)
                      )
                      pct = (
                          (downloaded / total_size * 100) if total_size else 0
                      )
                      print(
                          f"Progress: {downloaded // (1024*1024)} MB /"
                          f" {total_size // (1024*1024)} MB ({pct:.1f}%) -"
                          f" {speed_mb:.1f} MB/s",
                          flush=True,
                      )
                      last_print = now
                      last_bytes = downloaded

    total_time = round(time.time() - t0, 1)
    print(f"\nDownload finished in {total_time}s! Final size: {round(os.path.getsize(DEST)/(1024**3), 2)} GB", flush=True)

    print("\n===============================================================", flush=True)
    print(f"STEP 2: Creating Ollama Modelfile for {MODEL_NAME}", flush=True)
    print("===============================================================", flush=True)
    
    modelfile_path = os.path.join(CACHE_DIR, "Modelfile.medical")
    modelfile_content = f"""FROM {DEST}
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
SYSTEM "You are II-Medical-8B, an expert clinical AI trained specifically for medical diagnosis, clinical note analysis, and evidence-grounded reasoning. Always provide rigorous, structured, and clinically sound insights."
"""
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)
    print(f"Modelfile created at {modelfile_path}", flush=True)

    print("\n===============================================================", flush=True)
    print(f"STEP 3: Registering {MODEL_NAME} with Ollama", flush=True)
    print("===============================================================", flush=True)
    res = subprocess.run(["ollama", "create", MODEL_NAME, "-f", modelfile_path], capture_output=True, text=True)
    print("STDOUT:", res.stdout, flush=True)
    print("STDERR:", res.stderr, flush=True)
    if res.returncode != 0:
        print("ERROR: Failed to register model with Ollama!", flush=True)
        sys.exit(1)

    print("\n===============================================================", flush=True)
    print(f"STEP 4: Testing Clinical Inference on {MODEL_NAME}", flush=True)
    print("===============================================================", flush=True)
    test_prompt = "What are the first-line interventions and diagnostic steps for a patient with acute crushing chest pain radiating to the left arm and jaw with ST-elevation in leads II, III, and aVF?"
    t_gen = time.time()
    run_res = subprocess.run(
        ["ollama", "run", MODEL_NAME, test_prompt],
        capture_output=True, text=True, timeout=120
    )
    gen_time = round(time.time() - t_gen, 1)
    print(f"Inference complete in {gen_time}s:\n", flush=True)
    print(run_res.stdout[:600] + "...\n", flush=True)

    # Reclaim disk space
    if os.path.exists(DEST):
        print(f"Removing temporary raw GGUF {DEST} to preserve disk space (Ollama has imported its blob)...", flush=True)
        try:
            os.remove(DEST)
            if os.path.exists(modelfile_path):
                os.remove(modelfile_path)
            print("Cleanup complete!", flush=True)
        except Exception as e:
            print(f"Note: Cleanup skipped: {e}", flush=True)

    print("\n===============================================================")
    print(f"SUCCESS: {MODEL_NAME} IS FULLY INSTALLED AND READY FOR DOCASSISTIQ!")
    print("===============================================================", flush=True)

if __name__ == "__main__":
    main()

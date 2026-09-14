#!/usr/bin/env python3
"""DocAssistIQ ML Environment Setup & Hardware Detection Script.

Probes the system for PyTorch/CUDA availability and evaluates hardware capabilities.
"""

import sys

def detect_hardware():
    print("=" * 60)
    print("DocAssistIQ - ML Hardware Detection")
    print("=" * 60)
    
    try:
        import torch
    except ImportError:
        print("[ERROR] PyTorch is not installed. Please install requirements.txt")
        sys.exit(1)

    print(f"PyTorch Version: {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available:  {cuda_available}")

    if cuda_available:
        gpu_count = torch.cuda.device_count()
        print(f"GPU Count:       {gpu_count}")
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            vram_gb = props.total_memory / (1024**3)
            print(f"  GPU {i}: {props.name} (VRAM: {vram_gb:.2f} GB)")
            
            # Simple heuristic for compatibility warnings
            if vram_gb < 8.0:
                print("    [WARN] VRAM is < 8GB. You may need to use quantization (4-bit/8-bit) or smaller batch sizes.")
            elif vram_gb < 16.0:
                print("    [INFO] VRAM is < 16GB. Suitable for fine-tuning smaller models (e.g. 7B parameters) with LoRA.")
            else:
                print("    [INFO] VRAM is sufficient for standard fine-tuning tasks.")
    else:
        print("[WARN] No CUDA device detected. Training will run on CPU and will be extremely slow.")

    print("=" * 60)
    print("Environment check complete.")


if __name__ == "__main__":
    detect_hardware()

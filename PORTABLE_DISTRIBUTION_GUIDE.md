# DocAssistIQ — Portable Self-Contained Distribution Guide

This project is packaged to be **100% self-contained**. Everything needed to run the application—source code, local database schema & seed data, AI/LLM models, Docker container orchestration, and dependencies—is bundled directly inside the `DocAssistIQ` directory.

---

## 📦 What Is Included in This Folder

| Component | Location | Details |
| :--- | :--- | :--- |
| **All Source Code** | `backend/`, `frontend/`, `ml/` | FastAPI REST API, Next.js 14 Web UI, ML Pipelines |
| **Database & Seeds** | `infra/postgres/01_docassistiq_seed.sql` | Complete PostgreSQL schema + all 51 relational tables + clinical & user data |
| **AI / LLM Models** | `models/ollama/models/` | `ii-medical:8b`, `llama3.1:8b`, `llama3.2:latest`, and `nomic-embed-text` |
| **Docker Orchestration** | `docker-compose.yml` | Multi-container setup for Database, Redis, MinIO, Ollama, Backend, and Frontend |
| **1-Click Launchers** | `START_ALL_DOCKER.bat`, `START_ALL_LOCAL.bat` | Automated one-click startup scripts for Windows |

---

## 💻 System Requirements for the Recipient

- **Operating System:** Windows 10/11 (or macOS / Linux with Docker Compose)
- **RAM:** Minimum **8 GB** (Recommended: **16 GB** or more to comfortably run 8B LLM models)
- **Disk Space:** ~15 GB to 25 GB free space
- **Software:** 
  - **Option 1 (Recommended):** [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
  - **Option 2 (Local Native):** Python 3.11+, Node.js 20+, and [Ollama for Windows](https://ollama.com)

---

## 🚀 How to Run for the Recipient (1-Click Run)

### Option 1: Run via Docker (Zero Configuration — Recommended)

1. Make sure **Docker Desktop** is running on your machine.
2. Double-click:
   ```cmd
   START_ALL_DOCKER.bat
   ```
3. The script will:
   * Validate Docker is running.
   * Auto-initialize `.env`.
   * Start PostgreSQL (with `pgvector` & auto-seed all 51 tables).
   * Start Redis and MinIO Object Storage.
   * Launch Ollama with the bundled models mounted from `./models/ollama/models`.
   * Start the Backend API and Next.js Frontend.
   * Automatically open `http://localhost:3000` in your web browser.

**To stop all services:** Double-click `STOP_ALL_DOCKER.bat`.

---

### Option 2: Run Natively on Windows (Python + Node.js)

If you prefer to run FastAPI and Next.js directly on your host machine:

1. Double-click:
   ```cmd
   START_ALL_LOCAL.bat
   ```
2. The script will:
   * Start the background database services in Docker (`db`, `redis`, `minio`).
   * Start Ollama pointing directly to the bundled `./models/ollama/models` folder (`set OLLAMA_MODELS=...`).
   * Initialize Python virtual environment and dependencies.
   * Launch FastAPI backend on port 8000 and Next.js frontend on port 3000.
   * Open `http://localhost:3000` in your browser.

---

## 🌐 Default Ports & Access Points

| Service | URL / Port | Credentials / Purpose |
| :--- | :--- | :--- |
| **Web Application** | [http://localhost:3000](http://localhost:3000) | Main Medical Hub UI |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | FastAPI Core Backend |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger OpenAPI Explorer |
| **Ollama LLM Engine** | [http://localhost:11434](http://localhost:11434) | Local LLM inference & embeddings |
| **MinIO Storage Console** | [http://localhost:9011](http://localhost:9011) | User: `minioadmin` / Pass: `minioadmin` |
| **PostgreSQL Database** | `localhost:5434` (Docker: `5432`) | User: `docassistiq` / Pass: `changeme` |
| **Redis Cache** | `localhost:6379` | Message broker & cache |

---

## 🩺 Pre-Seeded Verified Doctor Accounts (Ready to Log In)

All accounts share the default development password: **`DoctorSecure2026!`**

| Email | Doctor Name | Specialty |
| :--- | :--- | :--- |
| `dr.chen@docassistiq.com` | Dr. Sarah Chen, MD, FACC | Cardiology |
| `dr.vance@docassistiq.com` | Dr. David Vance, MD, FAAN | Neurology |
| `dr.rostova@docassistiq.com` | Dr. Elena Rostova, MD, PhD | Pediatrics / Infectious Disease |
| `dr.thorne@docassistiq.com` | Dr. Marcus Thorne, MD, FACEP | Emergency Medicine / Critical Care |
| `dr.nair@docassistiq.com` | Dr. Priya Nair, MD, DNB | Dermatology |

*(Logging in with any of these accounts activates full doctor privileges, peer discussion feeds, and turns the real-time WebSocket connection to **LIVE**).*

---

## 🎙️ Speech-to-Text & Clinical Models Included
- **Faster-Whisper (`models--Systran--faster-whisper-base.en` & `tiny`):** Pre-cached in [`backend/model_cache/`](file:///c:/Users/User/Downloads/DocAssistIQ/backend/model_cache). Live transcription and voice consultation require zero model downloads.
- **Ollama Models:** `ii-medical:8b`, `llama3.1:8b`, `llama3.2:latest`, and `nomic-embed-text` located in [`models/ollama/models/`](file:///c:/Users/User/Downloads/DocAssistIQ/models/ollama/models).


---

## 📤 How to Share / Copy This Folder to Someone Else

When sending this folder to another person or copying to an external drive:

1. **Run the Packager Script:**
   ```cmd
   scripts\export_portable_package.bat
   ```
   This ensures the latest database dump is exported to `infra/postgres/01_docassistiq_seed.sql` and cleans any unnecessary build caches.

2. **Copying the Models:**
   * In Windows File Explorer, copying the `DocAssistIQ` folder to an external SSD or USB drive will automatically resolve the junction and copy all model weights (`~11 GB`).
   * Alternatively, zip the `DocAssistIQ` folder using **7-Zip** or **Windows Compress to ZIP**.

3. **Handing Off:**
   The recipient only needs to extract the folder, open Docker Desktop, and double-click `START_ALL_DOCKER.bat`.

---

## 🔧 Troubleshooting

- **Port Conflict (e.g. 5432 or 8000 already in use):**
  Edit `.env` and change `BACKEND_PORT`, `FRONTEND_PORT`, or `DB_PORT` to an open port (e.g., `DB_PORT=5435`).
- **Ollama Out-of-Memory:**
  If the recipient's machine has 8 GB RAM, configure `DEFAULT_LLM_MODEL=llama3.2:latest` in `.env` (a lighter 2 GB model instead of the 8B model).
- **GPU Acceleration:**
  If an NVIDIA GPU with CUDA drivers is present on the recipient machine, Docker Desktop will utilize it with WSL2 GPU passthrough enabled. If no GPU is present, it will automatically run smoothly in CPU mode.

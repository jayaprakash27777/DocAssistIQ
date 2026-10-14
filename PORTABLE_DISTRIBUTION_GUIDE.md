# DocAssistIQ — Portable Self-Contained Distribution Guide

This project is packaged to be **100% self-contained**. Everything needed to run the application—source code, local database schema & seed data, AI/LLM models, Docker container orchestration, and dependencies—is bundled directly inside the `DocAssistIQ` directory.

---

## 📦 What Is Included in This Folder

| Component | Location | Details |
| :--- | :--- | :--- |
| **All Source Code** | `backend/`, `frontend/`, `ml/` | FastAPI REST API, Next.js 14 Web UI, ML Pipelines |
| **Complete Database & Seeds** | `infra/postgres/01_docassistiq_seed.sql` | Complete PostgreSQL schema + all 51 relational tables + clinical & user data (3.1 MB) |
| **AI / LLM Models (Physical)** | `models/ollama/models/` | 11.4 GB model weights physically bundled: `ii-medical:8b`, `llama3.1:8b`, `llama3.2:latest`, and `nomic-embed-text` |
| **Speech-to-Text Models** | `backend/model_cache/`, `model_cache/` | `faster-whisper-base.en` & `faster-whisper-tiny` pre-cached for 100% offline transcription |
| **Offline Python Wheels** | `backend/wheels/` | 100 pre-downloaded Python wheels (143 MB) for zero-internet backend installation |
| **Frontend Dependencies** | `frontend/node_modules/` | Fully installed Node modules + pre-compiled `.next` build cache |
| **Full Documentation & PPTX** | Root directory | `DocAssistIQ_Comprehensive_Project_Report.docx`, `DocAssistIQ_Architecture_Presentation.pptx`, `DocAssistIQ_Master_All_In_One_4K_Presentation.pptx`, PNG/SVG Architecture Diagrams |
| **Docker Orchestration** | `docker-compose.yml` | Multi-container setup for Database, Redis, MinIO, Ollama, Backend, and Frontend |
| **1-Click Safe Launchers** | `start_safely.bat`, `stop_safely.bat` | Enterprise safe startup & shutdown protocols (auto Docker boot, port hygiene, auto browser load) |

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

### Primary Safe Launcher (Recommended)

1. Double-click:
   ```cmd
   start_safely.bat
   ```
   *(or `START_ALL_LOCAL.bat`)*
2. The protocol will automatically:
   * Auto-detect or launch Docker Desktop in the background.
   * Verify and safely boot PostgreSQL (`:5434`), Redis (`:6379`), and MinIO (`:9010`).
   * Verify and launch the local Ollama AI Engine (`:11434`) using the bundled models.
   * Sweep stale TCP sockets on ports `8000` and `3000` with automated cooldown.
   * Initialize Python virtual environment and dependencies.
   * Launch the FastAPI clinical backend engine on `http://127.0.0.1:8000`.
   * Launch the Next.js clinical frontend cockpit on `http://localhost:3000`.
   * Automatically launch your default web browser directly to `http://localhost:3000`.
   * Keep an interactive, protected console monitor with `[S]` Status Probe, `[B]` Browser Re-open, and `[Q]` Clean Safe Shutdown.

**To safely stop all services at any time:** Double-click `stop_safely.bat` (or press `Q` in the console monitor). All database records and caches are preserved without data loss.


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

**To stop all services safely at any time:** Double-click `stop_safely.bat` (or `STOP_ALL_LOCAL.bat`). This flushes sockets and preserves all patient records, findings, and caches.

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

2. **Copying or Zipping the Folder:**
   * Because all models (`models/ollama/models`, `backend/model_cache`), libraries (`backend/wheels`, `frontend/node_modules`), database seeds, and documents are **physically present inside this `DocAssistIQ` directory**, you can simply:
     - **Copy to USB / External SSD:** Drag and drop the `DocAssistIQ` folder to an external drive.
     - **Zip Archive:** Right-click `DocAssistIQ` -> **Send to** -> **Compressed (zipped) folder** (or use **7-Zip** / **WinRAR**).
   * Total folder size is ~14 to 15 GB (with all LLM weights and dependencies included).

3. **Handing Off to Another Machine:**
   The recipient extracts or copies the folder to their computer, and runs:
   - **Docker:** Double-click `START_ALL_DOCKER.bat` (starts all containers and loads seed data + local models).
   - **Native Windows:** Double-click `START_ALL_LOCAL.bat` (auto-creates `.venv` and installs from bundled `backend/wheels` offline with zero internet needed).

---

## 🔧 Troubleshooting

- **Port Conflict (e.g. 5432 or 8000 already in use):**
  Edit `.env` and change `BACKEND_PORT`, `FRONTEND_PORT`, or `DB_PORT` to an open port (e.g., `DB_PORT=5435`).
- **Ollama Out-of-Memory:**
  If the recipient's machine has 8 GB RAM, configure `DEFAULT_LLM_MODEL=llama3.2:latest` in `.env` (a lighter 2 GB model instead of the 8B model).
- **GPU Acceleration:**
  If an NVIDIA GPU with CUDA drivers is present on the recipient machine, Docker Desktop will utilize it with WSL2 GPU passthrough enabled. If no GPU is present, it will automatically run smoothly in CPU mode.

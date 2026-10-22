# IndusVision — AI-Powered Smart Industrial Monitoring & Management System

A modular Industry 4.0 platform combining AI computer vision (PPE detection), IoT sensor monitoring,
predictive maintenance, inventory management, alerts, and a centralized dashboard.

## Stack

| Layer | Technology |
|---|---|
| AI / Computer Vision | YOLOv8, OpenCV, Ultralytics |
| IoT | ESP32, DHT22, SW-420, ACS712, HC-SR04, MQ-2 |
| Backend | FastAPI, MongoDB (Motor async driver), JWT auth |
| AI Insights | Google Gemini API (narrative summaries, chat assistant) |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts |
| Deployment | Docker, Docker Compose, Nginx |

## Folder Structure

```
IndusVision/
├── Backend/                # FastAPI, MongoDB, and the complete AI workflow in Backend/ai
├── iot/                    # ESP32 firmware + wiring docs + local test server
├── Frontend/               # React + Tailwind dashboard
├── Worker-Safety/          # Trained PPE model weights (best.pt)
├── Docs/                   # Wiring guide, dataset guide, how-to-run guides
├── datasets/css/           # Downloaded PPE dataset expected by Backend/ai/dataset.yaml
├── docker-compose.yml      # Runs mongo + backend + frontend together
└── requirements.txt        # Installs Backend/requirements.txt
```

## Quick Start (Local, without Docker)

### 1. MongoDB
Install MongoDB Community Edition locally (https://www.mongodb.com/try/download/community), or run:
```bash
docker run -d -p 27017:27017 --name indusvision_mongo mongo:7
```

### 2. Backend
```bash
cd Backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env: set GEMINI_API_KEY at minimum
python seed_data.py             # creates admin user + sample machines/inventory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs: http://localhost:8000/docs
Default login (change immediately): `admin@indusvision.local` / `Admin@123`
For ESP32 uploads the API binds to the LAN with `--host 0.0.0.0`; use the PC's Wi-Fi IPv4 address in the firmware, not `localhost`.

### 3. Frontend
```bash
cd Frontend
npm install
cp .env.example .env            # points at http://localhost:8000 by default
npm run dev
```
Dashboard: http://localhost:5173

### 4. IoT (optional, needs real ESP32 hardware)
See `Docs/IoT_How_To_Run.md`. Point the firmware's `BACKEND_URL` at
`http://<your-computer-IP>:8000/api/sensors/ingest` (the real backend now — you can retire `iot/test_server.py`).

### 5. Worker Safety AI
The Worker Safety page captures a browser webcam feed and analyzes frames with the already-trained `Worker-Safety/best.pt`; allow camera access when prompted. For the notebook-style OpenCV window or model evaluation/export, use the tools in `Backend/ai`:
```bash
python Backend/ai/predict.py --source 0
```
Training and dataset setup are documented in `Docs/Dataset_And_Training_Guide.md`; inference does not retrain or replace your model.

## Quick Start (Docker Compose — everything at once)

```bash
# from the IndusVision/ root
cp Backend/.env.example .env   # edit GEMINI_API_KEY, JWT_SECRET_KEY here
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs
- MongoDB: localhost:27017

Then exec into the backend container once to seed data:
```bash
docker exec -it indusvision_backend python seed_data.py
```

## Where Gemini Fits In

YOLOv8 handles all visual detection (PPE, hazards) — that's a computer-vision model's job and Gemini
is not used for it. Gemini is used for the reasoning/writing layer on top:
- **Machine Health page → "Ask Gemini"**: turns raw sensor history + the rule-based prediction into a
  plain-English summary for a supervisor.
- **Reports → Safety Report (PDF/Excel)**: Gemini writes the narrative paragraph summarizing the
  period's PPE violations; the table of raw data comes straight from MongoDB.
- **Settings → Ask AI Assistant**: general Q&A grounded in a machine's recent sensor data.

Get a free Gemini API key at https://aistudio.google.com/app/apikey and set `GEMINI_API_KEY` in
`Backend/.env`. Every Gemini-backed endpoint fails gracefully with a clear message if the key isn't set —
nothing else in the app depends on it.

## Database (MongoDB Collections)

| Collection | Purpose |
|---|---|
| `users` | Auth + role-based access (admin/engineer/supervisor/operator) |
| `machines` | Registered machines, live status, health score |
| `sensor_readings` | Raw IoT sensor history per machine |
| `detections` | AI/YOLO detection logs, flagged violations |
| `inventory` | Stock items, thresholds |
| `suppliers`, `orders` | Supplier + purchase order tracking |
| `alerts` | Unified alert feed from sensors/detections/inventory/manual |
| `maintenance` | Predictive maintenance score snapshots per reading |
| `activity_logs` | (reserved for audit trail — extend as needed) |

## Role-Based Access

| Role | Can do |
|---|---|
| `admin` | Everything, including user management |
| `engineer` | Manage machines, inventory, suppliers, orders, alerts |
| `supervisor` | Manage inventory/orders, acknowledge/resolve alerts |
| `operator` | View dashboards, update inventory quantities, acknowledge alerts |

First admin is created via `POST /api/auth/bootstrap-admin` (works once, when the `users` collection is
empty) — `seed_data.py` already does this for you.

## Upgrading the Predictive Maintenance Model

`Backend/app/services/predictive_maintenance.py` currently uses a rule-based scoring function so the
whole pipeline works from day one. Once you've logged enough real sensor history
(`GET /api/reports/sensor-history/{machine_id}` exports it as CSV), train a real Random
Forest/XGBoost classifier and swap it in — the function signature and return shape are documented
in that file so nothing else in the app needs to change.

## Known Limitations / Next Steps for Your Report

- The `/api/sensors/ingest` and `/api/detections` endpoints are intentionally left without device-level
  auth (ESP32/AI clients can't easily hold a JWT) — see the security note at the bottom of
  `Backend/app/routes/sensors.py` for how to add a device API key for production.
- Predictive maintenance is rule-based until you train on real historical data (see above).
- The Worker Safety page currently analyzes uploaded images; continuous camera streaming needs an MJPEG/WebRTC bridge.
- Chart.js was swapped for Recharts (React-native, no ref/lifecycle fighting) — still satisfies the
  original tech-stack intent of chart visualizations.

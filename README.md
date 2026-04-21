# Browser Object Detection + Flask API

# this is the feature branch 1
# This is from featur 2

A teaching project combining real-time computer vision in the browser with a
Flask REST API for logging and analytics.

## Architecture

```
Browser (webcam + TensorFlow.js COCO-SSD)
         │
         │   HTTP POST /api/detections
         ▼
Flask API (Python)
         │
         ▼
SQLite database (detections.db)
```

- The **browser** runs object detection locally using TensorFlow.js.
- The **Flask API** logs detections, returns history, and computes stats.
- **CORS** is enabled so the two servers can talk across ports.

## Project Structure

```
object-detection-app/
├── backend/
│   ├── app.py              # Flask API
│   ├── requirements.txt    # Python dependencies
│   └── detections.db       # Auto-created on first run
├── frontend/
│   └── index.html          # Browser CV + UI
└── README.md
```

## Setup

### 1. Backend (Flask API)

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API will start on `http://localhost:5000`.

Test it:
```bash
curl http://localhost:5000/api/health
```

### 2. Frontend (Browser App)

Open a SECOND terminal and run:

```bash
cd frontend
python -m http.server 8000
```

Then open `http://localhost:8000` in Chrome or Firefox.

**Note:** You MUST serve the HTML file via HTTP (not open it directly with
`file://`), otherwise the browser will block webcam access.

## Running Tests

```bash
cd backend
pytest test_app.py -v
```

## API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | `/api/health`         | Health check                             |
| POST   | `/api/detections`     | Log a new detection                      |
| GET    | `/api/detections`     | Get 50 most recent detections            |
| GET    | `/api/stats`          | Aggregate stats per label                |

### Example POST payload
```json
{
  "label": "person",
  "confidence": 0.92
}
```

### Example GET /api/stats response
```json
[
  {"label": "person", "count": 47, "avg_confidence": 0.871},
  {"label": "cup", "count": 12, "avg_confidence": 0.723}
]
```

## Teaching Exercises

Try these to extend the project:

1. Add a `DELETE /api/detections/<id>` endpoint.
2. Add query filtering: `GET /api/detections?label=person`.
3. Add a confidence threshold slider to the UI.
4. Build a dashboard page that charts `/api/stats` using Chart.js.
5. Break it on purpose — send malformed JSON and see how the API responds.

## Troubleshooting

- **Camera not starting:** Make sure you're on `http://localhost` (not
  `file://`) and that you granted camera permission.
- **CORS errors:** Make sure the Flask backend is running and `flask-cors`
  is installed.
- **Model slow to load:** First load pulls COCO-SSD weights (~27 MB) from
  the CDN. Subsequent loads are cached.

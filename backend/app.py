from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
from contextlib import closing

app = Flask(__name__)
CORS(app)  # Allow browser (different port) to call this API

DB_PATH = "detections.db"


def init_db():
    """Create the detections table if it doesn't exist."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()


@app.route("/api/health", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify({"status": "ok", "service": "object-detection-api"})


@app.route("/api/detections", methods=["POST"])
def log_detection():
    """
    Log a detection from the browser.
    Expected JSON: { "label": "person", "confidence": 0.92 }
    """
    data = request.get_json()

    # Basic validation
    if not data or "label" not in data or "confidence" not in data:
        return jsonify({"error": "Missing 'label' or 'confidence'"}), 400

    label = data["label"]
    confidence = float(data["confidence"])
    timestamp = datetime.utcnow().isoformat()

    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO detections (label, confidence, timestamp) VALUES (?, ?, ?)",
            (label, confidence, timestamp),
        )
        conn.commit()

    return jsonify({
        "message": "Detection logged",
        "label": label,
        "confidence": confidence,
        "timestamp": timestamp,
    }), 201


@app.route("/api/detections", methods=["GET"])
def get_detections():
    """Return the 50 most recent detections."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM detections ORDER BY id DESC LIMIT 50"
        ).fetchall()
        return jsonify([dict(row) for row in rows])


@app.route("/api/stats", methods=["GET"])
def stats():
    """Return counts per label — useful for a dashboard."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute("""
            SELECT label, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM detections
            GROUP BY label
            ORDER BY count DESC
        """).fetchall()
        return jsonify([
            {"label": r[0], "count": r[1], "avg_confidence": round(r[2], 3)}
            for r in rows
        ])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

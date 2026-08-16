import os, sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = os.environ.get("DB_PATH", "keys.db")

def init():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS keys
                (key TEXT PRIMARY KEY, device_id TEXT,
                 expires_at TEXT, active INTEGER DEFAULT 1)""")
    c.commit(); c.close()

@app.post("/api/connect")
def connect():
    data = request.get_json(silent=True) or request.form
    key, device = str(data.get("key","")).strip(), str(data.get("device_id","")).strip()
    if not key or not device:
        return jsonify(success=False, status="missing"), 400
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    row = c.execute("SELECT * FROM keys WHERE key=?", (key,)).fetchone()
    if not row or not row["active"]:
        c.close(); return jsonify(success=False, status="invalid"), 401
    if row["device_id"] and row["device_id"] != device:
        c.close(); return jsonify(success=False, status="device_mismatch"), 403
    if not row["device_id"]:
        c.execute("UPDATE keys SET device_id=? WHERE key=?", (device,key)); c.commit()
    if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
        c.close(); return jsonify(success=False, status="expired"), 403
    c.close()
    return jsonify(success=True, status="valid", product="ABO ALTNANIN")

@app.get("/health")
def health(): return jsonify(ok=True)

if __name__ == "__main__":
    init(); app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

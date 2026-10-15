from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "registre_db"),
    )

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personnes (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            nom        VARCHAR(100) NOT NULL,
            prenom     VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    cur.close()
    db.close()
    print("Base de données initialisée")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/personnes", methods=["GET"])
def get_personnes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM personnes ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    db.close()
    # Convert datetime to string for JSON serialization
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = str(r["created_at"])
    return jsonify(rows)

@app.route("/api/personnes", methods=["POST"])
def add_personne():
    data = request.get_json()
    nom    = (data.get("nom") or "").strip()
    prenom = (data.get("prenom") or "").strip()
    if not nom or not prenom:
        return jsonify({"error": "nom et prenom sont requis"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO personnes (nom, prenom) VALUES (%s, %s)", (nom, prenom))
    db.commit()
    new_id = cur.lastrowid
    cur.close()
    db.close()
    return jsonify({"id": new_id, "nom": nom, "prenom": prenom}), 201

@app.route("/api/personnes/<int:pid>", methods=["DELETE"])
def delete_personne(pid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM personnes WHERE id = %s", (pid,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Supprimé"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

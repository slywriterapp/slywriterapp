from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = "word_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/update_usage", methods=["POST"])
def update_usage():
    body = request.get_json()
    uid = body.get("user_id")
    amount = body.get("words", 0)

    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data()
    data[uid] = data.get(uid, 0) + amount
    save_data(data)

    return jsonify({"status": "ok", "total_user_words": data[uid]})

@app.route("/get_usage", methods=["GET"])
def get_usage():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data()
    return jsonify({"words": data.get(uid, 0)})

@app.route("/total_words", methods=["GET"])
def total_words():
    data = load_data()
    total = sum(data.values())
    return jsonify({"total_words": total})

@app.route("/debug_all_users", methods=["GET"])
def debug_all_users():
    return jsonify(load_data())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from flask import Flask, request, jsonify, redirect
import json
import os
import hashlib

app = Flask(__name__)

USAGE_FILE = "word_data.json"
PLAN_FILE = "plan_data.json"
REFERRAL_FILE = "referral_data.json"

def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- WORD USAGE ----------------

@app.route("/update_usage", methods=["POST"])
def update_usage():
    body = request.get_json()
    uid = body.get("user_id")
    amount = body.get("words", 0)

    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data(USAGE_FILE)
    data[uid] = data.get(uid, 0) + amount
    save_data(USAGE_FILE, data)

    return jsonify({"status": "ok", "total_user_words": data[uid]})

@app.route("/get_usage", methods=["GET"])
def get_usage():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data(USAGE_FILE)
    return jsonify({"words": data.get(uid, 0)})

@app.route("/total_words", methods=["GET"])
def total_words():
    data = load_data(USAGE_FILE)
    total = sum(data.values())
    return jsonify({"total_words": total})

@app.route("/debug_all_users", methods=["GET"])
def debug_all_users():
    return jsonify(load_data(USAGE_FILE))

# ---------------- PLAN MANAGEMENT ----------------

@app.route("/get_plan", methods=["GET"])
def get_plan():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    plans = load_data(PLAN_FILE)
    return jsonify({"plan": plans.get(uid, "free")})

@app.route("/set_plan", methods=["POST"])
def set_plan():
    body = request.get_json()
    uid = body.get("user_id")
    new_plan = body.get("plan")

    if not uid or new_plan not in ["free", "pro", "premium", "enterprise"]:
        return jsonify({"error": "Missing or invalid data"}), 400

    plans = load_data(PLAN_FILE)
    plans[uid] = new_plan
    save_data(PLAN_FILE, plans)

    return jsonify({"status": "ok", "plan": new_plan})

@app.route("/debug_all_plans", methods=["GET"])
def debug_all_plans():
    return jsonify(load_data(PLAN_FILE))

# ---------------- REFERRALS ----------------

@app.route("/get_referrals", methods=["GET"])
def get_referrals():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    # Get referral code for user (generate if not exists)
    user_code = None
    for code, owner in code_map.items():
        if owner == uid:
            user_code = code
            break

    if not user_code:
        # Generate code: short hash of user ID
        user_code = hashlib.sha256(uid.encode()).hexdigest()[:8]
        code_map[user_code] = uid
        ref_data["code_map"] = code_map
        save_data(REFERRAL_FILE, ref_data)

    # Count how many people this user referred
    referred_count = sum(1 for referrer in ref_by_uid.values() if referrer == uid)

    return jsonify({
        "referral_code": user_code,
        "referrals": referred_count
    })

@app.route("/apply_referral", methods=["POST"])
def apply_referral():
    body = request.get_json()
    new_user = body.get("user_id")
    referral_code = body.get("referral_code")

    if not new_user or not referral_code:
        return jsonify({"error": "Missing data"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    if new_user in ref_by_uid:
        return jsonify({"status": "already_set"})

    referrer_uid = code_map.get(referral_code)
    if not referrer_uid or referrer_uid == new_user:
        return jsonify({"error": "Invalid referral code"}), 400

    ref_by_uid[new_user] = referrer_uid
    ref_data["by_uid"] = ref_by_uid
    save_data(REFERRAL_FILE, ref_data)

    return jsonify({"status": "ok", "referred_by": referrer_uid})

@app.route("/signup", methods=["GET"])
def signup_with_referral():
    referral_code = request.args.get("ref")
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    # Apply referral if valid and not already set
    if referral_code:
        referrer_uid = code_map.get(referral_code)
        if not referrer_uid:
            return jsonify({"error": "Invalid referral code"}), 400
        if user_id == referrer_uid:
            return jsonify({"error": "Cannot refer yourself"}), 400
        if user_id not in ref_by_uid:
            ref_by_uid[user_id] = referrer_uid
            ref_data["by_uid"] = ref_by_uid
            save_data(REFERRAL_FILE, ref_data)

    # Redirect to app download
    return redirect("https://slywriter.com/download")

@app.route("/referral_bonus", methods=["POST"])
def referral_bonus():
    body = request.get_json()
    referrer_id = body.get("referrer_id")
    referred_id = body.get("referred_id")

    if not referrer_id or not referred_id:
        return jsonify({"error": "Missing user IDs"}), 400
    if referrer_id == referred_id:
        return jsonify({"error": "Self-referral not allowed"}), 400

    ref_data = load_data(REFERRAL_FILE)
    rewarded_pairs = ref_data.get("rewarded_pairs", [])
    pair_key = f"{referrer_id}→{referred_id}"

    if pair_key in rewarded_pairs:
        return jsonify({"status": "already_rewarded"}), 200

    # Grant word bonuses
    word_data = load_data(USAGE_FILE)
    word_data[referrer_id] = word_data.get(referrer_id, 0) + 1000
    word_data[referred_id] = word_data.get(referred_id, 0) + 1000
    save_data(USAGE_FILE, word_data)

    rewarded_pairs.append(pair_key)
    ref_data["rewarded_pairs"] = rewarded_pairs
    save_data(REFERRAL_FILE, ref_data)

    return jsonify({
        "status": "bonus_applied",
        "referrer_total": word_data[referrer_id],
        "referred_total": word_data[referred_id]
    })

@app.route("/debug_referrals", methods=["GET"])
def debug_referrals():
    return jsonify(load_data(REFERRAL_FILE))

# ---------------- AI FILLER GENERATION ----------------

@app.route('/generate_filler', methods=['POST'])
def generate_filler():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"error": "OpenAI key not set"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')
    model = data.get('model', 'gpt-5-nano')  # Updated to use latest model

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are a human typing a first draft. "
                    "Generate a single plausible but ultimately unused or rambling sentence, "
                    "or a short filler clause, that someone might type, hesitate, then erase while writing."
                )},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=36
        )
        filler = response.choices[0].message.content.strip()
        return jsonify({"filler": filler})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- AI TEXT GENERATION ----------------

@app.route('/ai_generate_text', methods=['POST'])
def ai_generate_text():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')
    user_id = data.get('user_id')
    
    if not prompt:
        return jsonify({"success": False, "error": "Missing prompt"}), 400

    try:
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": "You are a helpful writing assistant."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        generated_text = response.choices[0].message.content.strip()
        
        return jsonify({
            "success": True,
            "text": generated_text
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/ai_humanize_text', methods=['POST'])
def ai_humanize_text():
    import requests
    
    data = request.get_json()
    text = data.get('text', '')
    model = data.get('model', '1')  # Default to balanced
    user_id = data.get('user_id')
    
    if not text:
        return jsonify({"success": False, "error": "Missing text"}), 400
    
    try:
        # Get AIUndetect credentials from environment variables
        api_key = os.environ.get("AIUNDETECT_API_KEY")
        email = os.environ.get("AIUNDETECT_EMAIL")
        
        if not api_key or not email:
            return jsonify({"success": False, "error": "AIUndetect credentials not configured on server"}), 500
        
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'mail': email,
            'data': text
        }
        
        response = requests.post(
            'https://aiundetect.com/api/v1/rewrite',
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return jsonify({
                    "success": True,
                    "humanized_text": result.get('data')
                })
            else:
                error_codes = {
                    1001: "Missing API key",
                    1002: "Rate limit exceeded", 
                    1003: "Invalid API Key",
                    1004: "Request parameter error",
                    1005: "Text language not supported",
                    1006: "You don't have enough words",
                    1007: "Server Error"
                }
                error_msg = error_codes.get(result.get('code'), f"Unknown error (code: {result.get('code')})")
                return jsonify({"success": False, "error": f"AIUndetect error: {error_msg}"}), 500
        else:
            return jsonify({"success": False, "error": f"HTTP {response.status_code}: {response.text}"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- MAIN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

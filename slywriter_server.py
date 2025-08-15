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
        # Enhanced system prompt to ensure adequate length
        system_prompt = (
            "You are a helpful writing assistant. IMPORTANT: Always generate comprehensive, "
            "detailed responses with proper depth and length. Never provide brief or short answers. "
            "Aim for at least 200-300 words minimum, with thorough explanations and examples."
        )
        
        # First attempt
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        generated_text = response.choices[0].message.content.strip()
        
        # Check if generated text is too short (less than 200 characters)
        if len(generated_text) < 200:
            print(f"[AI] First attempt too short ({len(generated_text)} chars), retrying with enhanced prompt...")
            
            # Enhanced prompt for retry
            enhanced_prompt = f"""{prompt}

IMPORTANT: Please provide a comprehensive, detailed response with:
- At least 300-500 words
- Multiple paragraphs with full explanations
- Specific examples and details
- Thorough coverage of the topic
- No brief or summary responses

Original prompt: {prompt}"""
            
            # Retry with enhanced prompt
            retry_response = client.chat.completions.create(
                model='gpt-5-nano',
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_completion_tokens=2000
            )
            
            retry_text = retry_response.choices[0].message.content.strip()
            
            # Use the longer of the two responses
            if len(retry_text) > len(generated_text):
                generated_text = retry_text
                print(f"[AI] Retry successful, using longer response ({len(retry_text)} chars)")
            else:
                print(f"[AI] Retry didn't improve length, using original ({len(generated_text)} chars)")
        
        # Final length check - if still too short, try one more time with very aggressive prompt
        if len(generated_text) < 150:
            print(f"[AI] Both attempts failed length check ({len(generated_text)} chars), trying aggressive prompt...")
            
            aggressive_prompt = f"""You must write a comprehensive, detailed essay about: {prompt}

STRICT REQUIREMENTS:
- MINIMUM 400 words required
- Write in multiple detailed paragraphs
- Include specific examples and explanations
- Expand on every point thoroughly
- Never give brief or short answers
- This must be substantial content

Topic: {prompt}

Write a thorough, detailed response that fully covers this topic with examples, explanations, and comprehensive detail."""

            final_response = client.chat.completions.create(
                model='gpt-5-nano',
                messages=[
                    {"role": "system", "content": "You are a detailed writing assistant. ALWAYS write comprehensive, lengthy responses with substantial detail. NEVER write brief answers."},
                    {"role": "user", "content": aggressive_prompt}
                ],
                max_completion_tokens=2000
            )
            
            final_text = final_response.choices[0].message.content.strip()
            if len(final_text) > len(generated_text):
                generated_text = final_text
                print(f"[AI] Aggressive prompt successful ({len(final_text)} chars)")
            
            # If still too short after 3 attempts, log but don't error to user
            if len(generated_text) < 150:
                print(f"[AI] WARNING: All attempts failed, using best result ({len(generated_text)} chars)")
                # Don't return error - let it proceed with whatever we got
        
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
                humanized_text = result.get('data', '')
                
                # Ensure humanized text maintains reasonable length
                original_length = len(text)
                humanized_length = len(humanized_text)
                
                # If humanized text is less than 70% of original, reject it
                if humanized_length < (original_length * 0.7):
                    return jsonify({
                        "success": False,
                        "error": f"Humanized text too short ({humanized_length} chars vs {original_length} original). Please try again."
                    }), 400
                
                return jsonify({
                    "success": True,
                    "humanized_text": humanized_text
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

# ---------------- EDUCATIONAL CONTENT GENERATION ----------------

@app.route('/ai_generate_lesson', methods=['POST'])
def ai_generate_lesson():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    original_question = data.get('original_question', '')
    explanation_style = data.get('explanation_style', 'casual')
    difficulty_level = data.get('difficulty_level', 'intermediate')
    user_id = data.get('user_id')
    
    if not original_question:
        return jsonify({"success": False, "error": "Missing original question"}), 400

    try:
        # Build educational prompt based on style and difficulty
        prompt = _build_educational_prompt(original_question, explanation_style, difficulty_level)
        
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": "You are an expert educational content creator. Generate comprehensive, engaging lessons with step-by-step explanations."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        lesson_content = response.choices[0].message.content.strip()
        
        # Parse the structured response
        lesson_data = _parse_lesson_content(lesson_content, original_question, explanation_style)
        
        return jsonify({
            "success": True,
            "lesson": lesson_data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _build_educational_prompt(question, style, difficulty):
    """Build a specialized prompt for educational content generation"""
    
    style_instructions = {
        'casual': "Explain like you're talking to a friend - use simple language, everyday examples, and a conversational tone.",
        'formal': "Use academic language with proper terminology, structured explanations, and scholarly examples.", 
        'analogy': "Focus heavily on analogies and metaphors to explain complex concepts. Use creative comparisons.",
        'visual': "Structure your explanation with clear bullet points, numbered steps, and visual descriptions."
    }
    
    difficulty_instructions = {
        'beginner': "Assume no prior knowledge. Define all terms and start with basics.",
        'intermediate': "Assume some background knowledge but explain key concepts clearly.",
        'advanced': "Use technical terminology and assume strong foundational knowledge."
    }
    
    prompt_parts = [
        f"Create a comprehensive educational lesson about: {question}",
        "",
        f"EXPLANATION STYLE: {style_instructions.get(style, style_instructions['casual'])}",
        f"DIFFICULTY LEVEL: {difficulty_instructions.get(difficulty, difficulty_instructions['intermediate'])}",
        "",
        "Please structure your response with these sections:",
        "",
        "STEP-BY-STEP EXPLANATION:",
        "Provide a detailed, step-by-step explanation of the topic.",
        "",
        "KEY POINTS:",
        "List 3-5 key takeaways (one per line, starting with '-')",
        "",
        "REAL-WORLD EXAMPLES:",
        "Provide 2-3 practical, real-world examples or applications",
        "",
        "FOLLOW-UP QUESTIONS:", 
        "Suggest 2-3 related questions for deeper exploration",
        "",
        "Make the content engaging, accurate, and educational. Use the specified style and difficulty level throughout."
    ]
    
    return "\n".join(prompt_parts)

def _parse_lesson_content(content, original_question, style):
    """Parse the AI-generated lesson content into structured data"""
    import datetime
    
    # Basic parsing - look for section headers
    sections = {
        'explanation': '',
        'key_points': [],
        'examples': [],
        'follow_up_questions': []
    }
    
    lines = content.split('\n')
    current_section = 'explanation'
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        if 'KEY POINTS:' in line.upper():
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'key_points'
        elif 'REAL-WORLD EXAMPLES:' in line.upper() or 'EXAMPLES:' in line.upper():
            if current_content:
                if current_section == 'key_points':
                    sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
                else:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'examples'
        elif 'FOLLOW-UP QUESTIONS:' in line.upper():
            if current_content:
                if current_section == 'key_points':
                    sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
                elif current_section == 'examples':
                    sections[current_section] = [item.strip() for item in current_content if item.strip()]
                else:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'follow_up_questions'
        else:
            # Add content to current section
            if current_section == 'key_points' and line.startswith('-'):
                current_content.append(line)
            elif current_section in ['examples', 'follow_up_questions']:
                current_content.append(line)
            else:
                current_content.append(line)
    
    # Handle the last section
    if current_content:
        if current_section == 'key_points':
            sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
        elif current_section in ['examples', 'follow_up_questions']:
            sections[current_section] = [item.strip() for item in current_content if item.strip()]
        else:
            sections[current_section] = '\n'.join(current_content).strip()
    
    # Build lesson data structure
    lesson_data = {
        'original_question': original_question,
        'explanation_style': style,
        'explanation': sections['explanation'],
        'key_points': sections['key_points'],
        'examples': sections['examples'],
        'follow_up_questions': sections['follow_up_questions'],
        'timestamp': datetime.datetime.now().isoformat(),
        'marked_for_review': False
    }
    
    return lesson_data

@app.route('/ai_generate_quiz', methods=['POST'])
def ai_generate_quiz():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    lesson_content = data.get('lesson_content', '')
    original_question = data.get('original_question', '')
    quiz_type = data.get('quiz_type', 'multiple_choice')  # multiple_choice, true_false, short_answer
    num_questions = data.get('num_questions', 3)
    user_id = data.get('user_id')
    
    if not lesson_content:
        return jsonify({"success": False, "error": "Missing lesson content"}), 400

    try:
        prompt = _build_quiz_prompt(lesson_content, original_question, quiz_type, num_questions)
        
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": "You are an expert quiz creator. Generate well-crafted questions that test understanding of the provided content."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=1500
        )
        
        quiz_content = response.choices[0].message.content.strip()
        quiz_data = _parse_quiz_content(quiz_content, quiz_type, original_question)
        
        return jsonify({
            "success": True,
            "quiz": quiz_data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _build_quiz_prompt(lesson_content, original_question, quiz_type, num_questions):
    """Build prompt for quiz generation"""
    
    type_instructions = {
        'multiple_choice': f"Create {num_questions} multiple choice questions with 4 options each (A, B, C, D). Mark the correct answer.",
        'true_false': f"Create {num_questions} true/false questions about key concepts.",
        'short_answer': f"Create {num_questions} short answer questions that require 1-2 sentence responses."
    }
    
    prompt_parts = [
        f"Based on this lesson about '{original_question}', create a quiz to test comprehension:",
        "",
        "LESSON CONTENT:",
        lesson_content[:1000],  # Limit content length for prompt
        "",
        f"QUIZ REQUIREMENTS:",
        type_instructions.get(quiz_type, type_instructions['multiple_choice']),
        "",
        "Format your response exactly like this:",
        ""
    ]
    
    if quiz_type == 'multiple_choice':
        prompt_parts.extend([
            "QUESTION 1: [Question text]",
            "A) [Option A]",
            "B) [Option B]", 
            "C) [Option C]",
            "D) [Option D]",
            "CORRECT: [A/B/C/D]",
            "",
            "QUESTION 2: [Question text]",
            "[...continue pattern...]"
        ])
    elif quiz_type == 'true_false':
        prompt_parts.extend([
            "QUESTION 1: [Statement]",
            "CORRECT: [TRUE/FALSE]",
            "",
            "QUESTION 2: [Statement]", 
            "[...continue pattern...]"
        ])
    else:  # short_answer
        prompt_parts.extend([
            "QUESTION 1: [Question text]",
            "ANSWER: [Expected answer]",
            "",
            "QUESTION 2: [Question text]",
            "[...continue pattern...]"
        ])
    
    return "\n".join(prompt_parts)

def _parse_quiz_content(content, quiz_type, original_question):
    """Parse AI-generated quiz content into structured data"""
    import datetime
    
    questions = []
    lines = content.split('\n')
    current_question = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('QUESTION'):
            # Save previous question if exists
            if current_question:
                questions.append(current_question)
            
            # Start new question
            question_text = line.split(':', 1)[1].strip() if ':' in line else line
            current_question = {
                'question': question_text,
                'type': quiz_type
            }
            
            if quiz_type == 'multiple_choice':
                current_question['options'] = []
                
        elif quiz_type == 'multiple_choice' and line.startswith(('A)', 'B)', 'C)', 'D)')):
            if current_question:
                option_text = line[2:].strip()
                current_question['options'].append(option_text)
                
        elif line.startswith('CORRECT:'):
            if current_question:
                correct_answer = line.split(':', 1)[1].strip()
                current_question['correct_answer'] = correct_answer
                
        elif line.startswith('ANSWER:'):
            if current_question:
                answer = line.split(':', 1)[1].strip()
                current_question['expected_answer'] = answer
    
    # Add the last question
    if current_question:
        questions.append(current_question)
    
    quiz_data = {
        'original_question': original_question,
        'quiz_type': quiz_type,
        'questions': questions,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    return quiz_data

# ---------------- MAIN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

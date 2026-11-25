from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os
from pathlib import Path
import pdfplumber

# 1. Load Environment Variables safely
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# Folder to temporarily store uploaded PDFs
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# 2. Setup Groq
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# This holds the text from the uploaded PDF
CURRENT_STUDY_TEXT = ""

SYSTEM_PROMPT = """You are Student Partner, a strict study tutor.

Rules:
1. NEVER give the answer directly. Only ask questions and give small hints.
2. Never repeat the same question after a wrong answer. Give a hint + a new simpler question.
3. Maximum 2 hints per question. Then explain briefly and move on.
4. If the answer sounds memorized, say: "That sounds memorized. Say it in your own words."
5. Keep asking "why?" until the student reaches the basic reason.
6. Keep replies short — max 4 sentences.
7. Be kind but strict.
"""

@app.route("/")
def home():
    return render_template("index.html")

# --- ROUTE: Handle PDF Upload ---
@app.route("/upload", methods=["POST"])
def upload_pdf():
    global CURRENT_STUDY_TEXT
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            extracted_text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            
            if not extracted_text.strip():
                return jsonify({"error": "Could not read text. Is this a scanned image PDF?"}), 400

            # Save text globally (limit to 15,000 chars for Groq limits)
            CURRENT_STUDY_TEXT = extracted_text[:15000] 
            
            return jsonify({"message": f"✅ Successfully read {file.filename}! Ask me a question to start."})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "Only PDF files are allowed"}), 400

# --- ROUTE: Handle Chat ---
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    
    if CURRENT_STUDY_TEXT:
        dynamic_prompt = SYSTEM_PROMPT + f"\n\nIMPORTANT: Here are the student's notes. You must ask questions ONLY based on this text:\n---\n{CURRENT_STUDY_TEXT}\n---"
    else:
        dynamic_prompt = SYSTEM_PROMPT + "\n\n(Note: The student hasn't uploaded notes yet. Tell them to upload a PDF so you can quiz them properly.)"
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b", 
            messages=[
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": user_message}
            ],
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
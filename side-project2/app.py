import os
import base64
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from flask import send_from_directory

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
# Make sure to set your GEMINI_API_KEY in .env or environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def clean_json(text):
    if text.startswith("```json"):
        return text[7:-3].strip()
    elif text.startswith("```"):
        return text[3:-3].strip()
    return text
    
def get_gemini_response(image_data):
    prompt = """
    Analyze this food image and provide nutritional information.
    Return ONLY a JSON object with:
    {
        "name": "Food Name",
        "calories": 250,
        "protein": 10,
        "carbs": 30,
        "fat": 8,
        "health": "Excellent/Good/Fair/Poor",
        "tip": "Short tip"
    }
    """

if "," in image_data:
    image_data = image_data.split(",")[1]

# 🔥 convert to bytes (IMPORTANT)
image_bytes = base64.b64decode(image_data)

image_input = {
    "mime_type": "image/jpeg",
    "data": image_bytes
}

    # 🔁 Try both models safely
    for model_name in [
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash"
    ]:
        try:
            print(f"Trying {model_name}...")

            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image_input])

            if not response or not response.text:
                raise Exception("Empty response")

            text = response.text.strip()

            # clean markdown
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()

            # 🔥 SAFE JSON PARSE
            try:
                return json.loads(text)
            except:
                print("Invalid JSON, raw:", text)

                # fallback safe return
                return {
                    "name": "Detected Food",
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0,
                    "health": "Unknown",
                    "tip": text[:100]
                }

        except Exception as e:
            print(f"{model_name} failed:", e)

    # 🚨 FINAL fallback (never crash)
    return {
        "name": "Server Busy",
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "health": "Unknown",
        "tip": "Try again in a few seconds"
    }

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        result = get_gemini_response(data['image'])
        return jsonify(result)
    except Exception as e:
        print("🔥 CRITICAL ERROR:", e)
        return jsonify({
            "name": "Error",
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "health": "Error",
            "tip": "Something went wrong"
        }), 200   # 👈 important: NOT 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

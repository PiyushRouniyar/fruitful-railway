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
    Return ONLY a JSON object with the following structure:
    {
        "name": "Food Name",
        "calories": 250,
        "protein": 10,
        "carbs": 30,
        "fat": 8,
        "health": "Excellent/Good/Fair/Poor",
        "tip": "A short healthy tip about this meal."
    }
        Be accurate but concise. Do not include any other text or formatting.
    -Foods are mostly nepali,indian and other international food and fruits
    """

    # clean base64
    if "," in image_data:
        image_data = image_data.split(",")[1]

    image_input = {
        "mime_type": "image/jpeg",
        "data": image_data
    }

    # 🥇 TRY MODEL 1 (FAST BUT UNSTABLE)
    try:
        print("Trying 3.1 model...")
        model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

        response = model.generate_content([prompt, image_input])
        text = response.text.strip()

        print("3.1 success")
        return json.loads(clean_json(text))

    except Exception as e:
        print("❌ 3.1 failed:", e)

    # 🥈 FALLBACK MODEL (STABLE)
    try:
        print("Trying 2.5 model...")
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content([prompt, image_input])
        text = response.text.strip()

        print("2.5 success")
        return json.loads(clean_json(text))

    except Exception as e:
        print("❌ 2.5 also failed:", e)

    # 🧯 FINAL FALLBACK
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
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "No image data provided"}), 400
    
    analysis = get_gemini_response(data['image'])
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

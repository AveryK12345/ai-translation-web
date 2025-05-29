from flask import Flask, render_template, request, jsonify
import os
import sys
import io
from contextlib import redirect_stdout

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translate import IntentoTranslator

app = Flask(__name__)

# Read API key from file
with open("../api-development.key", "r") as f:
    api_key = f.read().strip()

translator = IntentoTranslator(api_key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    target_lang = data.get('target_lang', 'es')
    source_lang = data.get('source_lang', 'en')
    use_sync = data.get('use_sync', False)
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Capture the output instead of printing to terminal
        output = io.StringIO()
        with redirect_stdout(output):
            translator.translate([text], target_lang, source_lang, use_sync=use_sync)
        translation_output = output.getvalue()
        
        return jsonify({
            'success': True,
            'output': translation_output
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
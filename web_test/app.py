from flask import Flask, render_template, request, jsonify
import sys
import os
import json

# Add parent directory to Python path to access translate module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translate import Translator

app = Flask(__name__)
translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        text = data.get('text')
        source_lang = data.get('source_lang', '')
        target_lang = data.get('target_lang')
        use_sync = data.get('use_sync', False)
        routing = data.get('routing')
        provider = data.get('provider')

        if not text or not target_lang:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Prepare translation parameters
        params = {
            'text': text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'use_sync': use_sync
        }

        # Add routing or provider if specified
        if routing:
            params['routing'] = routing
        if provider:
            params['provider'] = provider

        # Get translation
        result = translator.translate(**params)
        
        return jsonify({'output': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 
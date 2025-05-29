# AI Translation Web Application

A web-based translation application that uses the Intento API to provide high-quality translations. The application supports both synchronous and asynchronous translation modes, with real-time performance tracking.

## Features

- Web-based translation interface
- Support for multiple languages
- Synchronous and asynchronous translation modes
- Real-time translation duration tracking
- Modern, responsive UI using Tailwind CSS
- Support for various translation providers

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd translate_test
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Add your Intento API key:
   - Create a file named `api-development.key` in the root directory
   - Add your API key to this file

## Running the Application

1. Start the web server:
```bash
cd web_test
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter the text you want to translate
2. Select source and target languages
3. Choose translation mode:
   - Async: Recommended for longer texts
   - Sync: Faster for short texts
4. Click "Translate" to get the translation

## Project Structure

```
translate_test/
├── web_test/
│   ├── app.py              # Flask web application
│   ├── requirements.txt    # Web app dependencies
│   └── templates/
│       └── index.html      # Web interface
├── translate.py            # Core translation functionality
├── requirements.txt        # Main project dependencies
└── README.md              # This file
```

## Dependencies

- Flask
- Requests
- Python 3.6+

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

```bash
# Translate text
python translate.py --text "Hello world" --sync

# List available providers
python translate.py --list-providers

# List supported languages
python translate.py --list-languages

# Translate text asynchronously
python translate.py --text "Hello world" --to es --async #doesn't currently work, working on fix to bug
```

## 2. Local Web Translator

A Flask web application for easy translation through a browser interface.
I just created this for more comprehensive testing of option selection for smart routing integration (colloquial, 
legal, choosing between translation models)

```bash
# Start the web server
python app.py

# Open in browser
http://localhost:5000
```

## 3. Chrome Extension

Browser extension for translating web pages. Very similar intent to Google Translate, but built specifically for Rockwell.
Very rough right now, text is overflowing, more CSS and frontend work to be done.

### Installation
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `chrome_extension` folder

### Usage
1. Click the extension icon in Chrome and pin the extension
2. Click on the extension in top right
3. Select target language
4. Click "Translate Page"
5. check status and logging on console

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API key:
- Create `api-development.key` file with the (currently already all set up)


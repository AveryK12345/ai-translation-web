# AI Translation Tool

A comprehensive translation solution that leverages the Intento API to provide high-quality translations across multiple interfaces. The project includes a command-line interface, web application, and Chrome extension for flexible translation needs.

## Overview

This project provides three main interfaces for translation:

1. **Command Line Interface (CLI)**: For quick translations and API exploration
2. **Web Application**: A user-friendly interface for translation tasks
3. **Chrome Extension**: For translating web pages directly in the browser

## Architecture

### Core Components

- **Translation Engine** (`translate.py`): The core translation service that handles API communication and text processing
- **Web Interface** (`web_test/`): Flask-based web application for browser-based translation
- **Browser Extension** (`chrome_extension/`): Chrome extension for page translation

### API Integration

The project integrates with the Intento API, supporting:
- Multiple translation providers (Google, Microsoft, OpenAI, etc.)
- Smart routing for optimal translation quality
- Both synchronous and asynchronous translation modes
- Language auto-detection
- Custom translation profiles (legal, colloquial, etc.)

## Setup

### Prerequisites

- Python 3.6 or higher
- Chrome browser (for extension)
- Intento API key

### Installation

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

4. Configure API key:
   - Create `api-development.key` in the root directory
   - Add your Intento API key to this file

## Usage

### 1. Command Line Interface

The CLI provides direct access to translation features:

```bash
# Basic translation
python translate.py --text "Hello world" --to es

# Translate a text file
python translate.py --file input.txt --to es

# Translate a file and save to output file
python translate.py --file input.txt --to es --output translated.txt

# List available providers
python translate.py --list-providers

# List supported languages
python translate.py --list-languages

# Use specific provider
python translate.py --text "Hello world" --to es --provider "ai.text.translate.google.translate_api.v3"

# Use smart routing
python translate.py --text "Hello world" --to es --routing "best_colloquial"
```

### 2. Web Application

The web interface provides a user-friendly way to translate text:

1. Start the server:
```bash
cd web_test
python app.py
```

2. Open `http://localhost:5000` in your browser

Features:
- Real-time translation
- Provider selection
- Smart routing profiles
- Translation mode selection (sync/async)
- Performance tracking

### 3. Chrome Extension

For translating web pages directly:

1. Install the extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome_extension` folder

2. Usage:
   - Click the extension icon
   - Select target language
   - Click "Translate Page"

## Advanced Features

### Smart Routing

The system supports intelligent routing to different translation providers based on:
- Content type (legal, technical, colloquial)
- Language pair
- Quality requirements
- Cost considerations

### Translation Modes

1. **Synchronous Mode**:
   - Faster for short texts
   - Immediate response
   - Limited to smaller text sizes

2. **Asynchronous Mode**:
   - Better for longer texts
   - Handles larger content
   - Provides progress tracking

### Error Handling

The system includes comprehensive error handling for:
- API connectivity issues
- Invalid language codes
- Provider unavailability
- Rate limiting
- Text size limitations

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Ensure `api-development.key` exists and contains valid key
   - Check API key permissions

2. **Translation Failures**:
   - Verify text size (use async mode for larger texts)
   - Check language code validity
   - Ensure provider availability

3. **Web Application Issues**:
   - Verify Flask server is running
   - Check port availability
   - Ensure all dependencies are installed

### Debugging

Enable debug mode for detailed logging:
```bash
python translate.py --text "Hello" --to es --trace
```

## Project Structure

```
translate_test/
├── web_test/
│   ├── app.py              # Flask web application
│   ├── requirements.txt    # Web app dependencies
│   └── templates/
│       └── index.html      # Web interface
├── chrome_extension/       # Browser extension
├── translate.py           # Core translation functionality
├── requirements.txt       # Main project dependencies
└── README.md             # Documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License

## Support

For issues and feature requests, please create an issue in the repository.

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


#!/usr/bin/env python3

import argparse
import json
import os
import requests
import sys
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

class Translator:
    """
    A class to handle translation operations using the Intento API.
    Supports both synchronous and asynchronous translation modes,
    multiple providers, and smart routing.
    """

    # ============= Configuration Section =============
    def __init__(self):
        """Initialize the translator with API configuration and endpoints."""
        self.api_key = self._load_api_key()
        self.base_url = "https://api.inten.to/ai/text/translate"
        self.sync_url = "https://syncwrapper.inten.to/ai/text/translate"
        self.headers = self._setup_headers()
        self.default_provider = "ai.text.translate.openai.gpt-4.translate"
        self.default_model = "openai/gpt-4"
        self.default_polling_frequency = 1.0  # Default polling frequency in seconds

    def _load_api_key(self) -> str:
        """Load API key from possible locations."""
        key_paths = [
            "api-development.key",  # Current directory
            "../api-development.key",  # Parent directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-development.key")
        ]
        
        for path in key_paths:
            try:
                with open(path, "r") as f:
                    return f.read().strip()
            except FileNotFoundError:
                continue
        
        raise FileNotFoundError("api-development.key not found in current or parent directory")

    def _setup_headers(self) -> Dict[str, str]:
        """Setup API request headers."""
        return {
            'apikey': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Intento.Integration.WebApp/1.0'
        }

    # ============= Utility Methods Section =============
    def format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.2f}ms"
        return f"{seconds:.2f}s"

    def _prepare_payload(self, text: str, target_lang: str, source_lang: str,
                        use_sync: bool, routing: Optional[str], provider: Optional[str]) -> Dict:
        """Prepare the API request payload."""
        payload = {
            "context": {
                "text": [text],
                "to": target_lang,
                "from": source_lang
            },
            "service": {
                "async": not use_sync,
                "provider": self.default_provider,
                "model": self.default_model
            }
        }

        if routing:
            payload["service"] = {
                "async": not use_sync,
                "routing": routing
            }
        elif provider:
            payload["service"] = {
                "async": not use_sync,
                "provider": provider
            }

        return payload

    # ============= Core Translation Methods Section =============
    def translate(self, text: str, target_lang: str, source_lang: str = '',
                 use_sync: bool = False, routing: Optional[str] = None,
                 provider: Optional[str] = None, polling_frequency: float = None) -> str:
        """
        Core translation method that handles both sync and async translation.
        
        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (optional)
            use_sync: Whether to use synchronous translation
            routing: Smart routing profile to use (optional)
            provider: Specific provider to use (optional)
            polling_frequency: How often to check status for async requests (in seconds)
        """
        start_time = time.time()
        payload = self._prepare_payload(text, target_lang, source_lang, use_sync, routing, provider)
        url = self.sync_url if use_sync else self.base_url

        try:
            result = self._make_translation_request(url, payload, use_sync, polling_frequency)
            translated_text, provider_info = self._extract_translation_result(result, use_sync)
            
            duration = time.time() - start_time
            return self._format_output(translated_text, provider_info, duration)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Translation request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

    def _make_translation_request(self, url: str, payload: Dict, use_sync: bool, polling_frequency: float = None) -> Dict:
        """
        Make the translation request and handle the response.
        
        Args:
            url: The API endpoint URL
            payload: The request payload
            use_sync: Whether to use synchronous translation
            polling_frequency: How often to check status for async requests (in seconds)
        """
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if not use_sync:
            result = self._handle_async_response(result, polling_frequency)

        return result

    def _handle_async_response(self, initial_result: Dict, polling_frequency: float = None) -> Dict:
        """
        Handle asynchronous translation response and polling.
        
        Args:
            initial_result: The initial API response containing the operation ID
            polling_frequency: How often to check the status (in seconds). If None, uses default.
        """
        operation_id = initial_result.get('id')
        if not operation_id:
            raise Exception("No operation ID received")

        # Use provided polling frequency or default
        poll_interval = polling_frequency if polling_frequency is not None else self.default_polling_frequency

        while True:
            status_response = requests.get(
                f"https://api.inten.to/operations/{operation_id}",
                headers=self.headers
            )
            status_response.raise_for_status()
            status = status_response.json()

            if status.get('done'):
                return status

            time.sleep(poll_interval)

    def _extract_translation_result(self, result: Dict, use_sync: bool) -> tuple:
        """Extract translation text and provider info from the response."""
        if use_sync:
            if 'results' in result:
                translated_text = result['results'][0]
                provider_info = result.get('service', {}).get('provider', {})
            else:
                raise Exception("No translation results found in sync response")
        else:
            if 'response' in result and result['response']:
                translation_data = result['response'][0]
                translated_text = translation_data.get('results', [''])[0]
                provider_info = translation_data.get('service', {}).get('provider', {})
            else:
                raise Exception("No translation results found in async response")

        return translated_text, provider_info

    def _format_output(self, translated_text: str, provider_info: Dict, duration: float) -> str:
        """Format the final output string."""
        output = [
            f"Provider: {provider_info.get('name', 'Unknown')} ({provider_info.get('vendor', 'Unknown')})",
            f"Translation: {translated_text}",
            f"Duration: {self.format_duration(duration)}"
        ]
        return '\n'.join(output)

    # ============= File Translation Methods Section =============
    def translate_file(self, file_path: str, target_lang: str, source_lang: str = '',
                      use_sync: bool = False, routing: Optional[str] = None,
                      provider: Optional[str] = None, output_file: Optional[str] = None,
                      polling_frequency: float = None) -> str:
        """
        Translate the contents of a text file.
        
        Args:
            file_path: Path to the input file
            target_lang: Target language code
            source_lang: Source language code (optional)
            use_sync: Whether to use synchronous translation
            routing: Smart routing profile to use (optional)
            provider: Specific provider to use (optional)
            output_file: Path to save the translated text (optional)
            polling_frequency: How often to check status for async requests (in seconds)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            result = self.translate(text, target_lang, source_lang, use_sync, routing, provider, polling_frequency)
            translation = result.split('\n')[1].replace('Translation: ', '')
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(translation)
                return f"Translation saved to {output_file}"
            
            return result
            
        except FileNotFoundError:
            raise Exception(f"Input file not found: {file_path}")
        except Exception as e:
            raise Exception(f"File translation failed: {str(e)}")

# ============= CLI Interface Section =============
def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup the command line argument parser."""
    parser = argparse.ArgumentParser(description="Translation API Client")
    
    # Configuration commands
    parser.add_argument("--list-providers", "-l", action="store_true",
                      help="List available translation providers")
    parser.add_argument("--list-languages", "-L", action="store_true",
                      help="List supported source and target languages")
    parser.add_argument("--list-routing", "-r", action="store_true",
                      help="List available Smart Routing profiles")
    
    # Translation options
    parser.add_argument("--sync", "-s", action="store_true",
                      help="Use synchronous translation (only if < 10,000 tokens)")
    parser.add_argument("--text", "-t", nargs="+",
                      help="Text(s) to translate")
    parser.add_argument("--file", "-f",
                      help="Path to file to translate")
    parser.add_argument("--output", "-o",
                      help="Path to save translated file (only used with --file)")
    parser.add_argument("--to", default="es",
                      help="Target language code (default: es)")
    parser.add_argument("--from", dest="from_lang", default="en",
                      help="Source language code (default: en)")
    parser.add_argument("--routing", default=None,
                      help="Smart Routing profile to use (e.g., 'best', 'best_colloquial')")
    parser.add_argument("--provider", default=None,
                      help="Specific translation provider to use (default: GPT-4)")
    parser.add_argument("--poll-frequency", type=float, default=None,
                      help="How often to check translation status in seconds (default: 1.0)")
    
    return parser

def main():
    """Main entry point for the translation CLI."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    translator = Translator()

    try:
        if args.list_providers:
            translator.list_providers()
        elif args.list_languages:
            translator.list_languages()
        elif args.list_routing:
            translator.list_routing_profiles()
        elif args.file:
            result = translator.translate_file(
                args.file, 
                args.to, 
                args.from_lang, 
                args.sync, 
                args.routing, 
                args.provider,
                args.output,
                args.poll_frequency
            )
            print(result)
        elif args.text:
            translator.translate(args.text, args.to, args.from_lang, args.sync, args.routing, args.provider, args.poll_frequency)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
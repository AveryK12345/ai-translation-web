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
    def __init__(self):
        # Try to find api-development.key in current or parent directory
        key_paths = [
            "api-development.key",  # Current directory
            "../api-development.key",  # Parent directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-development.key")  # Absolute path from parent
        ]
        
        api_key = None
        for path in key_paths:
            try:
                with open(path, "r") as f:
                    api_key = f.read().strip()
                    break
            except FileNotFoundError:
                continue
        
        if not api_key:
            raise FileNotFoundError("api-development.key not found in current or parent directory")
        
        self.api_key = api_key
        self.base_url = "https://api.inten.to/ai/text/translate"
        self.sync_url = "https://syncwrapper.inten.to/ai/text/translate"
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Intento.Integration.WebApp/1.0'
        }
        # Set default provider to GPT-4
        self.default_provider = "ai.text.translate.openai.gpt-4.translate"
        self.default_model = "openai/gpt-4"

    def format_duration(self, seconds):
        """Convert seconds to a human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.2f}ms"
        return f"{seconds:.2f}s"

    def translate(self, text, target_lang, source_lang='', use_sync=False, routing=None, provider=None):
        """
        Translate text using Intento API.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            source_lang (str, optional): Source language code. If empty, auto-detect will be used
            use_sync (bool): Whether to use synchronous translation
            routing (str, optional): Smart routing profile to use
            provider (str, optional): Specific provider to use
        """
        start_time = time.time()

        # Prepare the request payload
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

        # Override with routing or specific provider if specified
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

        # Choose the appropriate endpoint
        url = self.sync_url if use_sync else self.base_url

        try:
            # Make the translation request
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Handle async response
            if not use_sync:
                operation_id = result.get('id')
                if not operation_id:
                    raise Exception("No operation ID received")

                # Poll for results
                while True:
                    status_response = requests.get(
                        f"https://api.inten.to/operations/{operation_id}",
                        headers=self.headers
                    )
                    status_response.raise_for_status()
                    status = status_response.json()

                    if status.get('done'):
                        result = status
                        break

                    time.sleep(1)  # Wait before next poll

            # Extract translation results
            if use_sync:
                # Handle sync response format
                if 'results' in result:
                    translated_text = result['results'][0]
                    provider_info = result.get('service', {}).get('provider', {})
                else:
                    raise Exception("No translation results found in sync response")
            else:
                # Handle async response format
                if 'response' in result and result['response']:
                    translation_data = result['response'][0]
                    translated_text = translation_data.get('results', [''])[0]
                    provider_info = translation_data.get('service', {}).get('provider', {})
                else:
                    raise Exception("No translation results found in async response")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Format output
            output = [
                f"Provider: {provider_info.get('name', 'Unknown')} ({provider_info.get('vendor', 'Unknown')})",
                f"Translation: {translated_text}",
                f"Duration: {self.format_duration(duration)}"
            ]
            
            return '\n'.join(output)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Translation request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Translation API Client")
    parser.add_argument("--list-providers", "-l", action="store_true",
                      help="List available translation providers")
    parser.add_argument("--list-languages", "-L", action="store_true",
                      help="List supported source and target languages")
    parser.add_argument("--list-routing", "-r", action="store_true",
                      help="List available Smart Routing profiles")
    parser.add_argument("--sync", "-s", action="store_true",
                      help="Use synchronous translation (only if < 10,000 tokens)")
    parser.add_argument("--text", "-t", nargs="+",
                      help="Text(s) to translate")
    parser.add_argument("--to", default="es",
                      help="Target language code (default: es)")
    parser.add_argument("--from", dest="from_lang", default="en",
                      help="Source language code (default: en)")
    parser.add_argument("--routing", default=None,
                      help="Smart Routing profile to use (e.g., 'best', 'best_colloquial')")
    parser.add_argument("--provider", default=None,
                      help="Specific translation provider to use (default: GPT-4)")

    args = parser.parse_args()

    translator = Translator()

    if args.list_providers:
        translator.list_providers()
    elif args.list_languages:
        translator.list_languages()
    elif args.list_routing:
        translator.list_routing_profiles()
    elif args.text:
        translator.translate(args.text, args.to, args.from_lang, args.sync, args.routing, args.provider)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import argparse
import json
import os
import requests
import sys
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

class IntentoTranslator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "User-Agent": "Intento.Integration.python/1.0"
        }
        self.base_url = "https://api.inten.to/ai/text/translate"
        self.operations_url = "https://api.inten.to/operations"
        self.routing_url = "https://api.inten.to/routing-designer/"

    def get_operation_url(self, operation_id: str) -> str:
        """Get the correct operations URL for checking status."""
        return f"{self.operations_url}/{operation_id}"

    def list_providers(self) -> None:
        """List available translation providers."""
        response = requests.get(self.base_url, headers=self.headers)
        data = response.json()
        
        print("\nAvailable Translation Providers:")
        print("-------------------------------")
        for provider in data:
            print(f"\nID: {provider.get('id')}")
            print(f"Name: {provider.get('name')}")
            print(f"Vendor: {provider.get('vendor')}")
            if provider.get('description'):
                print(f"Description: {provider.get('description')}")

    def list_languages(self) -> None:
        """List supported source and target languages."""
        response = requests.get(
            f"{self.base_url}/languages",
            headers=self.headers
        )
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    def list_routing_profiles(self) -> None:
        """List available Smart Routing profiles."""
        response = requests.get(self.routing_url, headers=self.headers)
        data = response.json()
        
        print("\nAvailable Smart Routing Profiles:")
        print("--------------------------------")
        for profile in data.get("data", []):
            print(f"\nName: {profile.get('name')}")
            print(f"Description: {profile.get('description')}")
            print(f"Public: {'Yes' if profile.get('is_public') else 'No'}")
            print(f"Active: {'Yes' if profile.get('is_active') else 'No'}")
            if profile.get('rule_groups'):
                print("Rules:")
                for group in profile.get('rule_groups', []):
                    print(f"  - {group.get('description', 'No description')}")

    def estimate_tokens(self, texts: List[str]) -> int:
        """Estimate token count from text array."""
        total_chars = sum(len(text) for text in texts)
        return total_chars // 4

    def format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable format."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        return f"{seconds:.2f}s"

    def translate(self, texts: List[str], target_lang: str = "es", 
                 source_lang: str = "en", use_sync: bool = False,
                 routing: Optional[str] = None,
                 provider: Optional[str] = None) -> None:
        """Translate text using Intento API."""
        start_time = time.time()
        
        payload = {
            "context": {
                "text": texts[0] if len(texts) == 1 else texts,
                "from": source_lang,
                "to": target_lang
            }
        }

        if provider:
            payload["service"] = {
                "provider": provider,
                "async": not use_sync
            }
        elif routing:
            payload["service"] = {
                "routing": routing,
                "async": not use_sync
            }
        else:
            payload["service"] = {
                "provider": "ai.text.translate.openai.gpt-4.translate",
                "model": "openai/gpt-4",
                "async": not use_sync
            }

        estimated_tokens = self.estimate_tokens(texts)

        if use_sync and estimated_tokens >= 10000:
            use_sync = False
            payload["service"]["async"] = True

        url = self.base_url

        response = requests.post(url, headers=self.headers, json=payload)
        response_data = response.json()

        if not response_data:
            print("Error: No response from server.")
            sys.exit(1)

        if "error" in response_data:
            print(f"Error: {response_data['error']}")
            sys.exit(1)

        if "results" in response_data:
            provider_name = response_data.get('meta', {}).get('providers', [{}])[0].get('name', 'Unknown')
            translation = json.dumps(response_data['results'], indent=2, ensure_ascii=False)
            duration = time.time() - start_time
            print(f"Provider: {provider_name}")
            print(f"Translation: {translation}")
            print(f"Duration: {self.format_duration(duration)}")
            return

        if not response_data.get("done", False) and "id" in response_data:
            attempt = 0
            max_attempts = 10
            delay = 1
            
            time.sleep(2)
            
            while attempt < max_attempts:
                time.sleep(delay * (2 ** attempt))
                
                operation_url = self.get_operation_url(response_data['id'])
                result = requests.get(operation_url, headers=self.headers)
                result_data = result.json()

                if "error" in result_data and result_data["error"] is not None:
                    print(f"Error: {result_data['error']}")
                    sys.exit(1)

                if result_data.get("done", False):
                    if "response" in result_data and result_data["response"]:
                        provider_name = result_data.get("meta", {}).get("providers", [{}])[0].get("name", "Unknown")
                        translation = result_data["response"][0].get("results", [])[0]
                        duration = time.time() - start_time
                        print(f"Provider: {provider_name}")
                        print(f"Translation: {translation}")
                        print(f"Duration: {self.format_duration(duration)}")
                        return
                    else:
                        print("Translation completed but no results found")
                        sys.exit(1)

                attempt += 1

            print("Translation timed out")
            sys.exit(1)
        else:
            print("Error: Unexpected response format")
            sys.exit(1)

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

    try:
        with open("api-development.key", "r") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("Error: api-development.key file not found")
        sys.exit(1)

    translator = IntentoTranslator(api_key)

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
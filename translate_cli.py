#!/usr/bin/env python3

import argparse
import json
import os
import sys
from translate import Translator

def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Intento Translation CLI")
    
    # Configuration commands
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument('--list-providers', action='store_true',
                            help='List all available translation providers')
    config_group.add_argument('--list-languages', action='store_true',
                            help='List all supported languages')
    config_group.add_argument('--list-routing', action='store_true',
                            help='List all available Smart Routing profiles')
    config_group.add_argument('--get-routing', metavar='PROFILE',
                            help='Get details of a specific routing profile')
    
    # Translation commands
    translate_group = parser.add_argument_group('Translation')
    translate_group.add_argument('--text', '-t', nargs='+',
                               help='Text(s) to translate')
    translate_group.add_argument('--to', required='--text' in sys.argv,
                               help='Target language code (e.g., es, fr, de)')
    translate_group.add_argument('--from', dest='from_lang',
                               help='Source language code (optional, auto-detect if not specified)')
    translate_group.add_argument('--provider', '-p',
                               help='Specific translation provider to use')
    translate_group.add_argument('--routing', '-r',
                               help='Smart Routing profile to use')
    translate_group.add_argument('--sync', '-s', action='store_true',
                               help='Use synchronous translation (faster for short texts)')
    translate_group.add_argument('--trace', action='store_true',
                               help='Enable trace mode for debugging')
    translate_group.add_argument('--format', choices=['text', 'json'],
                               default='text',
                               help='Output format (default: text)')
    
    # Advanced options
    advanced_group = parser.add_argument_group('Advanced Options')
    advanced_group.add_argument('--glossary', '-g',
                              help='Glossary ID to use for translation')
    advanced_group.add_argument('--category', '-c',
                              help='Content category for better translation')
    advanced_group.add_argument('--timeout', type=int, default=30,
                              help='Timeout in seconds for async operations')
    
    args = parser.parse_args()
    
    try:
        translator = Translator()
        
        # Configuration commands
        if args.list_providers:
            print("\nAvailable Translation Providers:")
            print("-------------------------------")
            response = requests.get(translator.base_url, headers=translator.headers)
            providers = response.json()
            for provider in providers:
                print(f"\nID: {provider.get('id')}")
                print(f"Name: {provider.get('name')}")
                print(f"Vendor: {provider.get('vendor')}")
                if provider.get('description'):
                    print(f"Description: {provider.get('description')}")
            return
            
        if args.list_languages:
            print("\nSupported Languages:")
            print("-------------------")
            response = requests.get(f"{translator.base_url}/languages", 
                                 headers=translator.headers)
            languages = response.json()
            for lang in languages:
                print(f"{lang['intento_code']}: {lang['iso_name']}")
            return
            
        if args.list_routing:
            print("\nAvailable Smart Routing Profiles:")
            print("--------------------------------")
            response = requests.get("https://api.inten.to/routing-designer/",
                                 headers=translator.headers)
            profiles = response.json()
            for profile in profiles.get('data', []):
                print(f"\nName: {profile.get('name')}")
                print(f"Description: {profile.get('description')}")
                print(f"Public: {'Yes' if profile.get('is_public') else 'No'}")
                print(f"Active: {'Yes' if profile.get('is_active') else 'No'}")
            return
            
        if args.get_routing:
            print(f"\nDetails for Routing Profile: {args.get_routing}")
            print("----------------------------------------")
            response = requests.get(f"https://api.inten.to/routing-designer/{args.get_routing}",
                                 headers=translator.headers)
            profile = response.json()
            print_json(profile)
            return
        
        # Translation command
        if args.text:
            if not args.to:
                parser.error("--to is required when translating text")
            
            # Prepare translation parameters
            params = {
                'text': ' '.join(args.text),
                'target_lang': args.to,
                'source_lang': args.from_lang or '',
                'use_sync': args.sync,
                'routing': args.routing,
                'provider': args.provider
            }
            
            # Add optional parameters
            if args.glossary:
                params['glossary'] = args.glossary
            if args.category:
                params['category'] = args.category
            if args.trace:
                params['trace'] = True
            
            # Perform translation
            result = translator.translate(**params)
            
            if args.format == 'json':
                # Parse the result into JSON format
                lines = result.split('\n')
                output = {}
                for line in lines:
                    if line.startswith('Provider:'):
                        output['provider'] = line.replace('Provider: ', '')
                    elif line.startswith('Translation:'):
                        output['translation'] = line.replace('Translation: ', '')
                    elif line.startswith('Duration:'):
                        output['duration'] = line.replace('Duration: ', '')
                print_json(output)
            else:
                print(result)
            return
        
        # If no arguments provided, show help
        if len(sys.argv) == 1:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
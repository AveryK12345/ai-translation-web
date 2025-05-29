#!/bin/sh

key=$(cat api-development.key)
echo "Key: $key"

print_help() {
  cat <<EOF
Usage: $0 [options]

Options:
  --list-providers, -l     List available translation providers
  --list-languages, -L     List supported source and target languages
  --sync, -s               Use synchronous translation (only if < 10,000 tokens)
  --help, -h               Show this help message

Examples:
  $0 --list-providers
  $0 --sync
  $0 --list-languages
EOF
}

# Flags
use_sync=false

# Parse command-line arguments
for arg in "$@"; do
  case $arg in
    --list-providers|-l)
      echo "Fetching list of available providers..."
      curl -s -XGET -H "apikey: $key" https://api.inten.to/ai/text/translate | jq .
      exit 0
      ;;
    --list-languages|-L)
      echo "Fetching list of supported languages..."
      curl -s -H "apikey: $key" \
           -H "User-Agent: Intento.Integration.shell-script/1.0" \
           https://api.inten.to/ai/text/translate/languages | jq .
      exit 0
      ;;
    --sync|-s)
      use_sync=true
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      print_help
      exit 1
      ;;
  esac
done

# Define payload
payload='{
  "context": {
    "text": [
      "Hello my name is AVery",
      "of text to translate"
    ],
    "to": "es",
    "from": "en"
  },
  "service": {
    "provider": "ai.text.translate.openai.gpt-4o.translate"
    }
}'

# Estimate token count from context.text
text_array=$(echo "$payload" | jq -r '.context.text[]')
total_chars=$(echo "$text_array" | wc -m)
estimated_tokens=$((total_chars / 4))

echo "Estimated token count: $estimated_tokens"

if [ "$use_sync" = true ] && [ "$estimated_tokens" -ge 10000 ]; then
  echo "Warning: Translation exceeds 10,000 token limit for synchronous translation."
  echo "Falling back to asynchronous mode..."
  use_sync=false
fi


# Determine URL and payload modifications
if [ "$use_sync" = true ]; then
  echo "Using synchronous translation endpoint..."
  url="https://syncwrapper.inten.to/ai/text/translate"
else
  echo "Using asynchronous translation endpoint..."
  url="https://api.inten.to/ai/text/translate"
  payload=$(echo "$payload" | jq '. + { "async": true }')
fi

# Perform the request
response=$(curl -s -XPOST -H "apikey: $key" "$url" -d "$payload")

# Check for empty response
if [ -z "$response" ]; then
  echo "No response from server."
  exit 1
fi

# Check for error
error=$(echo "$response" | jq -r '.error // empty')
if [ -n "$error" ]; then
  echo "Error in response: $error"
  echo "$response" | jq .
  exit 1
fi

# Check for direct result
has_results=$(echo "$response" | jq -e 'has("results")')

if [ "$has_results" = "true" ]; then
  echo "Translation completed immediately. Result:"
  echo "$response" | jq .
  exit 0
fi

# Check async handling
done=$(echo "$response" | jq -r '.done // "false"')
id=$(echo "$response" | jq -r '.id // empty')

if [ "$done" = "false" ] && [ -n "$id" ]; then
  echo "Translation not ready yet. Fetching result for ID: $id"
  result=$(curl -s -H "apikey: $key" "https://api.inten.to/ai/text/translate/$id")

  error=$(echo "$result" | jq -r '.error // empty')
  if [ -n "$error" ]; then
    echo "Error retrieving async result: $error"
    echo "$result" | jq .
    exit 1
  fi

  echo "Translation result for ID $id:"
  echo "$result" | jq .
else
  echo "Unexpected response format or missing ID:"
  echo "$response" | jq .
  exit 1
fi


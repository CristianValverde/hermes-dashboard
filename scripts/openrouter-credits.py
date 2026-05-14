#!/usr/bin/env python3
"""
openrouter-credits — quick balance check for OpenRouter.
Usage: openrouter-credits [--path AUTH_JSON_PATH] [--key API_KEY]
"""
import json
import sys
import argparse
import requests
import os

DEFAULT_AUTH_PATH = os.path.expanduser("~") + "/AppData/Local/hermes/auth.json"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def get_api_key_from_auth(auth_path):
    """Extract OpenRouter API key from auth.json"""
    try:
        with open(auth_path) as f:
            auth = json.load(f)
    except Exception as e:
        print(f"[ERROR] Cannot read auth.json at {auth_path}: {e}", file=sys.stderr)
        return None
    
    pool = auth.get("credential_pool", {}).get("openrouter", [])
    if not pool:
        print("[ERROR] No 'openrouter' credential pool found", file=sys.stderr)
        return None
    
    for item in pool:
        # Use the first key with access_token
        token = item.get("access_token")
        if token:
            return token
    
    print("[ERROR] No access_token found in openrouter pool", file=sys.stderr)
    return None

def fetch_credits(api_key):
    """GET /credits from OpenRouter API"""
    url = f"{OPENROUTER_BASE}/credits"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            total = data.get("total_credits", 0)
            usage = data.get("total_usage", 0)
            remaining = total - usage
            return {
                "total_credits": total,
                "total_usage": usage,
                "remaining": remaining
            }
        else:
            print(f"[ERROR] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"[ERROR] Request failed: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Check OpenRouter credits")
    parser.add_argument("--path", help=f"Path to auth.json (default: {DEFAULT_AUTH_PATH})",
                        default=DEFAULT_AUTH_PATH)
    parser.add_argument("--key", help="Direct API key (overrides auth.json)")
    args = parser.parse_args()
    
    api_key = args.key
    if not api_key:
        api_key = get_api_key_from_auth(args.path)
        if not api_key:
            sys.exit(1)
    
    result = fetch_credits(api_key)
    if result is None:
        sys.exit(2)
    
    # Output: credits_remaining: X
    # Minimal token usage — just the essential info
    print(f"credits_remaining: {result['remaining']:.2f}")
    
    # Optional: for debugging, show total and usage too (but more tokens)
    # Uncomment if needed:
    # print(f"credits_total: {result['total_credits']:.2f}")
    # print(f"credits_usage: {result['total_usage']:.2f}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Convenient launcher for the GitHub App server.
This script will:
1. Load environment variables from a .env file.
2. Start the FastAPI server using uvicorn.
3. Optionally, use ngrok to create a public URL for the local server.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # Load .env file
    load_dotenv()

    # Check for required environment variables
    required_vars = ["GITHUB_APP_ID", "GITHUB_PRIVATE_KEY", "GITHUB_APP_WEBHOOK_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file (or set them) based on .env.example")
        sys.exit(1)

    # Configuration
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    app_module = "src.webhook:app"

    # --- Ngrok Tunnel ---
    use_ngrok = '--ngrok' in sys.argv

    if use_ngrok:
        try:
            from pyngrok import ngrok
        except ImportError:
            print("❌ pyngrok not installed. Please run: pip install pyngrok")
            sys.exit(1)

        authtoken = os.getenv("NGROK_AUTHTOKEN")
        if authtoken:
            ngrok.set_auth_token(authtoken)

        try:
            public_url = ngrok.connect(port).public_url
            print(f"🚇 ngrok tunnel created: {public_url}")
            print(f"   Webhook URL for GitHub App: {public_url}/app-webhook")
        except Exception as e:
            print(f"❌ Could not start ngrok tunnel: {e}")
            sys.exit(1)

    else:
        print("🚀 Starting PR Review Bot Server (without ngrok)")

    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   App Webhook URL: http://localhost:{port}/app-webhook")
    print(f"   Health Check: http://localhost:{port}/")
    print(f"   Status: http://localhost:{port}/status")
    print("\n" + "="*50)
    print("   To set up your GitHub App:")
    print("   1. Create a GitHub App")
    print("   2. Set 'Webhook URL' to the URL above")
    print("   3. Generate and download a private key")
    print("   4. Set permissions (e.g., Pull requests: Read)")
    print("   5. Fill in .env with App ID, private key, and webhook secret")
    print("   6. Install the App on your repositories")
    print("="*50 + "\n")

    # --- Start Server ---
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            app_module,
            "--host", host,
            "--port", str(port),
            "--reload"
        ]
        print(f"Starting server with command: {' '.join(cmd)}")
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    finally:
        if use_ngrok:
            ngrok.disconnect(public_url)
            print("🔌 ngrok tunnel disconnected")

if __name__ == "__main__":
    main()

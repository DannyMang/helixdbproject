#!/usr/bin/env python3

import uvicorn
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Configuration
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Starting PR Review Bot Webhook Server")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Webhook URL: http://localhost:{port}/webhook")
    print(f"   Health Check: http://localhost:{port}/")
    print(f"   Status: http://localhost:{port}/status")

    # For development, set webhook secret if not already set
    if not os.getenv("GITHUB_WEBHOOK_SECRET"):
        print("\n⚠️  WARNING: No GITHUB_WEBHOOK_SECRET set!")
        print("   For security, set this environment variable:")
        print("   export GITHUB_WEBHOOK_SECRET='your-secret-here'")

    print(f"\n📝 To set up GitHub webhook:")
    print(f"   1. Go to your GitHub repo → Settings → Webhooks")
    print(f"   2. Click 'Add webhook'")
    print(f"   3. Payload URL: http://your-domain.com:{port}/webhook")
    print(f"   4. Content type: application/json")
    print(f"   5. Events: Pull requests")
    print(f"   6. Secret: (set GITHUB_WEBHOOK_SECRET)")
    print(f"\n🔄 Starting server...")

    try:
        uvicorn.run("src.webhook:app", host=host, port=port, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Webhook server stopped")

#!/usr/bin/env python3
"""Convenient launcher for the webhook server"""

import subprocess
import sys
import os

if __name__ == "__main__":
    try:
        subprocess.run([sys.executable, "scripts/start_webhook.py"] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\n👋 Webhook server stopped")
    except FileNotFoundError:
        print("❌ Could not find scripts/start_webhook.py")
        print("   Make sure you're in the project root directory")

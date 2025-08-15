#!/usr/bin/env python3
"""Convenient launcher for the webhook server with ngrok"""

import subprocess
import sys
import os

if __name__ == "__main__":
    try:
        subprocess.run([sys.executable, "scripts/start_with_ngrok.py"] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\n👋 Servers stopped")
    except FileNotFoundError:
        print("❌ Could not find scripts/start_with_ngrok.py")
        print("   Make sure you're in the project root directory")

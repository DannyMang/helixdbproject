#!/usr/bin/env python3

import subprocess
import time
import requests
import json
import signal
import sys
import os

def start_webhook_server():
    """Start the webhook server in the background"""
    return subprocess.Popen([
        "python", "scripts/start_webhook.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_ngrok():
    """Start ngrok tunnel"""
    return subprocess.Popen([
        "ngrok", "http", "8000", "--log=stdout"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_ngrok_url():
    """Get the public ngrok URL"""
    try:
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get ngrok tunnels info
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        
        if tunnels:
            public_url = tunnels[0]["public_url"]
            return public_url
        return None
    except Exception as e:
        print(f"Could not get ngrok URL: {e}")
        return None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n👋 Shutting down servers...')
    # Kill all child processes
    os.system("pkill -f 'python start_webhook.py'")
    os.system("pkill -f 'ngrok'")
    sys.exit(0)

def main():
    print("🚀 Starting PR Review Bot with ngrok tunneling\n")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start webhook server
    print("1️⃣ Starting webhook server on port 8000...")
    webhook_process = start_webhook_server()
    time.sleep(2)  # Give server time to start
    
    # Check if webhook server started successfully
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Webhook server started successfully")
        else:
            print("   ❌ Webhook server not responding properly")
            return
    except requests.exceptions.RequestException:
        print("   ❌ Could not connect to webhook server")
        return
    
    # Start ngrok tunnel
    print("2️⃣ Starting ngrok tunnel...")
    ngrok_process = start_ngrok()
    
    # Get public URL
    print("3️⃣ Getting public URL...")
    public_url = get_ngrok_url()
    
    if public_url:
        webhook_url = f"{public_url}/webhook"
        print(f"\n🎉 SUCCESS! Your webhook is publicly accessible at:")
        print(f"   📡 Public URL: {public_url}")
        print(f"   🔗 Webhook URL: {webhook_url}")
        print(f"   🏠 Local URL: http://localhost:8000")
        
        print(f"\n📋 GitHub Webhook Configuration:")
        print(f"   1. Go to your GitHub repo → Settings → Webhooks")
        print(f"   2. Click 'Add webhook'")
        print(f"   3. Payload URL: {webhook_url}")
        print(f"   4. Content type: application/json")
        print(f"   5. Events: Pull requests")
        print(f"   6. Active: ✅")
        
        if os.getenv("GITHUB_WEBHOOK_SECRET"):
            print(f"   7. Secret: (using GITHUB_WEBHOOK_SECRET from environment)")
        else:
            print(f"   7. Secret: (optional - set GITHUB_WEBHOOK_SECRET if desired)")
            
    else:
        print("   ❌ Could not get ngrok public URL")
        print("   Check ngrok logs or try restarting")
        return
    
    print(f"\n🔄 Both servers are running...")
    print(f"   Press Ctrl+C to stop")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

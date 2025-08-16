#!/usr/bin/env python3

import subprocess
import time
import requests
import json
import signal
import sys
import os

# Ensure Windows consoles can handle Unicode output
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def start_webhook_server():
    """Start the webhook server in the background"""
    return subprocess.Popen([
        sys.executable, "scripts/start_webhook.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_ngrok():
    """Start ngrok tunnel"""
    return subprocess.Popen([
        "ngrok", "http", "8000", "--log=stdout"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_ngrok_url(max_attempts: int = 10, delay_seconds: float = 1.0):
    """Get the public ngrok URL with retries"""
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            response.raise_for_status()
            tunnels = response.json().get("tunnels", [])
            if tunnels:
                return tunnels[0].get("public_url")
        except Exception as e:
            if attempt == 1:
                print("   ⏳ Waiting for ngrok to initialize...")
            time.sleep(delay_seconds)
    return None

webhook_process = None
ngrok_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n👋 Shutting down servers...')
    try:
        if webhook_process and webhook_process.poll() is None:
            webhook_process.terminate()
    except Exception:
        pass
    try:
        if ngrok_process and ngrok_process.poll() is None:
            ngrok_process.terminate()
    except Exception:
        pass
    sys.exit(0)

def main():
    print("🚀 Starting PR Review Bot with ngrok tunneling\n")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start webhook server
    print("1️⃣ Starting webhook server on port 8000...")
    global webhook_process
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
    global ngrok_process
    ngrok_process = start_ngrok()
    # Briefly wait and check if ngrok exited early (e.g., missing authtoken)
    time.sleep(1)
    if ngrok_process.poll() is not None:
        try:
            stdout, stderr = ngrok_process.communicate(timeout=2)
        except Exception:
            stdout, stderr = (b"", b"")
        print("   ❌ ngrok failed to start")
        if stdout:
            print("   --- ngrok stdout ---")
            print(stdout.decode(errors="ignore"))
        if stderr:
            print("   --- ngrok stderr ---")
            print(stderr.decode(errors="ignore"))
        print("\n   Hints:")
        print("   - Ensure ngrok is installed and on your PATH (try: ngrok version)")
        print("   - Ensure your ngrok authtoken is configured (see: https://dashboard.ngrok.com/get-started)")
        print("   - You can set it with: ngrok config add-authtoken <YOUR_TOKEN>")
        return
    
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
        print("   Check ngrok output above, verify authtoken, or try restarting")
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

#!/usr/bin/env python3

import requests
import json

def test_webhook_health():
    """Test if webhook server is running"""
    try:
        response = requests.get("http://localhost:8000/")
        print("✅ Health check:", response.json())
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Webhook server is not running")
        return False

def test_webhook_status():
    """Test webhook status endpoint"""
    try:
        response = requests.get("http://localhost:8000/status")
        print("📊 Status:", json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook server")

def test_ping_event():
    """Test with a GitHub ping event"""
    ping_payload = {
        "zen": "Responsive is better than fast.",
        "hook_id": 12345678,
        "hook": {
            "type": "Repository",
            "id": 12345678,
            "name": "web",
            "active": True,
            "events": ["pull_request"],
            "config": {
                "content_type": "json",
                "insecure_ssl": "0",
                "url": "http://localhost:8000/webhook"
            }
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "full_name": "user/test-repo"
        }
    }
    
    headers = {
        "X-GitHub-Event": "ping",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook",
            json=ping_payload,
            headers=headers
        )
        print("🏓 Ping test:", response.json())
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook server for ping test")

def test_pr_event():
    """Test with a simulated PR event"""
    pr_payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "id": 123456789,
            "number": 1,
            "title": "Test PR for webhook",
            "body": "This is a test PR to verify the webhook works",
            "user": {
                "login": "testuser",
                "id": 12345
            },
            "head": {
                "ref": "feature-branch",
                "sha": "abc123def456"
            },
            "base": {
                "ref": "main",
                "sha": "def456abc123"
            }
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "full_name": "user/test-repo",
            "private": False
        }
    }
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook",
            json=pr_payload,
            headers=headers
        )
        print("🔄 PR test:", response.json())
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook server for PR test")

if __name__ == "__main__":
    print("🧪 Testing Webhook Server\n")
    
    if test_webhook_health():
        test_webhook_status()
        print()
        test_ping_event()
        print()
        test_pr_event()
    else:
        print("\n💡 Start the webhook server first:")
        print("   python start_webhook.py")

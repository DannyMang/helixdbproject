# helixdbproject

A GitHub PR Review Bot that connects via webhooks to analyze pull requests.

## Quick Setup

### 1. Create and Activate Conda Environment
```bash
# Create conda environment with Python 3.11
conda create -n pr-bot python=3.11 -y

# Activate environment
conda activate pr-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Webhook Server
```bash
# Simple way
python run_webhook.py
```

### 3. Start with ngrok (for GitHub integration)
```bash
# Simple way
python run_with_ngrok.py
```


### 4. Configure GitHub Webhook

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks**
3. Click **Add webhook**
4. Configure:
   - **Payload URL**: `http://your-domain.com:8000/webhook`
   - **Content type**: `application/json`
   - **Secret**: Set `GITHUB_WEBHOOK_SECRET` environment variable
   - **Events**: Select "Pull requests"
   - **Active**: ✅ Checked

## Configuration

Create a `.env` file (copy from `.env.example`):
```bash
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here
PORT=8000
```

## Endpoints

- `POST /webhook` - GitHub webhook endpoint
- `GET /` - Health check
- `GET /status` - Status and configuration

## Project Structure

```
helixdbproject/
├── run_webhook.py          # 🚀 Quick launcher for webhook server
├── run_with_ngrok.py       # 🌐 Quick launcher with ngrok tunneling
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
├── scripts/               # Server launch scripts
│   ├── start_webhook.py   # Main webhook server
│   └── start_with_ngrok.py# Server + ngrok tunneling
├── src/                   # Main application code
│   ├── __init__.py        # Package init
│   └── webhook.py         # FastAPI webhook application
├── tests/                 # Test utilities
│   └── test_webhook.py    # Webhook testing tools
├── helixdb-cfg/          # HelixDB configuration
└── docs/                  # Documentation (future)
```

## Development

The webhook server will automatically receive and log PR events:
- PR opened
- PR updated (synchronized)
- PR reopened

## Next Steps

- [ ] Add HelixDB integration
- [ ] Implement code analysis
- [ ] Add PR commenting
- [ ] Deploy to production

- make webhook so PR is submitted then webhook will sent to server
- how do we handle codebase indexing
-

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

This is a template for a GitHub App that reviews pull requests. It can be run locally or deployed to a cloud platform like Heroku.

## Features

- **GitHub App Integration**: Authenticates as a GitHub App for secure and scalable API access.
- **Pull Request Analysis**: (To be implemented) Analyzes PRs for code quality, style, etc.
- **FastAPI Backend**: Built with FastAPI for a high-performance, modern web framework.
- **Easy Deployment**: Includes instructions for running locally and deploying to Heroku.

## How It Works

1.  **Installation**: The GitHub App is installed on a repository.
2.  **Webhook Events**: The app receives webhook events for pull requests.
3.  **Authentication**: It authenticates as the app installation to access the GitHub API.
4.  **Analysis**: (WIP) It fetches PR details and performs analysis.
5.  **Feedback**: (WIP) It posts comments, checks, or reviews on the PR.

## Setup and Running

### 1. Create a GitHub App

First, you need to create a GitHub App under your account or organization.

- Go to **Settings** > **Developer settings** > **GitHub Apps** > **New GitHub App**.
- **GitHub App name**: `Your App Name`
- **Homepage URL**: `https://github.com/your-username/your-repo`
- **Webhook URL**: Use your server's public URL (e.g., from ngrok or Heroku). It should point to `/app-webhook`.
- **Webhook secret**: Generate a strong secret and save it.
- **Permissions**:
    - **Pull requests**: `Read` (or `Read & write` if you want to post comments).
- **Subscribe to events**:
    - `Pull request`
    - `Installation`
- After creating, **generate a private key** and download the `.pem` file.

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```sh
cp .env.example .env
```

Now, edit `.env` and fill in the values:

- `GITHUB_APP_ID`: Your App's ID.
- `GITHUB_PRIVATE_KEY`: The contents of the `.pem` file you downloaded.
- `GITHUB_APP_WEBHOOK_SECRET`: The webhook secret you created.

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Run Locally

Start the server:

```sh
python run_app.py
```

This will start the server on `http://localhost:8000`.

### 5. Use ngrok for a Public URL

To receive webhooks from GitHub, you need a public URL. This project is set up to use `ngrok`.

- Make sure you have `ngrok` installed and configured.
- Run the server with the `--ngrok` flag:

```sh
python run_app.py --ngrok
```

This will create a public URL and print it to the console. Update your GitHub App's Webhook URL with this new ngrok URL.

## Deployment

### Deploy to Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Click the button above to deploy this app to Heroku.

You will need to set the following environment variables in the Heroku app settings:

- `GITHUB_APP_ID`
- `GITHUB_PRIVATE_KEY`
- `GITHUB_APP_WEBHOOK_SECRET`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

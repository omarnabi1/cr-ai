#!/bin/zsh
# CR-AI Setup Script
# Run once to set up the Python environment and install all dependencies
# Usage: chmod +x setup.sh && ./setup.sh

set -e
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CR-AI Project Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "[!] Python 3 not found. Install from python.org"
  exit 1
fi
echo "[✓] Python: $(python3 --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
  echo "[→] Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "[✓] Virtual environment active"

# Upgrade pip
pip install --upgrade pip --quiet

# Install dependencies
echo "[→] Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet
echo "[✓] Dependencies installed"

# Initialize DVC for dataset versioning
if ! dvc status &>/dev/null 2>&1; then
  echo "[→] Initializing DVC..."
  dvc init --no-scm 2>/dev/null || true
fi
echo "[✓] DVC initialized"

# Create .env file for API keys if it doesn't exist
if [ ! -f ".env" ]; then
  cat > .env << 'ENV'
# CR-AI API Keys
# Fill in your credentials and never commit this file to git

TELEGRAM_API_ID=
TELEGRAM_API_HASH=

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=CR-AI-Collector/1.0

TWITTER_BEARER_TOKEN=

WORLD_BANK_API_KEY=
ENV
  echo "[✓] .env file created — add your API keys"
else
  echo "[✓] .env file already exists"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Add API keys to .env"
echo "     - Telegram: https://my.telegram.org/apps"
echo "     - Reddit:   https://www.reddit.com/prefs/apps"
echo "     - Twitter:  https://developer.twitter.com"
echo ""
echo "  2. Activate environment: source .venv/bin/activate"
echo "  3. Run RSS collection:   python scripts/collection/master_collector.py"
echo "  4. Run Telegram:         python scripts/collection/telegram_collector.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

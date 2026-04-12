#!/bin/bash
# ============================================================================
# Google Cloud SDK Setup Guide
# ============================================================================
# This script provides instructions for setting up gcloud CLI
# It does NOT automatically install - just guides you through the process
# ============================================================================

echo "============================================"
echo "Google Cloud SDK Setup Guide"
echo "============================================"
echo ""

# Check if gcloud is already installed
if command -v gcloud &> /dev/null; then
    echo "✓ Google Cloud SDK is already installed"
    echo ""
    echo "Current configuration:"
    gcloud config list --format="text(core.project, core.account)"
    echo ""

    # Check if authenticated
    if gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q "@"; then
        echo "✓ You are authenticated"
    else
        echo "⚠ You need to authenticate"
        echo ""
        echo "Run: gcloud auth login"
    fi

    # Check BigQuery access
    echo ""
    echo "Testing BigQuery access..."
    if bq ls deepdyve-491623:searchconsole &> /dev/null; then
        echo "✓ BigQuery access confirmed"
    else
        echo "⚠ Cannot access BigQuery dataset"
        echo ""
        echo "Run: gcloud config set project deepdyve-491623"
    fi

    exit 0
fi

# Installation instructions
echo "Google Cloud SDK is not installed."
echo ""
echo "============================================"
echo "Installation Instructions"
echo "============================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected"
    echo ""
    echo "Option 1 - Homebrew (recommended):"
    echo "  brew install --cask google-cloud-sdk"
    echo ""
    echo "Option 2 - Manual install:"
    echo "  1. Download: https://cloud.google.com/sdk/docs/install"
    echo "  2. Extract and run: ./google-cloud-sdk/install.sh"
    echo ""
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux detected"
    echo ""
    echo "Debian/Ubuntu:"
    echo "  sudo apt-get install apt-transport-https ca-certificates gnupg"
    echo "  echo 'deb https://packages.cloud.google.com/apt cloud-sdk main' | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list"
    echo "  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -"
    echo "  sudo apt-get update && sudo apt-get install google-cloud-sdk"
    echo ""
    echo "Or download: https://cloud.google.com/sdk/docs/install"
    echo ""
else
    echo "See: https://cloud.google.com/sdk/docs/install"
    echo ""
fi

echo "============================================"
echo "After Installation"
echo "============================================"
echo ""
echo "1. Initialize gcloud:"
echo "   gcloud init"
echo ""
echo "2. Authenticate:"
echo "   gcloud auth login"
echo ""
echo "3. Set project:"
echo "   gcloud config set project deepdyve-491623"
echo ""
echo "4. Test BigQuery access:"
echo "   bq ls deepdyve-491623:searchconsole"
echo ""
echo "5. Deploy views:"
echo "   ./scripts/deploy_views.sh"
echo ""

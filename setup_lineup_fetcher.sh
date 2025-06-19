#!/bin/bash
"""
Setup script for MLB lineup fetcher
Creates virtual environment and installs dependencies
"""

echo "🚀 Setting up MLB Lineup Fetcher..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup completed!"
echo ""
echo "To use the lineup fetcher:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Test the fetcher: python test_lineup_fetcher.py"
echo "3. Run manual fetch: python fetch_starting_lineups.py"
echo "4. Run scheduler: python lineup_scheduler.py"
echo ""
echo "To set up cron job for automatic updates:"
echo "*/15 12-23 * * * cd $(pwd) && ./venv/bin/python lineup_scheduler.py >> lineup_updates.log 2>&1"
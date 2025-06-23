#!/bin/bash

# update-odds.sh - Enhanced MLB HR odds data updater
# Syncs to both development and production directories
# Designed to run every 30 minutes throughout the day
#
# Add to crontab:
# */30 6-23 * * * /path/to/BaseballScraper/update-odds.sh >> /path/to/BaseballScraper/logs/odds-update.log 2>&1

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Log the start time with enhanced formatting
echo "========================================"
echo "$(date): 🎰 Starting odds update..."
echo "$(date): Working directory: $SCRIPT_DIR"

# Check if we're in valid time window (6 AM - 11:30 PM)
CURRENT_HOUR=$(date +%H)
if [ "$CURRENT_HOUR" -lt 6 ] || [ "$CURRENT_HOUR" -gt 23 ]; then
    echo "$(date): 🌙 Outside odds tracking hours (6 AM - 11:30 PM), exiting gracefully"
    exit 0
fi

# Activate virtual environment
echo "$(date): 🐍 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "$(date): ⚠️ No virtual environment found at venv/bin/activate"
fi

# Verify Python environment
PYTHON_VERSION=$(python3 --version 2>&1)
echo "$(date): 🐍 Using Python: $PYTHON_VERSION"

# Download the latest odds data from DraftKings
echo "$(date): 📶 Downloading latest odds data from DraftKings..."
wget --no-check-certificate --timeout=30 --tries=3 -O mlb-batter-hr-props.json "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743?=json"

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "$(date): ✅ Download successful, processing odds..."
    
    # Verify JSON file was downloaded and has content
    if [ -s "mlb-batter-hr-props.json" ]; then
        echo "$(date): 📄 JSON file size: $(wc -c < mlb-batter-hr-props.json) bytes"
        
        # Run the Python script to process the data
        echo "$(date): 🔄 Processing odds data..."
        python3 odds-scrape.py
        
        if [ $? -eq 0 ]; then
            echo "$(date): ✅ Odds update completed successfully"
            
            # Check that output files were created
            PUBLIC_ODDS="../BaseballTracker/public/data/odds/mlb-hr-odds-only.csv"
            BUILD_ODDS="../BaseballTracker/build/data/odds/mlb-hr-odds-only.csv"
            
            if [ -f "$PUBLIC_ODDS" ]; then
                PLAYER_COUNT=$(tail -n +2 "$PUBLIC_ODDS" | wc -l)
                echo "$(date): 📈 Processed $PLAYER_COUNT players in odds data"
            fi
            
            # Archive the JSON file with timestamp for debugging
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            mkdir -p "logs/json_archive"
            cp mlb-batter-hr-props.json "logs/json_archive/mlb-batter-hr-props_$TIMESTAMP.json"
            
            # Clean up current JSON file
            rm mlb-batter-hr-props.json
            
        else
            echo "$(date): ❌ Error processing odds data"
            # Keep JSON file for debugging
            mv mlb-batter-hr-props.json "mlb-batter-hr-props_error_$(date +%Y%m%d_%H%M%S).json"
            deactivate 2>/dev/null
            exit 1
        fi
    else
        echo "$(date): ❌ Downloaded JSON file is empty or missing"
        deactivate 2>/dev/null
        exit 1
    fi
else
    echo "$(date): ❌ Error downloading odds data (wget exit code: $?)"
    deactivate 2>/dev/null
    exit 1
fi

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null
    echo "$(date): 🐍 Virtual environment deactivated"
fi

echo "$(date): ✅ Odds update process finished successfully"
echo "========================================"
echo
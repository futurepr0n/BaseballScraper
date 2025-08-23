#!/bin/bash

# update-odds.sh - Enhanced MLB odds data updater (HR + Hits)
# Downloads and processes both Home Run and 1+ Hits props
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
echo "$(date): 🎰 Starting odds update (HR + Hits props)..."
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
    . venv/bin/activate
else
    echo "$(date): ⚠️ No virtual environment found at venv/bin/activate"
fi

# Verify Python environment (use venv's python after activation)
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "$(date): 🐍 Using venv Python: $PYTHON_VERSION from $VIRTUAL_ENV"
else
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "$(date): ⚠️ Using system Python: $PYTHON_VERSION (venv not activated)"
fi

# Download the latest odds data from DraftKings (both HR and Hits)
echo "$(date): 📶 Downloading latest odds data from DraftKings..."

# Download HR props
echo "$(date): ⚾ Downloading HR props..."
wget --no-check-certificate --timeout=30 --tries=3 -O mlb-batter-hr-props.json "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743?=json"
HR_DOWNLOAD_SUCCESS=$?

# Download Hits props (may use different category)
echo "$(date): 🥎 Downloading Hits props..."
wget --no-check-certificate --timeout=30 --tries=3 -O mlb-batter-hits-props.json "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/17320?=json"
HITS_DOWNLOAD_SUCCESS=$?

# Check if at least one download was successful
if [ $HR_DOWNLOAD_SUCCESS -eq 0 ] || [ $HITS_DOWNLOAD_SUCCESS -eq 0 ]; then
    echo "$(date): ✅ At least one download successful, processing odds..."
    
    # Verify files and show sizes
    if [ -s "mlb-batter-hr-props.json" ]; then
        echo "$(date): ⚾ HR props file size: $(wc -c < mlb-batter-hr-props.json) bytes"
    else
        echo "$(date): ⚠️ HR props file missing or empty"
    fi
    
    if [ -s "mlb-batter-hits-props.json" ]; then
        echo "$(date): 🥎 Hits props file size: $(wc -c < mlb-batter-hits-props.json) bytes"
    else
        echo "$(date): ⚠️ Hits props file missing or empty (may not be available)"
    fi
        
        # Run the enhanced Python script to process the data (use venv's python)
        echo "$(date): 🔄 Processing odds data with enhanced scraper..."
        if [ -n "$VIRTUAL_ENV" ]; then
            python enhanced_odds_scrape.py
        else
            echo "$(date): ⚠️ Warning: venv not activated, using system python3"
            python3 enhanced_odds_scrape.py
        fi
        
        if [ $? -eq 0 ]; then
            echo "$(date): ✅ Odds update completed successfully"
            
            # Check that output files were created in centralized location
            CENTRALIZED_HR_ODDS="../BaseballData/data/odds/mlb-hr-odds-only.csv"
            CENTRALIZED_HITS_ODDS="../BaseballData/data/odds/mlb-hits-odds-only.csv"
            
            if [ -f "$CENTRALIZED_HR_ODDS" ]; then
                HR_PLAYER_COUNT=$(tail -n +2 "$CENTRALIZED_HR_ODDS" | wc -l)
                echo "$(date): ⚾ Processed $HR_PLAYER_COUNT HR players in odds data (centralized)"
            fi
            
            if [ -f "$CENTRALIZED_HITS_ODDS" ]; then
                HITS_PLAYER_COUNT=$(tail -n +2 "$CENTRALIZED_HITS_ODDS" | wc -l)
                echo "$(date): 🥎 Processed $HITS_PLAYER_COUNT Hits players in odds data (centralized)"
            fi
            
            # Archive the JSON files with timestamp for debugging
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            mkdir -p "logs/json_archive"
            
            if [ -f "mlb-batter-hr-props.json" ]; then
                cp mlb-batter-hr-props.json "logs/json_archive/mlb-batter-hr-props_$TIMESTAMP.json"
                rm mlb-batter-hr-props.json
                echo "$(date): 🗃️ Archived HR props file"
            fi
            
            if [ -f "mlb-batter-hits-props.json" ]; then
                cp mlb-batter-hits-props.json "logs/json_archive/mlb-batter-hits-props_$TIMESTAMP.json"
                rm mlb-batter-hits-props.json
                echo "$(date): 🗃️ Archived Hits props file"
            fi
            
        else
            echo "$(date): ❌ Error processing odds data"
            # Keep JSON files for debugging
            ERROR_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            if [ -f "mlb-batter-hr-props.json" ]; then
                mv mlb-batter-hr-props.json "mlb-batter-hr-props_error_$ERROR_TIMESTAMP.json"
            fi
            if [ -f "mlb-batter-hits-props.json" ]; then
                mv mlb-batter-hits-props.json "mlb-batter-hits-props_error_$ERROR_TIMESTAMP.json"
            fi
            deactivate 2>/dev/null
            exit 1
        fi
else
    echo "$(date): ❌ Error downloading odds data"
    echo "$(date): HR download exit code: $HR_DOWNLOAD_SUCCESS"
    echo "$(date): Hits download exit code: $HITS_DOWNLOAD_SUCCESS"
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
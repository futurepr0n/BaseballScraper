#!/bin/bash

# update-odds.sh - Script to update MLB HR odds data
# Add this to your crontab to run every 30 minutes:
# */30 * * * * /app/BaseballScraper/update-odds.sh >> /app/BaseballScraper/odds-update.log 2>&1

# Set the working directory to your project root
cd "/app/BaseballScraper"

# Log the start time
echo "$(date): Starting odds update..."

# Activate virtual environment
echo "$(date): Activating virtual environment..."
source venv/bin/activate

# Check if virtual environment activation was successful
if [ $? -eq 0 ]; then
    echo "$(date): Virtual environment activated successfully"
else
    echo "$(date): Warning: Could not activate virtual environment, proceeding with system Python"
fi

# Download the latest odds data from DraftKings
echo "$(date): Downloading latest odds data..."
wget --no-check-certificate -O mlb-batter-hr-props.json "https://sportsbook-nash.draftkings.com/api/sportscontent/dkcaon/v1/leagues/84240/categories/743?=json"

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "$(date): Download successful, processing odds..."
    
    # Run the Python script to process the data (using venv Python)
    python3 odds-scrape.py
    
    if [ $? -eq 0 ]; then
        echo "$(date): Odds update completed successfully"
        
        # Optional: Clean up the JSON file if you don't want to keep it
        # rm mlb-batter-hr-props.json
        
    else
        echo "$(date): Error processing odds data"
        deactivate 2>/dev/null  # Deactivate venv before exit
        exit 1
    fi
else
    echo "$(date): Error downloading odds data"
    deactivate 2>/dev/null  # Deactivate venv before exit
    exit 1
fi

# Deactivate virtual environment
deactivate 2>/dev/null

echo "$(date): Odds update process finished"
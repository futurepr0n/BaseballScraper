#!/bin/bash

# Odds Update Cron Wrapper Script (HR + Hits)
# Downloads and processes both Home Run and 1+ Hits props
# Ensures proper environment and logging for cron execution

# Set working directory - handle both dev and production environments
if [ -d "/app/BaseballScraper" ]; then
    # Production environment
    cd "/app/BaseballScraper"
else
    # Development environment
    cd "/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballScraper"
fi

# Activate virtual environment (REQUIRED)
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
    echo "$(date): Virtual environment activated: $VIRTUAL_ENV" >> logs/odds_cron.log
else
    echo "$(date): ERROR: No virtual environment found at venv/bin/activate" >> logs/odds_cron.log
    echo "$(date): Please set up venv: python3 -m venv venv && . venv/bin/activate && pip install requirements" >> logs/odds_cron.log
    exit 1
fi

# Run the odds update script
echo "$(date): Starting odds update (HR + Hits props)..." >> logs/odds_cron.log
./update-odds.sh >> logs/odds_cron.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Odds update completed successfully" >> logs/odds_cron.log
else
    echo "$(date): Odds update failed with exit code $EXIT_CODE" >> logs/odds_cron.log
fi

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE

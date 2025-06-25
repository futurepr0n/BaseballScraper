#!/bin/bash

# Hellraiser Analysis Cron Wrapper Script
# Ensures proper environment and logging for cron execution

# Set working directory
cd "/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballScraper"

# Activate virtual environment (REQUIRED)
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
    echo "$(date): Virtual environment activated: $VIRTUAL_ENV" >> logs/hellraiser_cron.log
else
    echo "$(date): ERROR: No virtual environment found at venv/bin/activate" >> logs/hellraiser_cron.log
    echo "$(date): Please set up venv: python3 -m venv venv && . venv/bin/activate && pip install requirements" >> logs/hellraiser_cron.log
    exit 1
fi

# Set Python path for project imports
export PYTHONPATH="$PYTHONPATH:/Users/futurepr0n/Development/Capping.Pro/Claude-Code"

# Run the Hellraiser scheduler (use venv's python)
echo "$(date): Starting Hellraiser scheduler with venv python..." >> logs/hellraiser_cron.log
python daily_hellraiser_scheduler.py >> logs/hellraiser_cron.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Hellraiser scheduler completed successfully" >> logs/hellraiser_cron.log
else
    echo "$(date): Hellraiser scheduler failed with exit code $EXIT_CODE" >> logs/hellraiser_cron.log
fi

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE

#!/bin/bash

# Enhanced Hellraiser Analysis Cron Wrapper Script
# Ensures proper environment, logging, and error handling for automated execution

# Colors for logging (safe for cron)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for timestamped logging
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file and optionally to stdout
    echo "[$timestamp] [$level] $message" >> logs/hellraiser_cron.log
    
    # For interactive runs, also show on stdout
    if [ -t 1 ]; then
        case "$level" in
            "ERROR") echo -e "${RED}[$timestamp] [ERROR]${NC} $message" ;;
            "SUCCESS") echo -e "${GREEN}[$timestamp] [SUCCESS]${NC} $message" ;;
            "WARNING") echo -e "${YELLOW}[$timestamp] [WARNING]${NC} $message" ;;
            *) echo "[$timestamp] [$level] $message" ;;
        esac
    fi
}

# Set working directory - handle both dev and production environments
if [ -d "/app/BaseballScraper" ]; then
    # Production environment
    WORK_DIR="/app/BaseballScraper"
    export PYTHONPATH="$PYTHONPATH:/app"
    log "INFO" "Production environment detected: $WORK_DIR"
else
    # Development environment
    WORK_DIR="/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballScraper"
    export PYTHONPATH="$PYTHONPATH:/Users/futurepr0n/Development/Capping.Pro/Claude-Code"
    log "INFO" "Development environment detected: $WORK_DIR"
fi

# Change to working directory
cd "$WORK_DIR" || {
    log "ERROR" "Failed to change to working directory: $WORK_DIR"
    exit 1
}

# Ensure logs directory exists
mkdir -p logs
if [ $? -ne 0 ]; then
    log "ERROR" "Failed to create logs directory"
    exit 1
fi

log "INFO" "Starting Enhanced Hellraiser Analysis Cron Job"
log "INFO" "Working directory: $(pwd)"
log "INFO" "Python path: $PYTHONPATH"

# Check for virtual environment
if [ -f "venv/bin/activate" ]; then
    # Activate virtual environment
    source venv/bin/activate
    if [ $? -eq 0 ]; then
        log "SUCCESS" "Virtual environment activated: $VIRTUAL_ENV"
        log "INFO" "Python executable: $(which python)"
        log "INFO" "Python version: $(python --version 2>&1)"
    else
        log "ERROR" "Failed to activate virtual environment"
        exit 1
    fi
else
    log "ERROR" "Virtual environment not found at: $(pwd)/venv/bin/activate"
    log "INFO" "To set up venv: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verify the scheduler script exists
if [ ! -f "daily_hellraiser_scheduler.py" ]; then
    log "ERROR" "Scheduler script not found: daily_hellraiser_scheduler.py"
    log "INFO" "Current directory contents:"
    ls -la >> logs/hellraiser_cron.log 2>&1
    exit 1
fi

# Run the Enhanced Hellraiser Scheduler
log "INFO" "Executing Enhanced Hellraiser Scheduler..."
log "INFO" "Command: python daily_hellraiser_scheduler.py"

START_TIME=$(date +%s)
python daily_hellraiser_scheduler.py >> logs/hellraiser_cron.log 2>&1
EXIT_CODE=$?
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))

if [ $EXIT_CODE -eq 0 ]; then
    log "SUCCESS" "Enhanced Hellraiser Scheduler completed successfully in ${EXECUTION_TIME}s"
    
    # Check if analysis files were generated
    if [ -f "../BaseballData/data/hellraiser/hellraiser_analysis_$(date +%Y-%m-%d).json" ]; then
        log "SUCCESS" "Analysis file generated successfully"
    else
        log "WARNING" "Scheduler completed but no analysis file found for today"
    fi
else
    log "ERROR" "Enhanced Hellraiser Scheduler failed with exit code $EXIT_CODE after ${EXECUTION_TIME}s"
    log "ERROR" "Check the log above for detailed error information"
fi

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    log "INFO" "Virtual environment deactivated"
fi

log "INFO" "Enhanced Hellraiser Cron Job completed with exit code $EXIT_CODE"
log "INFO" "============================================================"

exit $EXIT_CODE

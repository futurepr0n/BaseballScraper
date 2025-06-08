#!/bin/bash

# daily-reset.sh - Reset daily odds tracking for fresh start

echo "🌅 Daily Odds Tracking Reset"
echo "============================"

DATA_DIR="/app/BaseballTracker/public/data"

echo "📅 $(date): Starting daily reset..."

# Backup yesterday's data (optional)
if [ "$1" = "backup" ]; then
    BACKUP_DIR="$DATA_DIR/backups/$(date +%Y-%m-%d)"
    mkdir -p "$BACKUP_DIR"
    
    echo "💾 Backing up yesterday's data to $BACKUP_DIR..."
    
    if [ -f "$DATA_DIR/mlb-hr-odds-tracking.csv" ]; then
        cp "$DATA_DIR/mlb-hr-odds-tracking.csv" "$BACKUP_DIR/"
        echo "   ✅ Backed up tracking data"
    fi
    
    if [ -f "$DATA_DIR/mlb-hr-odds-history.csv" ]; then
        cp "$DATA_DIR/mlb-hr-odds-history.csv" "$BACKUP_DIR/"
        echo "   ✅ Backed up history data"
    fi
fi

# Remove tracking files to start fresh
echo "🗑️  Removing daily tracking files..."

if [ -f "$DATA_DIR/mlb-hr-odds-tracking.csv" ]; then
    rm "$DATA_DIR/mlb-hr-odds-tracking.csv"
    echo "   ✅ Removed tracking file"
else
    echo "   ⚠️  Tracking file not found"
fi

if [ -f "$DATA_DIR/mlb-hr-odds-history.csv" ]; then
    rm "$DATA_DIR/mlb-hr-odds-history.csv"
    echo "   ✅ Removed history file"
else
    echo "   ⚠️  History file not found"
fi

# Keep the basic odds file for compatibility
if [ -f "$DATA_DIR/mlb-hr-odds-only.csv" ]; then
    echo "   📋 Keeping basic odds file for compatibility"
else
    echo "   ⚠️  Basic odds file not found"
fi

echo ""
echo "✅ Daily reset complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Run your first odds update: cd /app/BaseballScraper && ./update-odds.sh"
echo "2. This will establish new opening odds for today"
echo "3. Hourly runs will track movement from these opening odds"
echo ""
echo "📊 Today's tracking will show:"
echo "   - Opening odds (first scrape of the day)"
echo "   - Movement between each hourly update"
echo "   - Daily trends (bullish/bearish/stable)"
echo "   - Session high/low ranges"
echo ""

# If run with "auto" parameter, immediately run first odds update
if [ "$1" = "auto" ]; then
    echo "🔄 Running first odds update for the day..."
    cd /app/BaseballScraper
    ./update-odds.sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ First odds update complete - today's tracking has begun!"
        echo "📅 All players now have opening odds established"
        echo "📈 Subsequent runs will show movement arrows and trends"
    else
        echo ""
        echo "❌ First odds update failed - check the logs"
    fi
fi

echo ""
echo "📆 To automate this daily:"
echo "   Add to crontab: 0 8 * * * /app/BaseballScraper/daily-reset.sh auto"
echo "   This runs every day at 8 AM and establishes opening odds"
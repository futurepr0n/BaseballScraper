#!/bin/bash

# daily-reset.sh - Reset daily odds tracking at 6 AM each day
# This clears tracking data but preserves historical logs

echo "🌅 Daily Odds Tracking Reset"
echo "============================"

# Get the script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Define paths - use relative paths for portability
DEV_ODDS_DIR="$BASE_DIR/BaseballTracker/public/data/odds"
PROD_ODDS_DIR="$BASE_DIR/BaseballTracker/build/data/odds"

# Ensure directories exist
mkdir -p "$DEV_ODDS_DIR"
mkdir -p "$PROD_ODDS_DIR"

echo "📅 $(date): Starting daily reset..."
echo "📁 Odds directories:"
echo "   Dev:  $DEV_ODDS_DIR"
echo "   Prod: $PROD_ODDS_DIR"

# Function to reset tracking files in a directory
reset_tracking_files() {
    local odds_dir="$1"
    local env_name="$2"
    
    echo "🗂️  Resetting $env_name tracking files..."
    
    # Archive yesterday's data if it exists
    if [ -f "$odds_dir/mlb-hr-odds-tracking.csv" ]; then
        local yesterday=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date -v-1d +%Y%m%d 2>/dev/null || date +%Y%m%d)
        local archive_dir="$odds_dir/archive"
        mkdir -p "$archive_dir"
        
        echo "   📦 Archiving yesterday's data to archive/"
        cp "$odds_dir/mlb-hr-odds-tracking.csv" "$archive_dir/mlb-hr-odds-tracking-$yesterday.csv" 2>/dev/null
        cp "$odds_dir/mlb-hr-odds-only.csv" "$archive_dir/mlb-hr-odds-only-$yesterday.csv" 2>/dev/null
        
        # Remove old archives (keep last 7 days)
        find "$archive_dir" -name "mlb-hr-odds-*-*.csv" -mtime +7 -delete 2>/dev/null
    fi
    
    # Reset tracking files (but keep history log for movement analysis)
    echo "   🧹 Clearing daily tracking files..."
    rm -f "$odds_dir/mlb-hr-odds-only.csv"
    rm -f "$odds_dir/mlb-hr-odds-tracking.csv"
    
    # Create fresh headers for new day
    echo "player_name,current_odds,team,books_avg,last_updated" > "$odds_dir/mlb-hr-odds-only.csv"
    echo "player_name,previous_odds,current_odds,opening_odds,team,books_avg,session_id,run_number,first_seen,last_updated,movement_direction,movement_amount,session_high,session_low,movement_indicator,daily_range,trend_direction,total_movement,movement_percentage,book_count" > "$odds_dir/mlb-hr-odds-tracking.csv"
    
    echo "   ✅ $env_name reset complete"
}

# Reset both development and production environments
reset_tracking_files "$DEV_ODDS_DIR" "Development"
reset_tracking_files "$PROD_ODDS_DIR" "Production"

# Log the reset
mkdir -p "$SCRIPT_DIR/logs"
echo "🌅 $(date): Daily reset completed successfully" >> "$SCRIPT_DIR/logs/daily-reset.log"

# Clean up old log files (keep last 30 days)
find "$SCRIPT_DIR/logs" -name "daily-reset.log" -mtime +30 -delete 2>/dev/null

# Create movement tracking summary file for dashboard
cat > "$DEV_ODDS_DIR/daily-status.json" << EOF
{
  "last_reset": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "session_date": "$(date +%Y-%m-%d)",
  "status": "reset_complete",
  "next_scrape": "$(date -d '+30 minutes' +%H:%M' 2>/dev/null || date -v+30M +%H:%M)",
  "tracking_active": true,
  "scrape_schedule": "Every 30 minutes from 6:30 AM to 11:30 PM"
}
EOF

# Copy to production
cp "$DEV_ODDS_DIR/daily-status.json" "$PROD_ODDS_DIR/daily-status.json"

echo ""
echo "✅ Daily reset complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Run your first odds update: cd $SCRIPT_DIR && ./daily_odds_scrape.sh"
echo "2. This will establish new opening odds for today"
echo "3. Half-hourly runs will track movement from these opening odds"
echo ""
echo "📊 Today's tracking will show:"
echo "   - Opening odds (first scrape of the day)"
echo "   - Movement between each 30-minute update"
echo "   - Daily trends (bullish/bearish/stable)"
echo "   - Session high/low ranges"
echo "   - Line movement for dashboard analysis"
echo ""

# If run with "auto" parameter, immediately run first odds update
if [ "$1" = "auto" ]; then
    echo "🔄 Running first odds update for the day..."
    cd "$SCRIPT_DIR"
    ./daily_odds_scrape.sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ First odds update complete - today's tracking has begun!"
        echo "📅 All players now have opening odds established"
        echo "📈 Subsequent runs will show movement arrows and trends"
        echo "🎯 Line movement tracking active for dashboard"
    else
        echo ""
        echo "❌ First odds update failed - check the logs"
    fi
fi

echo ""
echo "📆 Automation schedule:"
echo "   6:00 AM: Daily reset (this script)"
echo "   6:30 AM - 11:30 PM: Odds updates every 30 minutes"
echo ""
echo "🚀 Ready for $(date +%Y-%m-%d) tracking!"
#!/bin/bash

# daily_odds_scrape.sh - Wrapper script for odds scraping with movement tracking
# Runs every 30 minutes from 6:30 AM to 11:30 PM

# Get the script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Define paths - use relative paths for portability
DEV_ODDS_DIR="$BASE_DIR/BaseballTracker/public/data/odds"
PROD_ODDS_DIR="$BASE_DIR/BaseballTracker/build/data/odds"

# Ensure directories exist
mkdir -p "$DEV_ODDS_DIR"
mkdir -p "$PROD_ODDS_DIR"
mkdir -p "$SCRIPT_DIR/logs"

# Check if it's within scraping hours (6:30 AM to 11:30 PM)
current_hour=$(date +%H)
current_minute=$(date +%M)
current_time_minutes=$((current_hour * 60 + current_minute))

# 6:30 AM = 390 minutes, 11:30 PM = 1430 minutes
start_time=390  # 6:30 AM
end_time=1430   # 11:30 PM

if [ $current_time_minutes -lt $start_time ] || [ $current_time_minutes -gt $end_time ]; then
    echo "⏰ $(date): Outside scraping hours (6:30 AM - 11:30 PM), skipping..."
    exit 0
fi

echo "📊 $(date): Starting odds scraping (Run #$(date +%s))"
echo "🎯 Target directories:"
echo "   Dev:  $DEV_ODDS_DIR"
echo "   Prod: $PROD_ODDS_DIR"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the odds scraper
echo "🔄 Running daily_odds_scraper.py..."
python3 daily_odds_scraper.py

# Check if the scraper was successful
if [ $? -eq 0 ]; then
    echo "✅ Odds scraper completed successfully"
    
    # Update production files if they exist in dev
    echo "📁 Syncing to production environment..."
    
    # Copy all odds files to production
    if [ -f "$DEV_ODDS_DIR/mlb-hr-odds-only.csv" ]; then
        cp "$DEV_ODDS_DIR/mlb-hr-odds-only.csv" "$PROD_ODDS_DIR/"
        echo "   ✅ Synced basic odds file"
    fi
    
    if [ -f "$DEV_ODDS_DIR/mlb-hr-odds-tracking.csv" ]; then
        cp "$DEV_ODDS_DIR/mlb-hr-odds-tracking.csv" "$PROD_ODDS_DIR/"
        echo "   ✅ Synced tracking file"
    fi
    
    if [ -f "$DEV_ODDS_DIR/mlb-hr-odds-history.csv" ]; then
        cp "$DEV_ODDS_DIR/mlb-hr-odds-history.csv" "$PROD_ODDS_DIR/"
        echo "   ✅ Synced history file"
    fi
    
    # Update daily status for dashboard
    cat > "$DEV_ODDS_DIR/daily-status.json" << EOF
{
  "last_update": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "session_date": "$(date +%Y-%m-%d)",
  "status": "active",
  "next_scrape": "$(date -d '+30 minutes' +%H:%M' 2>/dev/null || date -v+30M +%H:%M)",
  "tracking_active": true,
  "scrape_count": $(grep -c "," "$DEV_ODDS_DIR/mlb-hr-odds-only.csv" 2>/dev/null || echo "0"),
  "total_players": $(tail -n +2 "$DEV_ODDS_DIR/mlb-hr-odds-only.csv" 2>/dev/null | wc -l || echo "0")
}
EOF
    
    # Copy status to production
    cp "$DEV_ODDS_DIR/daily-status.json" "$PROD_ODDS_DIR/"
    
    # Generate movement summary for dashboard
    if [ -f "$DEV_ODDS_DIR/mlb-hr-odds-tracking.csv" ]; then
        echo "📈 Generating movement summary for dashboard..."
        
        # Create movement summary (top movers for dashboard card)
        python3 -c "
import csv
import json
from collections import defaultdict
import sys

try:
    movements = []
    with open('$DEV_ODDS_DIR/mlb-hr-odds-tracking.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('movement_percentage') and row.get('movement_percentage') != '':
                try:
                    movement_pct = float(row['movement_percentage'])
                    if abs(movement_pct) >= 5:  # Only significant movements
                        movements.append({
                            'player': row['player_name'],
                            'team': row['team'],
                            'current_odds': row['current_odds'],
                            'opening_odds': row['opening_odds'],
                            'movement_percentage': movement_pct,
                            'direction': 'up' if movement_pct > 0 else 'down',
                            'trend': row.get('trend_direction', 'stable')
                        })
                except ValueError:
                    continue
    
    # Sort by absolute movement percentage
    movements.sort(key=lambda x: abs(x['movement_percentage']), reverse=True)
    
    # Take top 10 movers
    top_movers = movements[:10]
    
    summary = {
        'top_movers': top_movers,
        'total_significant_moves': len(movements),
        'last_updated': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
        'session_date': '$(date +%Y-%m-%d)'
    }
    
    with open('$DEV_ODDS_DIR/movement-summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f'✅ Movement summary generated: {len(top_movers)} top movers')
    
except Exception as e:
    print(f'⚠️ Error generating movement summary: {e}')
"
        
        # Copy movement summary to production
        if [ -f "$DEV_ODDS_DIR/movement-summary.json" ]; then
            cp "$DEV_ODDS_DIR/movement-summary.json" "$PROD_ODDS_DIR/"
            echo "   ✅ Movement summary synced to production"
        fi
    fi
    
    # Log success
    echo "📊 $(date): Odds scraping completed successfully" >> "$SCRIPT_DIR/logs/odds-scraper.log"
    
    echo ""
    echo "🎯 Next scrape scheduled for: $(date -d '+30 minutes' +%H:%M' 2>/dev/null || date -v+30M +%H:%M)"
    
else
    echo "❌ Odds scraper failed - check the logs"
    echo "❌ $(date): Odds scraping failed" >> "$SCRIPT_DIR/logs/odds-scraper.log"
    exit 1
fi

# Clean up old logs (keep last 7 days)
find "$SCRIPT_DIR/logs" -name "odds-scraper.log" -mtime +7 -delete 2>/dev/null

echo "✅ Odds scraping session complete"
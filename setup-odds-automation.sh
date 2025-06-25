#!/bin/bash

# setup-odds-automation.sh - Set up automated odds tracking with cron jobs

echo "🚀 MLB Odds Tracking Automation Setup"
echo "====================================="

# Get the script directory for absolute paths in cron
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Script directory: $SCRIPT_DIR"
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR/daily-reset.sh"
chmod +x "$SCRIPT_DIR/daily_odds_scrape.sh"

echo "🔐 Made scripts executable"

# Create the cron job entries
CRON_TEMP=$(mktemp)

# Get current crontab (if any)
crontab -l 2>/dev/null > "$CRON_TEMP"

# Remove any existing MLB odds tracking entries
sed -i.bak '/# MLB Odds Tracking/d' "$CRON_TEMP"
sed -i.bak '/daily-reset.sh/d' "$CRON_TEMP"
sed -i.bak '/daily_odds_scrape.sh/d' "$CRON_TEMP"

echo "" >> "$CRON_TEMP"
echo "# MLB Odds Tracking - Daily Reset and Scraping" >> "$CRON_TEMP"
echo "# Daily reset at 6:00 AM (clears tracking, establishes new opening odds)" >> "$CRON_TEMP"
echo "0 6 * * * $SCRIPT_DIR/daily-reset.sh auto >> $SCRIPT_DIR/logs/cron-daily-reset.log 2>&1" >> "$CRON_TEMP"
echo "" >> "$CRON_TEMP"
echo "# Odds scraping every 30 minutes from 6:30 AM to 11:30 PM" >> "$CRON_TEMP"
echo "30 6-23 * * * $SCRIPT_DIR/daily_odds_scrape.sh >> $SCRIPT_DIR/logs/cron-odds-scrape.log 2>&1" >> "$CRON_TEMP"
echo "0 7-23 * * * $SCRIPT_DIR/daily_odds_scrape.sh >> $SCRIPT_DIR/logs/cron-odds-scrape.log 2>&1" >> "$CRON_TEMP"

# Show the user what will be added
echo "📅 Cron jobs to be added:"
echo ""
echo "┌─────────────────────────────────────────────────────────────────────┐"
echo "│ Daily Reset (6:00 AM):                                             │"
echo "│ 0 6 * * * $SCRIPT_DIR/daily-reset.sh auto                     │"
echo "│                                                                     │"
echo "│ Odds Scraping (Every 30 minutes, 6:30 AM - 11:30 PM):             │"
echo "│ 30 6-23 * * * $SCRIPT_DIR/daily_odds_scrape.sh                │"
echo "│ 0 7-23 * * * $SCRIPT_DIR/daily_odds_scrape.sh                 │"
echo "└─────────────────────────────────────────────────────────────────────┘"
echo ""

# Ask for confirmation
read -p "🤔 Do you want to install these cron jobs? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install the cron jobs
    crontab "$CRON_TEMP"
    
    if [ $? -eq 0 ]; then
        echo "✅ Cron jobs installed successfully!"
        echo ""
        echo "📊 Schedule Summary:"
        echo "   🌅 6:00 AM:     Daily reset (clears tracking, starts fresh)"
        echo "   🕕 6:30 AM:     First odds scrape (establishes opening odds)"
        echo "   🕐 7:00 AM:     Second scrape (tracks first movement)"
        echo "   ⏰ Every 30min: Continued tracking until 11:30 PM"
        echo ""
        echo "📁 Log files will be created in:"
        echo "   Daily reset: $SCRIPT_DIR/logs/cron-daily-reset.log"
        echo "   Odds scraping: $SCRIPT_DIR/logs/cron-odds-scrape.log"
        echo ""
        
        # Create logs directory
        mkdir -p "$SCRIPT_DIR/logs"
        
        # Show current crontab
        echo "📋 Current crontab:"
        crontab -l | grep -A 10 -B 2 "MLB Odds"
        
    else
        echo "❌ Failed to install cron jobs"
        exit 1
    fi
else
    echo "⏭️  Cron job installation skipped"
    echo ""
    echo "📝 To install manually later, add these lines to your crontab:"
    echo "   crontab -e"
    echo ""
    cat "$CRON_TEMP" | grep -A 10 "MLB Odds"
fi

# Clean up
rm -f "$CRON_TEMP" "$CRON_TEMP.bak"

echo ""
echo "🧪 Testing Scripts:"
echo "─────────────────"

# Test daily reset script
echo "🔍 Testing daily-reset.sh..."
if "$SCRIPT_DIR/daily-reset.sh" test; then
    echo "   ✅ Daily reset script works"
else
    echo "   ⚠️  Daily reset script may have issues"
fi

# Test odds scrape script
echo "🔍 Testing daily_odds_scrape.sh..."
if "$SCRIPT_DIR/daily_odds_scrape.sh" | head -10; then
    echo "   ✅ Odds scrape script started (may skip due to time restrictions)"
else
    echo "   ⚠️  Odds scrape script may have issues"
fi

echo ""
echo "📊 Dashboard Integration:"
echo "────────────────────────"
echo "The automation creates these files for dashboard cards:"
echo "   📄 daily-status.json     - Current scraping status"
echo "   📈 movement-summary.json - Top line movers for dashboard"
echo "   📋 mlb-hr-odds-*.csv    - Odds data files"
echo ""
echo "Files are updated in both:"
echo "   🔧 Development: ../BaseballTracker/public/data/odds/"
echo "   🚀 Production:  ../BaseballTracker/build/data/odds/"
echo ""

echo "🎯 Next Steps:"
echo "─────────────"
echo "1. 📅 Wait for 6:00 AM tomorrow for the first automated reset"
echo "2. 🔍 Monitor logs in $SCRIPT_DIR/logs/"
echo "3. 📊 Check dashboard for odds movement cards"
echo "4. 🔧 Adjust timing if needed with: crontab -e"
echo ""

echo "📞 Manual Commands:"
echo "   🌅 Run daily reset now:  $SCRIPT_DIR/daily-reset.sh auto"
echo "   📊 Run odds scrape now:  $SCRIPT_DIR/daily_odds_scrape.sh"
echo "   📋 View cron jobs:       crontab -l"
echo "   📄 View logs:            tail -f $SCRIPT_DIR/logs/*.log"
echo ""

echo "✅ MLB Odds Tracking Automation Setup Complete!"
echo "🚀 Your system will now automatically track line movement throughout each day!"
#!/bin/bash

# setup-movement-tracking.sh - Setup and test comprehensive daily odds tracking

echo "📈 MLB Daily Odds Tracking Setup"
echo "================================"

cd /app/BaseballScraper

echo "🔄 Starting comprehensive daily tracking system..."
echo ""
echo "How this system works:"
echo "  📊 OPENING ODDS: First time player seen today (never changes)"
echo "  📈 PREVIOUS ODDS: From last scrape (updates each run)"  
echo "  💰 CURRENT ODDS: This scrape's odds"
echo "  🎯 MOVEMENT: Previous → Current (what you see as arrows)"
echo "  📊 TREND: Opening → Current (overall day direction)"
echo ""

echo "1. 🌅 First run of the day (establishes opening odds)..."
./update-odds.sh

if [ $? -eq 0 ]; then
    echo "   ✅ Opening odds established"
    
    echo ""
    echo "2. 📊 Checking created files..."
    
    if [ -f "/app/BaseballTracker/public/data/mlb-hr-odds-only.csv" ]; then
        echo "   ✅ Basic odds file: $(wc -l < /app/BaseballTracker/public/data/mlb-hr-odds-only.csv) lines"
    fi
    
    if [ -f "/app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv" ]; then
        echo "   ✅ Tracking file: $(wc -l < /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv) lines"
        echo ""
        echo "   📋 Sample tracking data:"
        head -3 /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv
        echo ""
        echo "   🔍 Players with multiple runs:"
        awk -F, '$8 > 1 {print $1 ": Run #" $8 " (" $4 " → " $5 ")"}' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | head -5
    else
        echo "   ⚠️  Tracking file not created yet"
    fi
    
    if [ -f "/app/BaseballTracker/public/data/mlb-hr-odds-history.csv" ]; then
        echo "   ✅ History file: $(wc -l < /app/BaseballTracker/public/data/mlb-hr-odds-history.csv) lines"
    fi
    
    echo ""
    echo "3. ⏰ Testing daily progression..."
    echo "   💡 Run the script multiple times to see the tracking:"
    echo ""
    echo "   First run:  All players show opening odds (no arrows)"
    echo "   Second run: Movement arrows appear (↗ ↘ →)"
    echo "   Third run:  Tracks previous → current movement"
    echo "   Fourth run: Shows daily trends (📈 📉 📊)"
    echo ""
    
    echo "4. 🎯 Expected progression example:"
    echo "   Run 1: Player opens at +500 (no movement)"
    echo "   Run 2: Player at +450 ↘ (worse odds)"  
    echo "   Run 3: Player at +475 ↗ (better than last)"
    echo "   Run 4: Player at +480 ↗ 📉 (up from last, down from opening)"
    echo ""
    
    echo "5. 🧪 Visual indicators explained:"
    echo "   ↗ Green:  Odds longer than previous scrape (better)"
    echo "   ↘ Red:    Odds shorter than previous scrape (worse)"
    echo "   → Gray:   Minimal movement since previous scrape" 
    echo "   📈 Green: Trending up from opening (bullish)"
    echo "   📉 Red:   Trending down from opening (bearish)"
    echo "   📊 Gray:  Stable trend from opening"
    echo ""
    
    echo "6. 🔍 What you'll see in the app:"
    echo "   Matt Mervis"
    echo "   MIA • +950 ↗ 📉   ← Current odds, movement, trend"
    echo "   16 games since HR"
    echo "   Opening: +900 • Range: +900-+975  ← Daily context"
    echo ""
    
    echo "7. 🗂️ File structure:"
    echo "   mlb-hr-odds-only.csv     - Simple current odds (compatibility)"
    echo "   mlb-hr-odds-tracking.csv - Comprehensive tracking data"
    echo "   mlb-hr-odds-history.csv  - Complete chronological log"
    echo ""
    
    echo "8. 🔄 Daily reset process:"
    echo "   You mentioned manually deleting files daily"
    echo "   Delete these files to start fresh:"
    echo "   rm /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv"
    echo "   rm /app/BaseballTracker/public/data/mlb-hr-odds-history.csv"
    echo "   (Keep mlb-hr-odds-only.csv for compatibility)"
    echo ""
    
    echo "✅ Setup complete! Daily tracking system is now active."
    
else
    echo "❌ Initial setup failed. Check the logs."
    exit 1
fi

# If run with "simulate" parameter, run multiple times to show progression
if [ "$1" = "simulate" ]; then
    echo ""
    echo "🎬 Simulation Mode: Testing daily progression..."
    
    for i in {2..4}; do
        echo ""
        echo "📊 Simulating run #$i (waiting 30 seconds for potential changes)..."
        sleep 30
        
        echo "   Running odds update #$i..."
        ./update-odds.sh
        
        if [ -f "/app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv" ]; then
            echo "   📈 Movement summary for run #$i:"
            
            # Count movements
            UP=$(awk -F, '$11 == "UP"' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | wc -l)
            DOWN=$(awk -F, '$11 == "DOWN"' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | wc -l)
            STABLE=$(awk -F, '$11 == "STABLE"' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | wc -l)
            
            echo "   ↗ UP: $UP players"
            echo "   ↘ DOWN: $DOWN players"  
            echo "   → STABLE: $STABLE players"
            
            # Show trend directions
            BULLISH=$(awk -F, '$17 == "bullish"' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | wc -l)
            BEARISH=$(awk -F, '$17 == "bearish"' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | wc -l)
            
            if [ $BULLISH -gt 0 ] || [ $BEARISH -gt 0 ]; then
                echo "   📈 Daily trends: $BULLISH bullish, $BEARISH bearish"
            fi
            
            # Show sample player with movement
            echo "   📋 Sample tracking:"
            awk -F, '$8 > 1 {print "   " $1 ": " $2 " → " $3 " (" $15 ")"}' /app/BaseballTracker/public/data/mlb-hr-odds-tracking.csv | head -3
        fi
    done
    
    echo ""
    echo "🚀 Simulation complete! Refresh your React app to see:"
    echo "   - Movement arrows next to current odds"
    echo "   - Trend indicators for daily direction"  
    echo "   - Opening odds and session ranges in details"
    echo ""
    echo "🎯 Your hourly cron job will now track all changes throughout the day!"
fi

echo ""
echo "📅 Remember: This system tracks the full day's progression."
echo "   Each hourly run adds to the story of how odds moved."
echo "   Delete tracking files at start of each day for fresh tracking."
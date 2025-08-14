#!/bin/bash

# Cleanup and Re-run Tool for Play-by-Play Testing
# Allows complete cleanup of a date's data and fresh re-run

DATE_PATTERN=""
TARGET_DATE=""
CLEANUP_ONLY=false
DRY_RUN=false

show_usage() {
    echo "🧹 Cleanup and Re-run Tool"
    echo "=========================="
    echo ""
    echo "Usage: $0 [OPTIONS] <date>"
    echo ""
    echo "Options:"
    echo "  --cleanup-only     Only cleanup, don't re-run"
    echo "  --dry-run         Show what would be done without doing it"
    echo "  --help            Show this help message"
    echo ""
    echo "Date format: YYYY-MM-DD (e.g., 2025-08-13)"
    echo ""
    echo "Examples:"
    echo "  $0 2025-08-13                    # Cleanup and re-run for August 13"
    echo "  $0 --cleanup-only 2025-08-13    # Only cleanup August 13 data"
    echo "  $0 --dry-run 2025-08-13         # Show what would be cleaned"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cleanup-only)
            CLEANUP_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        -*)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$TARGET_DATE" ]; then
                TARGET_DATE="$1"
            else
                echo "❌ Multiple dates provided. Only one date allowed."
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$TARGET_DATE" ]; then
    echo "❌ No date provided"
    show_usage
    exit 1
fi

# Validate date format
if ! echo "$TARGET_DATE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    echo "❌ Invalid date format. Use YYYY-MM-DD"
    exit 1
fi

# Convert date to filename format
DATE_PATTERN=$(echo $TARGET_DATE | awk -F'-' '{
    months["01"]="january"; months["02"]="february"; months["03"]="march"; 
    months["04"]="april"; months["05"]="may"; months["06"]="june";
    months["07"]="july"; months["08"]="august"; months["09"]="september";
    months["10"]="october"; months["11"]="november"; months["12"]="december";
    day = $3 + 0;  # Remove leading zero
    print months[$2] "_" day "_" $1
}')

echo "🧹 Cleanup and Re-run Tool"
echo "=========================="
echo "📅 Target Date: $TARGET_DATE"
echo "📂 File Pattern: $DATE_PATTERN"

if [ "$DRY_RUN" = true ]; then
    echo "🧪 DRY RUN MODE - No files will be modified"
fi

echo ""

# Function to execute or show command
run_command() {
    local cmd="$1"
    local description="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo "   [DRY RUN] $description"
        echo "   Command: $cmd"
    else
        echo "   $description"
        eval "$cmd"
        if [ $? -eq 0 ]; then
            echo "   ✅ Done"
        else
            echo "   ⚠️ Command returned non-zero status"
        fi
    fi
}

# Cleanup Process
echo "🗑️ Cleanup Phase"
echo "=================="

# 1. CSV files in main directory
echo "1. Removing CSV files from main directory..."
run_command "rm -f *_hitting_${DATE_PATTERN}_*.csv *_pitching_${DATE_PATTERN}_*.csv" "Remove local CSV files"

# 2. CSV files in centralized backup
echo ""
echo "2. Removing CSV files from centralized backup..."
run_command "rm -f ../BaseballData/CSV_BACKUPS/*${DATE_PATTERN}*" "Remove centralized CSV backup files"

# 3. Play-by-play JSON files
echo ""
echo "3. Removing play-by-play JSON files..."
run_command "rm -f *_playbyplay_${DATE_PATTERN}_*.json" "Remove play-by-play JSON files"

# 4. Processed JSON data
echo ""
echo "4. Removing processed JSON data..."
JSON_PATH="../BaseballData/data/2025/$(echo $DATE_PATTERN | cut -d'_' -f1)/${DATE_PATTERN}.json"
run_command "rm -f \"$JSON_PATH\"" "Remove processed game data JSON"

# 5. Schedule file restoration
echo ""
echo "5. Checking schedule file status..."
MAIN_SCHEDULE="${DATE_PATTERN}.txt"
SCANNED_SCHEDULE="../BaseballData/SCANNED/${DATE_PATTERN}.txt"

if [ -f "$SCANNED_SCHEDULE" ] && [ ! -f "$MAIN_SCHEDULE" ]; then
    run_command "cp \"$SCANNED_SCHEDULE\" \"$MAIN_SCHEDULE\"" "Restore schedule file from SCANNED"
elif [ -f "$MAIN_SCHEDULE" ]; then
    echo "   ✅ Schedule file already in main directory"
elif [ "$DRY_RUN" = true ]; then
    echo "   [DRY RUN] Would check for schedule file restoration"
else
    echo "   ⚠️ No schedule file found in either location"
fi

# 6. Log files
echo ""
echo "6. Removing related log files..."
run_command "rm -f logs/*${DATE_PATTERN}*.log" "Remove date-specific logs"
run_command "rm -f logs/enhanced_daily_automation_*.log" "Remove automation logs"
run_command "rm -f logs/playbyplay_scrape.log" "Remove play-by-play logs"

echo ""
echo "✅ Cleanup phase completed"

# Summary of what was cleaned
if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "📊 Cleanup Summary"
    echo "=================="
    echo "🗃️ Files that would be cleaned:"
    echo "   - CSV files: *_hitting/pitching_${DATE_PATTERN}_*.csv"
    echo "   - Centralized CSVs: ../BaseballData/CSV_BACKUPS/*${DATE_PATTERN}*"
    echo "   - Play-by-play: *_playbyplay_${DATE_PATTERN}_*.json"
    echo "   - JSON data: $JSON_PATH"
    echo "   - Log files: logs/*${DATE_PATTERN}*.log"
fi

# Re-run Phase
if [ "$CLEANUP_ONLY" = false ]; then
    echo ""
    echo "🔄 Re-run Phase"
    echo "==============="
    
    if [ "$DRY_RUN" = true ]; then
        echo "🧪 DRY RUN - Would execute:"
        echo "   1. Enhanced daily automation for $TARGET_DATE"
        echo "   2. Play-by-play automation for $TARGET_DATE"
        echo ""
        echo "Commands that would run:"
        echo "   ./enhanced_daily_automation.sh --test-mode --target-date $TARGET_DATE"
        echo "   python daily_playbyplay_automation.py --date $TARGET_DATE"
    else
        echo "🎯 Running complete automation for $TARGET_DATE..."
        echo ""
        
        # Check if enhanced_daily_automation.sh exists in root directory
        if [ -f "../enhanced_daily_automation.sh" ]; then
            echo "⚙️ Running enhanced daily automation..."
            cd ..
            ./enhanced_daily_automation.sh --test-mode --target-date "$TARGET_DATE"
            automation_status=$?
            cd BaseballScraper
            
            if [ $automation_status -eq 0 ]; then
                echo "✅ Enhanced daily automation completed successfully"
            else
                echo "⚠️ Enhanced daily automation returned status: $automation_status"
                echo "💡 You may want to run play-by-play automation manually:"
                echo "   python daily_playbyplay_automation.py --date $TARGET_DATE"
            fi
        else
            echo "❌ Enhanced daily automation script not found"
            echo "💡 Running play-by-play automation directly..."
            
            if python daily_playbyplay_automation.py --date "$TARGET_DATE"; then
                echo "✅ Play-by-play automation completed successfully"
            else
                echo "❌ Play-by-play automation failed"
            fi
        fi
    fi
fi

echo ""
echo "🎉 Process completed!"

if [ "$DRY_RUN" = false ] && [ "$CLEANUP_ONLY" = false ]; then
    echo ""
    echo "📋 Verification Commands:"
    echo "========================"
    echo "Check play-by-play files:  ls -la *_playbyplay_${DATE_PATTERN}_*.json"
    echo "Check CSV files:           ls -la *_{hitting,pitching}_${DATE_PATTERN}_*.csv"
    echo "Check JSON data:           ls -la \"$JSON_PATH\""
    echo "Check automation logs:     tail -f logs/enhanced_daily_automation_*.log"
fi

echo ""
#!/bin/bash

# Backfill Missing Play-by-Play Data
# Based on analysis of missing dates from August 4-13, 2025

echo "🔄 Play-by-Play Backfill Tool"
echo "=============================="
echo "📅 Backfilling missing dates: August 4-13, 2025"
echo ""

# Define missing dates in chronological order (oldest first)
MISSING_DATES=(
    "2025-08-04"  # Monday - Schedule in SCANNED only
    "2025-08-07"  # Thursday - Schedule in main dir
    "2025-08-08"  # Friday - Schedule in main dir
    "2025-08-09"  # Saturday - Schedule in main dir
    "2025-08-10"  # Sunday - Schedule in SCANNED only
    "2025-08-11"  # Monday - Schedule in main dir
    "2025-08-12"  # Tuesday - Schedule in main dir
    "2025-08-13"  # Wednesday - Schedule in main dir
)

# Function to check if play-by-play files already exist for a date
check_existing_pbp() {
    local date=$1
    local month_day_year=$(echo $date | awk -F'-' '{print tolower(strftime("%B", mktime($1" "$2" "$3" 0 0 0")))_$3_$1}')
    local count=$(ls -1 *_playbyplay_${month_day_year}_*.json 2>/dev/null | wc -l)
    echo $count
}

# Function to convert YYYY-MM-DD to month_day_year format
convert_date_format() {
    local date=$1
    local month_day_year=$(echo $date | awk -F'-' '{
        months["01"]="january"; months["02"]="february"; months["03"]="march"; 
        months["04"]="april"; months["05"]="may"; months["06"]="june";
        months["07"]="july"; months["08"]="august"; months["09"]="september";
        months["10"]="october"; months["11"]="november"; months["12"]="december";
        day = $3 + 0;  # Remove leading zero
        print months[$2] "_" day "_" $1
    }')
    echo $month_day_year
}

# Function to check if schedule file exists and where
find_schedule_file() {
    local date_format=$1
    local main_file="${date_format}.txt"
    local scanned_file="../BaseballData/SCANNED/${date_format}.txt"
    
    if [ -f "$main_file" ]; then
        echo "main:$main_file"
    elif [ -f "$scanned_file" ]; then
        echo "scanned:$scanned_file"
    else
        echo "none"
    fi
}

# Main backfill process
echo "🔍 Analyzing missing dates..."
echo ""

total_missing=0
backfilled=0
skipped=0
failed=0

for date in "${MISSING_DATES[@]}"; do
    echo "📅 Processing $date..."
    
    # Convert to expected filename format
    date_format=$(convert_date_format $date)
    
    # Check if play-by-play already exists
    existing_count=$(check_existing_pbp $date)
    
    if [ $existing_count -gt 0 ]; then
        echo "   ✅ Already has $existing_count play-by-play files - skipping"
        ((skipped++))
        continue
    fi
    
    # Find schedule file
    schedule_info=$(find_schedule_file $date_format)
    schedule_location=$(echo $schedule_info | cut -d':' -f1)
    schedule_file=$(echo $schedule_info | cut -d':' -f2)
    
    if [ "$schedule_location" = "none" ]; then
        echo "   ❌ No schedule file found for $date_format"
        ((failed++))
        continue
    fi
    
    echo "   📁 Schedule file: $schedule_file"
    ((total_missing++))
    
    # For SCANNED files, copy back to main directory temporarily
    temp_file=""
    if [ "$schedule_location" = "scanned" ]; then
        temp_file="${date_format}.txt"
        echo "   📋 Copying from SCANNED to main directory temporarily..."
        cp "$schedule_file" "$temp_file"
        if [ $? -ne 0 ]; then
            echo "   ❌ Failed to copy schedule file"
            ((failed++))
            continue
        fi
    fi
    
    # Run play-by-play automation
    echo "   ⚾ Running play-by-play automation..."
    if python daily_playbyplay_automation.py --date "$date"; then
        echo "   ✅ Play-by-play completed successfully"
        ((backfilled++))
        
        # Count generated files
        new_count=$(check_existing_pbp $date)
        echo "   📊 Generated $new_count play-by-play files"
    else
        echo "   ❌ Play-by-play automation failed"
        ((failed++))
    fi
    
    # Clean up temporary file
    if [ -n "$temp_file" ] && [ -f "$temp_file" ]; then
        rm "$temp_file"
        echo "   🧹 Cleaned up temporary schedule file"
    fi
    
    echo ""
done

# Summary
echo "📋 Backfill Summary"
echo "==================="
echo "📊 Total dates analyzed: ${#MISSING_DATES[@]}"
echo "✅ Successfully backfilled: $backfilled"
echo "⏭️ Already had data (skipped): $skipped"
echo "❌ Failed: $failed"
echo "🎯 Missing dates found: $total_missing"

if [ $backfilled -gt 0 ]; then
    echo ""
    echo "🎉 Backfill completed! Generated play-by-play files:"
    ls -la *_playbyplay_august_*_2025_*.json | tail -20
fi

echo ""
echo "💡 To verify results, run:"
echo "   ls -la *_playbyplay_august_*_2025_*.json | wc -l"
echo ""
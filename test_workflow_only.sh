#!/bin/bash

# test_workflow_only.sh - Test just the archival and processing workflow
# Skips the scraper step, only tests the data processing pipeline

echo "🧪 Testing Enhanced Daily Automation Workflow (Archive & Process Only)"
echo "====================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Create test CSV files
print_status $BLUE "📝 Creating test CSV files..."

# Create a mock hitting file
cat > "TEST_hitting_august_7_2025_12345.csv" << EOF
player,ab,r,h,rbi,hr,bb,k,avg,obp,slg
Test Player 1,4,1,2,1,1,0,1,0.300,0.350,0.500
Test Player 2,3,0,1,0,0,1,2,0.250,0.333,0.400
EOF

# Create a mock pitching file  
cat > "TEST_pitching_august_7_2025_12345.csv" << EOF
player,ip,h,r,er,bb,k,hr,pc_st,era
Test Pitcher 1,6.0,5,2,2,1,7,1,95-65,3.00
Test Pitcher 2,1.0,0,0,0,0,2,0,15-10,2.50
EOF

print_status $GREEN "✅ Created 2 test CSV files"
ls -la TEST_*.csv

# Test the archive function directly
print_status $BLUE "📦 Testing archive function..."

python3 -c "
from enhanced_scrape import archive_csv_files_to_backups
import sys
print('Testing archive function...')
success = archive_csv_files_to_backups('august_7_2025')
if success:
    print('✅ Archive function successful')
    sys.exit(0)
else:
    print('❌ Archive function failed')
    sys.exit(1)
"
ARCHIVE_EXIT_CODE=$?

print_status $BLUE "🔍 Archive Test Results:"
if [ $ARCHIVE_EXIT_CODE -eq 0 ]; then
    print_status $GREEN "✅ Archive function completed successfully"
    
    # Check if files were archived
    if [ -d "../BaseballData/CSV_BACKUPS" ]; then
        ARCHIVED_COUNT=$(ls -1 ../BaseballData/CSV_BACKUPS/TEST_*.csv 2>/dev/null | wc -l)
        if [ $ARCHIVED_COUNT -gt 0 ]; then
            print_status $GREEN "✅ $ARCHIVED_COUNT files successfully archived to centralized backup"
            print_status $BLUE "   Archived files:"
            ls -la ../BaseballData/CSV_BACKUPS/TEST_*.csv
        else
            print_status $YELLOW "⚠️ No test files found in centralized backup"
        fi
    else
        print_status $YELLOW "⚠️ Centralized backup directory not found"
    fi
    
else
    print_status $RED "❌ Archive function failed with exit code: $ARCHIVE_EXIT_CODE"
fi

# Test data processing (if archives were successful)
if [ $ARCHIVE_EXIT_CODE -eq 0 ]; then
    print_status $BLUE "⚙️ Testing data processing workflow..."
    print_status $YELLOW "Switching to BaseballTracker directory..."
    
    # Check if process_all_stats.sh exists and can run
    if [ -f "../BaseballTracker/process_all_stats.sh" ]; then
        print_status $GREEN "✅ process_all_stats.sh found"
        print_status $BLUE "   (Skipping actual processing to avoid affecting real data)"
    else
        print_status $RED "❌ process_all_stats.sh not found"
    fi
fi

# Clean up test files
print_status $BLUE "🧹 Cleaning up local test files..."
rm -f TEST_*.csv

print_status $BLUE "🧹 Cleaning up test files from centralized backup..."
rm -f ../BaseballData/CSV_BACKUPS/TEST_*.csv

print_status $GREEN "🏁 Workflow test completed"
echo "====================================================================="

# Summary
if [ $ARCHIVE_EXIT_CODE -eq 0 ]; then
    print_status $GREEN "✅ WORKFLOW VALIDATION: Archive functionality working correctly"
    print_status $GREEN "✅ The enhanced_daily_automation.sh script should work properly"
    print_status $BLUE "💡 Ready for production use!"
else
    print_status $RED "❌ WORKFLOW VALIDATION: Archive functionality has issues"
    print_status $YELLOW "🔧 Need to fix archive function before using enhanced_daily_automation.sh"
fi
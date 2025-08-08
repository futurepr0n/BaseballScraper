#!/bin/bash

# test_enhanced_automation.sh - Test the enhanced daily automation workflow
# Creates mock CSV files to test the pipeline without running the full scraper

echo "🧪 Testing Enhanced Daily Automation Workflow"
echo "============================================="

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
ls -la *.csv

print_status $BLUE "📊 Running enhanced daily automation with test files..."

# Run the enhanced daily automation
./enhanced_daily_automation.sh
EXIT_CODE=$?

print_status $BLUE "🔍 Testing Results:"
if [ $EXIT_CODE -eq 0 ]; then
    print_status $GREEN "✅ Enhanced daily automation completed successfully"
    
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
    
    # Check if local files were cleaned up
    LOCAL_CSV_COUNT=$(ls -1 *.csv 2>/dev/null | wc -l)
    if [ $LOCAL_CSV_COUNT -eq 0 ]; then
        print_status $GREEN "✅ Local CSV files successfully cleaned up"
    else
        print_status $YELLOW "⚠️ $LOCAL_CSV_COUNT CSV files still in local directory"
        ls -la *.csv
    fi
    
else
    print_status $RED "❌ Enhanced daily automation failed with exit code: $EXIT_CODE"
fi

print_status $BLUE "🧹 Cleaning up test files from centralized backup..."
rm -f ../BaseballData/CSV_BACKUPS/TEST_*.csv

print_status $BLUE "🏁 Test completed"
echo "============================================="
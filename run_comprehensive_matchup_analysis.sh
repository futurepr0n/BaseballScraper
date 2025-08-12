#!/bin/bash

# Comprehensive Matchup Analysis Script
# Usage: ./run_comprehensive_matchup_analysis.sh "Pitcher 1" "Team 1" "Pitcher 2" "Team 2"

# Check if all arguments are provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 \"Pitcher 1 Name\" \"Team 1 Code\" \"Pitcher 2 Name\" \"Team 2 Code\""
    echo "Example: $0 \"Eury Perez\" \"MIA\" \"Carlos Carrasco\" \"ATL\""
    exit 1
fi

PITCHER1="$1"
TEAM1="$2"
PITCHER2="$3"
TEAM2="$4"
DATE=$(date +%Y-%m-%d)

echo "🔍 Starting Comprehensive Matchup Analysis"
echo "================================================"
echo "📅 Date: $DATE"
echo "⚾ Matchup: $PITCHER1 ($TEAM1) vs $PITCHER2 ($TEAM2)"
echo "================================================"

# Activate virtual environment
source venv/bin/activate

# Step 1: Run weakspot analysis for both pitchers
echo -e "\n📊 Step 1: Running Weakspot Analysis..."
echo "----------------------------------------"

echo "Analyzing $PITCHER1..."
python3 weakspot_analyzer.py --pitcher "$PITCHER1" > "${PITCHER1// /_}_weakspots.json" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ $PITCHER1 weakspot analysis complete"
else
    echo "❌ Error analyzing $PITCHER1"
fi

echo "Analyzing $PITCHER2..."
python3 weakspot_analyzer.py --pitcher "$PITCHER2" > "${PITCHER2// /_}_weakspots.json" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ $PITCHER2 weakspot analysis complete"
else
    echo "❌ Error analyzing $PITCHER2"
fi

# Step 2: Run comprehensive framework analysis
echo -e "\n🎯 Step 2: Running Comprehensive Framework Analysis..."
echo "-----------------------------------------------------"

# Create output filename
OUTPUT_FILE="matchup_${TEAM1}_vs_${TEAM2}_${DATE}.json"

# Run the comprehensive analysis
python3 pitcher_arsenal_analyzer.py "$PITCHER1" "$PITCHER2" --output "$OUTPUT_FILE" --format detailed

# Step 3: Extract key vulnerabilities from weakspot files
echo -e "\n🔑 Step 3: Key Vulnerabilities Summary..."
echo "----------------------------------------"

echo -e "\n$PITCHER1 Top Vulnerabilities:"
if [ -f "${PITCHER1// /_}_weakspots.json" ]; then
    echo "Predictability Score: $(grep -o '"predictability_score": [0-9.]*' "${PITCHER1// /_}_weakspots.json" | cut -d' ' -f2)"
    echo "Top 3 Vulnerable Positions:"
    grep -A2 '"vulnerability_score":' "${PITCHER1// /_}_weakspots.json" | head -15
fi

echo -e "\n$PITCHER2 Top Vulnerabilities:"
if [ -f "${PITCHER2// /_}_weakspots.json" ]; then
    echo "Predictability Score: $(grep -o '"predictability_score": [0-9.]*' "${PITCHER2// /_}_weakspots.json" | cut -d' ' -f2)"
    echo "Top 3 Vulnerable Positions:"
    grep -A2 '"vulnerability_score":' "${PITCHER2// /_}_weakspots.json" | head -15
fi

# Step 4: Check for today's hellraiser picks
echo -e "\n💎 Step 4: Checking Hellraiser Analysis..."
echo "----------------------------------------"

HELLRAISER_FILE="/Users/futurepr0n/Development/Capping.Pro/Claude-Code/BaseballData/data/hellraiser/hellraiser_analysis_${DATE}.json"

if [ -f "$HELLRAISER_FILE" ]; then
    echo "Hellraiser picks for $TEAM1 vs $PITCHER2:"
    grep -B2 -A10 "\"team\": \"$TEAM1\"" "$HELLRAISER_FILE" | grep -A10 "$PITCHER2" || echo "No specific picks found"
    
    echo -e "\nHellraiser picks for $TEAM2 vs $PITCHER1:"
    grep -B2 -A10 "\"team\": \"$TEAM2\"" "$HELLRAISER_FILE" | grep -A10 "$PITCHER1" || echo "No specific picks found"
else
    echo "No hellraiser analysis found for today"
fi

# Step 5: Generate quick recommendations
echo -e "\n📋 Analysis Complete!"
echo "===================="
echo "Output files created:"
echo "1. ${PITCHER1// /_}_weakspots.json"
echo "2. ${PITCHER2// /_}_weakspots.json"
echo "3. $OUTPUT_FILE (detailed comparative analysis)"

echo -e "\n🎯 Quick Recommendations:"
echo "------------------------"
echo "1. Check predictability scores - Higher = More exploitable"
echo "2. Target lineup positions with highest vulnerability scores"
echo "3. Focus on innings with peak vulnerability"
echo "4. Cross-reference with hitter arsenal data for specific matchups"

echo -e "\n✅ Analysis complete! Review the output files for detailed insights."
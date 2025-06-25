#!/bin/bash

# Setup script for Enhanced Baseball Scraper with Postponement Detection
# This script sets up the enhanced scraper and automation tools

echo "🏟️ Setting up Enhanced Baseball Scraper with Postponement Detection"
echo "================================================================="

# Make scripts executable
echo "📄 Making scripts executable..."
chmod +x enhanced_scrape.py
chmod +x smart_morning_run.py

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p SCANNED
mkdir -p logs
mkdir -p backups

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
python3 -c "import requests, bs4, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing Python dependencies. Installing..."
    pip3 install requests beautifulsoup4 pandas
else
    echo "✅ Python dependencies are satisfied"
fi

# Create a sample crontab entry
echo "⏰ Creating sample crontab configuration..."
cat > crontab_sample.txt << 'EOF'
# Enhanced Baseball Scraper - Run every morning at 8:00 AM
# This will automatically detect postponements and update next day's schedule
0 8 * * * cd /path/to/BaseballScraper && /usr/bin/python3 smart_morning_run.py >> logs/morning_run.log 2>&1

# Alternative: Run with email notifications
# 0 8 * * * cd /path/to/BaseballScraper && /usr/bin/python3 smart_morning_run.py | mail -s "Baseball Scraper Report" your-email@example.com

# Backup important files weekly (Sundays at 2 AM)
0 2 * * 0 cd /path/to/BaseballScraper && tar -czf backups/weekly_backup_$(date +\%Y\%m\%d).tar.gz *.txt *.json *.py

# Clean old logs monthly (1st of month at 3 AM)
0 3 1 * * cd /path/to/BaseballScraper && find logs/ -name "*.log" -mtime +30 -delete
EOF

# Create a manual test script
echo "🧪 Creating test script..."
cat > test_postponement_detection.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for postponement detection
Use this to test the postponement detection logic with known postponed games
"""

from enhanced_scrape import detect_postponed_game, get_page_content
import sys

def test_postponement_detection():
    print("🧪 Testing Postponement Detection")
    print("=" * 40)
    
    # Test with a known URL (you can replace with actual postponed game URL)
    test_url = input("Enter a game URL to test (or press Enter for demo): ").strip()
    
    if not test_url:
        print("Demo mode - testing with mock postponed content")
        mock_html = """
        <html>
            <body>
                <div class="game-status">Game Postponed due to rain</div>
                <div>No team data available</div>
            </body>
        </html>
        """
        result = detect_postponed_game(mock_html, "demo_url")
    else:
        print(f"Fetching content from: {test_url}")
        html_content = get_page_content(test_url)
        if html_content:
            result = detect_postponed_game(html_content, test_url)
        else:
            print("❌ Could not fetch page content")
            return
    
    print("\n📊 Postponement Detection Result:")
    print(f"   Is Postponed: {result['is_postponed']}")
    print(f"   Reason: {result['reason']}")
    print(f"   Status: {result['status']}")
    
    if 'detected_text' in result:
        print(f"   Detected Text: {result['detected_text']}")

if __name__ == "__main__":
    test_postponement_detection()
EOF

chmod +x test_postponement_detection.py

# Create a usage guide
echo "📖 Creating usage guide..."
cat > POSTPONEMENT_DETECTION_GUIDE.md << 'EOF'
# Enhanced Baseball Scraper - Postponement Detection Guide

## Overview
The enhanced scraper automatically detects postponed/cancelled games and updates the next day's schedule with any new games that may have been added to replace them.

## Files

### Core Scripts
- `enhanced_scrape.py` - Main scraper with postponement detection
- `smart_morning_run.py` - Intelligent automation script
- `test_postponement_detection.py` - Test postponement detection logic

### Original Files
- `scrape.py` - Original scraper (kept for backup)

## How It Works

### 1. Postponement Detection
The scraper detects postponed games by:
- Looking for missing `div.TeamTitle` elements (your original error case)
- Scanning for postponement keywords (postponed, cancelled, rain delay, etc.)
- Checking game status elements
- Analyzing page structure for signs of postponement

### 2. Schedule Updates
When postponed games are detected:
- Fetches fresh schedule from ESPN for the next day
- Compares with existing schedule file
- Adds any new games that weren't previously scheduled
- Creates backup of original schedule file
- Logs all changes for review

### 3. Automation
The `smart_morning_run.py` script:
- Runs the enhanced scraper automatically
- Analyzes results and generates reports
- Handles errors gracefully
- Creates detailed logs for monitoring

## Usage

### Manual Execution
```bash
# Run enhanced scraper once
python3 enhanced_scrape.py

# Run smart morning automation
python3 smart_morning_run.py

# Test postponement detection
python3 test_postponement_detection.py

# Dry run (see what would happen without executing)
python3 smart_morning_run.py --dry-run

# Verbose output
python3 smart_morning_run.py --verbose
```

### Automated Execution
1. Edit the crontab sample file with your actual paths
2. Install the cron job:
   ```bash
   crontab crontab_sample.txt
   ```

### Example Workflow
1. Morning automation runs at 8 AM via cron
2. Scraper processes yesterday's games
3. Detects any postponed games
4. Updates tomorrow's schedule with new games from ESPN
5. Generates comprehensive report
6. Sends email notification (if configured)

## Output Files

### Generated Files
- `postponements_MONTH_DAY_YEAR.json` - Detailed postponement logs
- `morning_run_YYYYMMDD.json` - Daily automation results
- `MONTH_DAY_YEAR.txt.backup.TIMESTAMP` - Schedule backups

### Log Files
- `logs/morning_run.log` - Automation logs
- Console output with detailed processing information

## Monitoring

### Key Metrics to Monitor
- Number of postponed games detected
- Schedule update success/failure
- Data extraction success rate
- File archival status

### Alert Conditions
- Multiple postponements in a day
- Schedule update failures
- Scraper execution failures
- Missing expected game data

## Troubleshooting

### Common Issues
1. **Schedule Update Fails**
   - Check ESPN website accessibility
   - Verify date formatting
   - Check file permissions

2. **False Postponement Detection**
   - Review postponement logs
   - Adjust detection criteria if needed
   - Check specific game URLs manually

3. **Missing Dependencies**
   - Run setup script again
   - Install missing Python packages

### Manual Recovery
If automation fails:
1. Check `morning_run_YYYYMMDD.json` for details
2. Run enhanced scraper manually
3. Manually update schedule files if needed
4. Review postponement logs for missed games

## Customization

### Adjusting Detection Sensitivity
Edit the `postponement_indicators` list in `enhanced_scrape.py`:
```python
postponement_indicators = [
    'postponed', 'cancelled', 'canceled', 'suspended', 'delayed',
    'ppd', 'susp', 'game not played', 'rain delay', 'weather',
    'makeup game', 'rescheduled'
    # Add more keywords as needed
]
```

### Email Notifications
Modify the crontab entry to include email:
```bash
0 8 * * * cd /path/to/BaseballScraper && python3 smart_morning_run.py | mail -s "Baseball Scraper Report" your-email@example.com
```

### Schedule Update Timing
Adjust cron timing as needed:
- Earlier: `0 7 * * *` (7 AM)
- Later: `0 9 * * *` (9 AM)
- Multiple times: `0 7,12,18 * * *` (7 AM, 12 PM, 6 PM)

## Best Practices

1. **Monitor Regularly**: Check logs and reports daily
2. **Backup Data**: Keep backups of schedule files
3. **Test Changes**: Use dry-run mode when testing
4. **Review Postponements**: Manually verify postponement detections
5. **Update Keywords**: Add new postponement indicators as discovered

EOF

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Review the generated files:"
echo "   - crontab_sample.txt (for automation setup)"
echo "   - POSTPONEMENT_DETECTION_GUIDE.md (detailed usage guide)"
echo "   - test_postponement_detection.py (for testing)"
echo ""
echo "2. Test the enhanced scraper:"
echo "   python3 enhanced_scrape.py"
echo ""
echo "3. Test the automation:"
echo "   python3 smart_morning_run.py --dry-run"
echo ""
echo "4. Set up automation (edit paths in crontab_sample.txt first):"
echo "   crontab crontab_sample.txt"
echo ""
echo "🏟️ Your enhanced baseball scraper is ready to intelligently handle postponements!"
# BaseballScraper - CLAUDE.md

This file provides guidance to Claude Code when working with the BaseballScraper component.

## Component Overview

The **BaseballScraper** is a Python-based data collection system that scrapes MLB game data from ESPN boxscores and generates CSV files for the baseball analytics pipeline.

## Enhanced Features (2025 Update)

### Postponement Detection System
The scraper now includes intelligent postponement detection and automatic schedule updates:

- **Enhanced Scraper** (`enhanced_scrape.py`) - Main scraper with postponement detection
- **Smart Automation** (`smart_morning_run.py`) - Intelligent morning automation
- **Setup Scripts** (`setup_postponement_detection.sh`) - Automated configuration

## Quick Start Commands

### Basic Setup
```bash
cd BaseballScraper
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 pandas
```

### Enhanced Setup with Postponement Detection (Recommended)
```bash
cd BaseballScraper

# 1. Run the setup
./setup_postponement_detection.sh

# 2. Test the enhanced scraper
python3 enhanced_scrape.py

# 3. Test automation (dry run)
python3 smart_morning_run.py --dry-run

# 4. Set up daily automation at 8 AM
# (Edit paths in crontab_sample.txt first, then)
crontab crontab_sample.txt
```

### Manual Execution
```bash
# Original scraper (processes yesterday's games)
python scrape.py

# Enhanced scraper with postponement detection
python enhanced_scrape.py

# Smart morning automation
python smart_morning_run.py

# Test postponement detection
python test_postponement_detection.py
```

### Automated Execution
```bash
# Set up daily automation (edit paths in crontab_sample.txt first)
crontab crontab_sample.txt
```

## File Structure

### Core Scripts
- `scrape.py` - Original scraper (backup/legacy)
- `enhanced_scrape.py` - Enhanced scraper with postponement detection
- `smart_morning_run.py` - Intelligent automation wrapper
- `test_postponement_detection.py` - Testing utilities

### Schedule Files
- `MONTH_DAY_YEAR.txt` - Daily game URL lists (e.g., `june_18_2025.txt`)
- `crontab_sample.txt` - Cron job configuration template

### Output Files
- `TEAM_hitting_DATE_GAMEID.csv` - Team hitting statistics
- `TEAM_pitching_DATE_GAMEID.csv` - Team pitching statistics
- `postponements_DATE.json` - Postponement detection logs
- `morning_run_YYYYMMDD.json` - Daily automation results

### Directories
- `SCANNED/` - Processed schedule files archive
- `logs/` - Automation and error logs
- `backups/` - Weekly backup archives

## Key Features

### Postponement Detection
Automatically detects postponed/cancelled games by:
- Checking for missing `div.TeamTitle` elements
- Scanning for postponement keywords (postponed, cancelled, rain delay, etc.)
- Analyzing game status elements and page structure
- Generating detailed postponement reports

### Schedule Management
When postponements are detected:
- Fetches fresh schedule from ESPN for next day
- Updates next day's schedule file with new games
- Creates automatic backups of original files
- Logs all changes for review

### Data Processing
Extracts comprehensive player statistics:
- **Hitting**: AB, R, H, RBI, HR, BB, K, AVG, OBP, SLG
- **Pitching**: IP, H, R, ER, BB, K, HR, PC-ST, ERA
- Includes gameId in all output filenames for tracking

## Integration Points

### With BaseballTracker
- CSV outputs feed into BaseballTracker's data processing pipeline
- Schedule files coordinate daily data collection
- Postponement logs help identify data gaps

### With BaseballAPI
- Generated CSV files provide base statistics for API analysis
- Postponement detection ensures API has complete data sets

## Development Workflow

### Daily Operation (Automated)
**Morning Automation Workflow:**

1. **8:00 AM** - Cron job runs `smart_morning_run.py`
2. **Scraper runs** - Processes yesterday's games  
3. **Postponements detected** - Automatically identified
4. **Schedule updated** - Tomorrow's file updated with new games
5. **Report generated** - Comprehensive summary created
6. **Files archived** - Processed files moved to SCANNED/

```bash
# Morning automation (via cron at 8 AM)
smart_morning_run.py
  ├── Runs enhanced_scrape.py
  ├── Detects postponements
  ├── Updates next day's schedule
  ├── Generates comprehensive report
  └── Archives processed files
```

### Manual Operation
```bash
# 1. Run scraper for specific date
python enhanced_scrape.py

# 2. Check for postponements
cat postponements_MONTH_DAY_YEAR.json

# 3. Verify schedule updates
diff june_18_2025.txt june_19_2025.txt

# 4. Process data in BaseballTracker
cd ../BaseballTracker
./process_all_stats.sh
```

### Testing and Debugging
```bash
# Test postponement detection
python test_postponement_detection.py

# Dry run automation
python smart_morning_run.py --dry-run

# Verbose output
python smart_morning_run.py --verbose

# Check logs
tail -f logs/morning_run.log
```

## Common Issues and Solutions

### Missing Dependencies
```bash
# Install required packages
pip install requests beautifulsoup4 pandas
```

### Postponement Detection Issues
- Check `postponements_DATE.json` for detection details
- Review `POSTPONEMENT_DETECTION_GUIDE.md` for troubleshooting
- Test with known postponed game URLs

### Schedule Update Failures
- Verify ESPN website accessibility
- Check file permissions for schedule files
- Review ESPN schedule page format changes

### Automation Issues
- Check cron job configuration: `crontab -l`
- Review automation logs: `logs/morning_run.log`
- Test manual execution first

## Data Quality

### Validation Checks
- Minimum player count per team (validates complete data)
- Essential columns presence (player, key stats)
- GameId extraction success
- File format validation

### Error Handling
- Graceful handling of network issues
- Automatic retry logic with delays
- Comprehensive error logging
- Postponement vs. error differentiation

## Security Considerations

- User-Agent headers for ethical scraping
- Request delays to avoid overloading ESPN servers
- No sensitive data storage
- Automatic cleanup of old logs

## Performance Notes

### Timing
- Random delays between requests (10-35 seconds)
- Total execution time: ~15-30 minutes for full day
- Memory usage: Moderate (pandas DataFrame processing)

### Optimization
- Concurrent processing not used (respects ESPN servers)
- Efficient data structure usage
- Automatic file archival to prevent directory bloat

## Monitoring and Alerts

### Key Metrics
- Number of games processed successfully
- Number of postponements detected
- Schedule update success rate
- Data extraction completion rate

### Alert Conditions
- Multiple postponements in single day
- Schedule update failures
- Scraper execution failures
- Unexpected data format changes

## Future Enhancements

### Planned Features
- Multiple data source support
- Enhanced postponement prediction
- Real-time schedule monitoring
- Advanced data validation

### Integration Opportunities
- Direct API integration with BaseballAPI
- Real-time data streaming to BaseballTracker
- Machine learning for postponement prediction
- Weather data integration for postponement context

## Dependencies

### Python Packages
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing and data extraction
- `pandas` - Data manipulation and CSV generation

### System Requirements
- Python 3.7+
- Unix-like environment (for cron automation)
- Internet connectivity for ESPN access
- Sufficient disk space for CSV outputs

### External Services
- ESPN MLB boxscore pages
- ESPN MLB schedule pages
- System cron daemon (for automation)

For detailed usage instructions, see `POSTPONEMENT_DETECTION_GUIDE.md`.
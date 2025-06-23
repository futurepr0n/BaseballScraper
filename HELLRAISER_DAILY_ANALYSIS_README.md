# Hellraiser Daily Analysis System

## Overview

This system runs Hellraiser HR analysis throughout the day, capturing changing odds and lineup information to optimize pick timing. It archives all analysis runs and provides performance tracking to identify the most successful analysis times and methodologies.

## 🔥 Key Features

- **Continuous Daily Analysis**: Runs multiple times per day based on game schedules
- **Automatic Archiving**: Saves each analysis run with timestamps for comparison
- **Performance Tracking**: Analyzes which times/methods produce the best picks
- **Intelligent Scheduling**: Adapts to daily game times (11 AM - 10 PM range)
- **Pick Evolution Tracking**: Shows how picks change throughout the day

## 📁 File Structure

```
BaseballScraper/
├── daily_hellraiser_scheduler.py      # Main scheduler with archiving
├── generate_hellraiser_analysis.py    # Core analysis generator
├── setup_hellraiser_automation.sh     # Automated cron setup
├── simple_performance_analyzer.py     # Performance analysis tool
├── test_hellraiser_workflow_fixed.py  # Test suite
└── logs/                              # All logs and test results

BaseballTracker/public/data/hellraiser/
├── hellraiser_YYYY-MM-DD.json        # Current day's analysis
├── archive/                           # Timestamped analysis history
└── performance/                       # Analysis reports and metrics
```

## 🚀 Quick Start

### 1. Setup and Testing

```bash
cd BaseballScraper

# Test the complete workflow
python3 test_hellraiser_workflow_fixed.py --quick

# Run the automation setup
./setup_hellraiser_automation.sh

# Install the cron jobs
crontab hellraiser_crontab.txt
```

### 2. Verify Installation

```bash
# Check cron jobs are installed
crontab -l

# Monitor the scheduler logs
tail -f logs/hellraiser_scheduler.log

# Check that directories were created
ls -la ../BaseballTracker/public/data/hellraiser/
```

## 📋 Daily Schedule

The system automatically runs based on game times:

- **Every 2 hours from 6 AM to 10 PM** (captures all game windows)
- **12:30 PM** (before early afternoon games)
- **6:30 PM** (before evening games)

### Sample Daily Timeline:
```
06:00 - Morning Baseline (before first games)
08:00 - Early Check
10:00 - Pre-game Update
12:00 - Midday Analysis
12:30 - Afternoon Game Prep
14:00 - Afternoon Check
16:00 - Pre-evening Update
18:00 - Evening Analysis
18:30 - Evening Game Prep
20:00 - Late Game Check
22:00 - Final Analysis
```

## 🎯 Analysis Pathways

The system tracks three main analysis pathways:

1. **Perfect Storm** - Multi-faceted advantages (pitcher vulnerability + elite batter)
2. **Batter-Driven** - Elite batter power profiles against specific pitch types
3. **Pitcher-Driven** - Vulnerable pitchers making multiple batters viable

## 📊 Performance Tracking

### Running Performance Analysis

```bash
# Analyze last 7 days
python3 simple_performance_analyzer.py --days 7

# Check specific recent performance
python3 simple_performance_analyzer.py --days 3

# View generated reports
ls -la ../BaseballTracker/public/data/hellraiser/performance/
```

### Understanding Reports

Performance reports show:
- **Pathway effectiveness** - Which methods produce highest confidence picks
- **Time patterns** - Which hours generate the most successful analysis
- **Player frequency** - Most commonly picked players and their success rates
- **Pick evolution** - How selections change throughout the day

## 🔧 Manual Operations

### Run Single Analysis
```bash
# Generate current analysis
python3 generate_hellraiser_analysis.py

# Run scheduler once (respects time windows)
python3 daily_hellraiser_scheduler.py
```

### Archive Management
```bash
# Check archive files
ls -la ../BaseballTracker/public/data/hellraiser/archive/

# Archive files are named: hellraiser_YYYY-MM-DD_HH-MM-SS_run_type.json
# Example: hellraiser_2025-06-23_14-30-00_midday_check.json
```

### Monitor Real-time
```bash
# Watch scheduler activity
tail -f logs/hellraiser_scheduler.log

# Watch cron execution
tail -f logs/hellraiser_cron.log

# Check current analysis
cat ../BaseballTracker/public/data/hellraiser/hellraiser_$(date +%Y-%m-%d).json
```

## 📈 Data Integration

### With HellraiserCard Component
The React component automatically loads the latest analysis:
- Displays current day's picks with confidence scores
- Shows pathway classifications and value assessments
- Updates when new analysis runs complete

### Archive Data Format
Each archived file contains:
```json
{
  "picks": [...],
  "updatedAt": "2025-06-23T14:30:00Z",
  "generatedBy": "hellraiser_v4.0",
  "archiveMetadata": {
    "archivedAt": "2025-06-23T14:30:15Z",
    "runType": "Midday Check",
    "originalFilename": "hellraiser_2025-06-23.json"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

**Analysis not running:**
```bash
# Check cron status
crontab -l | grep hellraiser

# Verify file permissions
ls -la daily_hellraiser_scheduler.py
# Should show -rwxr-xr-x (executable)

# Test manual execution
python3 daily_hellraiser_scheduler.py
```

**No archive files:**
```bash
# Check if analysis is generating output
ls -la ../BaseballTracker/public/data/hellraiser/

# Verify archive directory exists
mkdir -p ../BaseballTracker/public/data/hellraiser/archive
```

**Performance analysis fails:**
```bash
# Use simple analyzer instead
python3 simple_performance_analyzer.py

# Check if archive files exist
ls -la ../BaseballTracker/public/data/hellraiser/archive/
```

### Log Analysis
```bash
# Check for errors in scheduler
grep "ERROR\\|FAIL" logs/hellraiser_scheduler.log

# View cron execution
grep "hellraiser" /var/log/cron

# Check last few runs
tail -20 logs/hellraiser_scheduler.log
```

## 📅 Maintenance

### Weekly Tasks
- Review performance reports to identify optimal analysis times
- Clean up old log files (older than 30 days)
- Check disk space usage in archive directory

### Monthly Tasks
- Analyze pathway effectiveness trends
- Update cron schedule based on seasonal game time changes
- Archive old performance reports

### Archive Cleanup
```bash
# Archive files older than 30 days (optional)
find ../BaseballTracker/public/data/hellraiser/archive/ -name "*.json" -mtime +30 -exec mv {} archive_old/ \;

# Compress old logs
gzip logs/hellraiser_*.log.old
```

## 🎯 Success Metrics

Track these key performance indicators:

1. **Analysis Frequency**: 8-12 analysis runs per day
2. **Archive Growth**: ~10-15 archived files per day
3. **Pathway Distribution**: Balanced across all three methods
4. **Confidence Trends**: Average confidence scores by time of day
5. **Pick Evolution**: How many picks change throughout the day

## 🔮 Advanced Usage

### Custom Scheduling
Edit `hellraiser_crontab.txt` to adjust timing:
```bash
# More frequent during peak betting hours
*/30 17-21 * * * /path/to/run_hellraiser_cron.sh
```

### Team-Specific Analysis
```bash
# Analyze specific teams only
python3 generate_hellraiser_analysis.py --teams NYY LAA
```

### Integration with Other Systems
The archived data can be used for:
- Machine learning model training
- Betting outcome tracking
- Odds movement correlation analysis
- Player performance prediction

---

## 📞 Support

For issues or questions:
1. Check the test suite: `python3 test_hellraiser_workflow_fixed.py`
2. Review logs in `logs/` directory
3. Verify cron jobs are running: `crontab -l`
4. Ensure odds data is updating: check `update-odds.sh` automation

This system provides comprehensive daily HR analysis with full archiving and performance tracking to help identify the most effective analysis timing and methodologies.
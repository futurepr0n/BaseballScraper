#!/bin/bash
# MLB Game Backfill Pipeline
# ==========================
# Comprehensive script to backfill missing games and regenerate predictions

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Python environment is available
check_python_env() {
    log_info "Checking Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is not available"
        exit 1
    fi
    
    # Check required packages
    python3 -c "import requests, bs4, pandas" 2>/dev/null || {
        log_warning "Missing required Python packages. Installing..."
        pip3 install requests beautifulsoup4 pandas
    }
    
    log_success "Python environment ready"
}

# Function to backup current data
backup_current_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup in $backup_dir"
    
    mkdir -p "$backup_dir"
    
    # Backup JSON files for affected dates
    for date in "2025-07-29" "2025-08-02" "2025-07-12"; do
        IFS='-' read -r year month day <<< "$date"
        month_name=$(date -d "$date" +%B | tr '[:upper:]' '[:lower:]')
        json_file="../BaseballData/data/2025/$month_name/${month_name}_${day}_2025.json"
        
        if [[ -f "$json_file" ]]; then
            cp "$json_file" "$backup_dir/"
            log_info "Backed up $json_file"
        fi
    done
    
    log_success "Backup created at $backup_dir"
}

# Function to run the backfill script
run_backfill() {
    log_info "Starting game backfill process..."
    
    if [[ -f "games_to_backfill.json" ]]; then
        log_info "Using configuration file: games_to_backfill.json"
        python3 backfill_missing_games.py --config games_to_backfill.json
    else
        log_info "Using default known issues"
        python3 backfill_missing_games.py
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Backfill process completed successfully"
    else
        log_error "Backfill process failed"
        exit 1
    fi
}

# Function to validate backfill results
validate_results() {
    log_info "Validating backfill results..."
    
    # Check if games were properly added/updated
    local validation_errors=0
    
    # Check July 29 - should have proper final score for game 401696518
    local july29_file="../BaseballData/data/2025/july/july_29_2025.json"
    if [[ -f "$july29_file" ]]; then
        if grep -q '"status": "Scheduled"' "$july29_file" && grep -q '"originalId": 401696518' "$july29_file"; then
            log_error "July 29 Game 2 still shows 'Scheduled' status"
            ((validation_errors++))
        else
            log_success "July 29 Game 2 status updated"
        fi
    fi
    
    # Check August 2 - should show ATL win
    local aug2_file="../BaseballData/data/2025/august/august_02_2025.json"
    if [[ -f "$aug2_file" ]]; then
        if grep -q '"homeScore": 1' "$aug2_file" && grep -q '"awayScore": 0' "$aug2_file" && grep -q '"originalId": 401696561' "$aug2_file"; then
            log_error "August 2 game still shows incorrect score"
            ((validation_errors++))
        else
            log_success "August 2 game score updated"
        fi
    fi
    
    # Check July 12 - should have both Cleveland games
    local july12_file="../BaseballData/data/2025/july/july_12_2025.json"
    if [[ -f "$july12_file" ]]; then
        local cle_games=$(grep -c '"awayTeam": "CLE"' "$july12_file" || echo 0)
        if [[ $cle_games -lt 2 ]]; then
            log_error "July 12 should have 2 Cleveland games, found $cle_games"
            ((validation_errors++))
        else
            log_success "July 12 has both Cleveland games"
        fi
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "All validation checks passed"
        return 0
    else
        log_error "Validation failed with $validation_errors errors"
        return 1
    fi
}

# Function to regenerate predictions
regenerate_predictions() {
    log_info "Regenerating predictions with updated data..."
    
    # Change to BaseballTracker directory
    cd "../BaseballTracker"
    
    # Run the daily update for affected dates
    for date in "2025-07-29" "2025-08-02" "2025-07-12"; do
        log_info "Regenerating predictions for $date"
        if [[ -f "daily_update.sh" ]]; then
            ./daily_update.sh "$date" || log_warning "Failed to regenerate for $date"
        else
            log_warning "daily_update.sh not found"
        fi
    done
    
    # Return to original directory
    cd "$SCRIPT_DIR"
    
    log_success "Prediction regeneration completed"
}

# Function to display summary
display_summary() {
    log_info "Backfill Pipeline Summary"
    echo "=========================="
    echo "Processed games:"
    echo "  - July 29: TOR@BAL Game 2 (401696518) - Fixed final score"
    echo "  - August 2: ATL@CIN (401696561) - Corrected suspended game result"  
    echo "  - July 12: CLE@CHW doubleheader (401800822, 401696319) - Added missing games"
    echo ""
    echo "Next steps:"
    echo "  1. Verify data looks correct in BaseballTracker frontend"
    echo "  2. Check that predictions have been updated"
    echo "  3. Monitor for any additional data integrity issues"
    echo ""
    log_success "Backfill pipeline completed successfully!"
}

# Main execution
main() {
    log_info "Starting MLB Game Backfill Pipeline"
    echo "===================================="
    
    # Parse command line arguments
    local skip_backup=false
    local skip_validation=false
    local skip_predictions=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --skip-validation)
                skip_validation=true
                shift
                ;;
            --skip-predictions)
                skip_predictions=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-backup       Skip backing up current data"
                echo "  --skip-validation   Skip validation of results"
                echo "  --skip-predictions  Skip regenerating predictions"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute pipeline steps
    check_python_env
    
    if [[ "$skip_backup" != true ]]; then
        backup_current_data
    fi
    
    run_backfill
    
    if [[ "$skip_validation" != true ]]; then
        if ! validate_results; then
            log_error "Validation failed. Check the backfill results manually."
            exit 1
        fi
    fi
    
    if [[ "$skip_predictions" != true ]]; then
        regenerate_predictions
    fi
    
    display_summary
}

# Execute main function with all arguments
main "$@"
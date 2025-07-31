#!/usr/bin/env python3
"""
Roster Enhancement Tool
Applies suggested improvements to roster.json based on handedness validation results.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from enhanced_player_name_matcher import PlayerNameNormalizer, PlayerNameMatcher

class RosterEnhancementTool:
    """Tool for applying roster enhancements"""
    
    def __init__(self, roster_path: str = "../BaseballTracker/public/data/rosters.json"):
        self.roster_path = roster_path
        self.normalizer = PlayerNameNormalizer()
        self.backup_path = None
        
    def create_backup(self) -> str:
        """Create backup of current roster file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.roster_path}.backup_{timestamp}"
        
        shutil.copy2(self.roster_path, backup_path)
        self.backup_path = backup_path
        
        print(f"📦 Backup created: {backup_path}")
        return backup_path
    
    def load_roster_data(self) -> List[Dict]:
        """Load current roster data"""
        try:
            with open(self.roster_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading roster data: {e}")
            return []
    
    def save_roster_data(self, roster_data: List[Dict]) -> bool:
        """Save updated roster data"""
        try:
            with open(self.roster_path, 'w', encoding='utf-8') as f:
                json.dump(roster_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving roster data: {e}")
            return False
    
    def find_player_by_id(self, roster_data: List[Dict], player_id: str) -> Optional[Dict]:
        """Find player in roster by ID"""
        for player in roster_data:
            if str(player.get('playerId', '')) == str(player_id):
                return player
        return None
    
    def add_alternate_names_field(self, player: Dict, alternate_names: List[str]) -> Dict:
        """Add alternateNames field to player record"""
        if 'alternateNames' not in player:
            player['alternateNames'] = []
        
        # Add new alternate names (avoid duplicates)
        for alt_name in alternate_names:
            normalized_alt = self.normalizer.normalize_name(alt_name)
            if normalized_alt and normalized_alt not in player['alternateNames']:
                player['alternateNames'].append(normalized_alt)
        
        return player
    
    def enhance_fullname_field(self, player: Dict, new_full_name: str) -> Dict:
        """Enhance fullName field if it's incomplete"""
        current_full = player.get('fullName', '')
        current_name = player.get('name', '')
        
        # Only update if current fullName is same as name (indicating it's abbreviated)
        if current_full == current_name:
            player['fullName'] = new_full_name
            print(f"   📝 Enhanced fullName: '{current_full}' → '{new_full_name}'")
        
        return player
    
    def apply_handedness_updates(self, roster_data: List[Dict], handedness_results: List[Dict]) -> int:
        """Apply handedness updates from validation results"""
        updates_made = 0
        
        for result in handedness_results:
            if not result.get('needs_update'):
                continue
            
            player_name = result.get('name', '')
            team = result.get('team', '')
            new_handedness = result.get('api_handedness', '')
            player_type = 'pitcher' if 'throws' in result.get('action_needed', '') else 'hitter'
            
            # Find player in roster
            for player in roster_data:
                if (player.get('name', '').lower() == player_name.lower() or 
                    player.get('fullName', '').lower() == player_name.lower()) and \
                   player.get('team', '') == team and \
                   player.get('type', '') == player_type:
                    
                    # Update handedness
                    if player_type == 'pitcher':
                        handedness_field = 'ph'
                    else:
                        handedness_field = 'bats'
                        # Convert S to B for switch hitters
                        if new_handedness == 'S':
                            new_handedness = 'B'
                    
                    old_value = player.get(handedness_field, 'MISSING')
                    player[handedness_field] = new_handedness
                    
                    print(f"   ✅ Updated {player_name} ({team}): {handedness_field} '{old_value}' → '{new_handedness}'")
                    updates_made += 1
                    break
        
        return updates_made
    
    def apply_roster_suggestions(self, roster_data: List[Dict], suggestions: List[Dict]) -> int:
        """Apply roster enhancement suggestions"""
        updates_made = 0
        
        for suggestion in suggestions:
            player_id = suggestion.get('player_id', '')
            suggested_value = suggestion.get('suggested_value', '')
            action = suggestion.get('suggested_action', '')
            
            player = self.find_player_by_id(roster_data, player_id)
            if not player:
                print(f"   ⚠️ Player {player_id} not found in roster")
                continue
            
            if action == 'add_alternate_name':
                old_alternates = player.get('alternateNames', [])
                self.add_alternate_names_field(player, [suggested_value])
                new_alternates = player.get('alternateNames', [])
                
                if len(new_alternates) > len(old_alternates):
                    print(f"   ✅ Added alternate name to {player.get('name', 'Unknown')}: '{suggested_value}'")
                    updates_made += 1
        
        return updates_made
    
    def enhance_roster_data(self, handedness_results: Dict, 
                          apply_changes: bool = False) -> Dict:
        """Main method to enhance roster data"""
        print("🔧 Starting Roster Enhancement Process...")
        
        if apply_changes:
            # Create backup before making changes
            self.create_backup()
        
        # Load current roster
        roster_data = self.load_roster_data()
        if not roster_data:
            return {'error': 'Failed to load roster data'}
        
        total_updates = 0
        
        # Apply handedness updates
        pitcher_updates = self.apply_handedness_updates(
            roster_data, handedness_results.get('pitcher_validation', [])
        )
        batter_updates = self.apply_handedness_updates(
            roster_data, handedness_results.get('batter_validation', [])
        )
        
        # Apply roster suggestions
        suggestion_updates = self.apply_roster_suggestions(
            roster_data, handedness_results.get('roster_suggestions', [])
        )
        
        total_updates = pitcher_updates + batter_updates + suggestion_updates
        
        print(f"\n📊 Enhancement Summary:")
        print(f"   • Pitcher handedness updates: {pitcher_updates}")
        print(f"   • Batter handedness updates: {batter_updates}")
        print(f"   • Roster suggestions applied: {suggestion_updates}")
        print(f"   • Total updates: {total_updates}")
        
        if apply_changes and total_updates > 0:
            # Save updated roster
            if self.save_roster_data(roster_data):
                print(f"✅ Roster data updated successfully!")
                print(f"📦 Backup available at: {self.backup_path}")
                return {
                    'success': True,
                    'updates_made': total_updates,
                    'backup_path': self.backup_path
                }
            else:
                # Restore backup if save failed
                if self.backup_path:
                    shutil.copy2(self.backup_path, self.roster_path)
                    print(f"❌ Save failed - roster restored from backup")
                return {'error': 'Failed to save updated roster'}
        elif not apply_changes:
            print(f"🔍 DRY RUN - No changes applied to roster file")
            return {
                'success': True,
                'dry_run': True,
                'potential_updates': total_updates
            }
        else:
            print(f"ℹ️ No updates needed - roster data is current")
            return {
                'success': True,
                'updates_made': 0
            }

def main():
    """Main execution function for standalone use"""
    import sys
    
    # Check if handedness results file provided
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
        try:
            with open(results_file, 'r') as f:
                handedness_results = json.load(f)
        except Exception as e:
            print(f"❌ Error loading results file {results_file}: {e}")
            return
    else:
        print("Usage: python roster_enhancement_tool.py <handedness_results.json>")
        print("Or import and use programmatically")
        return
    
    # Apply enhancements
    enhancer = RosterEnhancementTool()
    
    # Ask user if they want to apply changes
    apply_changes = input("Apply changes to roster.json? (y/N): ").lower().strip() == 'y'
    
    result = enhancer.enhance_roster_data(handedness_results, apply_changes)
    
    if result.get('success'):
        print("\n✅ Roster enhancement completed successfully!")
    else:
        print(f"\n❌ Enhancement failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
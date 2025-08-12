#!/usr/bin/env python3

"""
Quick fix for enhanced_comprehensive_hellraiser.py to handle empty picks gracefully
"""

import os
import re

def fix_empty_picks_handling():
    """Fix the ValueError when no picks are generated"""
    
    script_path = "enhanced_comprehensive_hellraiser.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    # Read the script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Find the problematic line and replace it
    old_pattern = r'print\(f"   Score Range: \{min\(p\[\'confidenceScore\'\] for p in analysis_picks\):.1f\}% - \{max\(p\[\'confidenceScore\'\] for p in analysis_picks\):.1f\}%"\)'
    
    new_code = '''if analysis_picks:
            print(f"   Score Range: {min(p['confidenceScore'] for p in analysis_picks):.1f}% - {max(p['confidenceScore'] for p in analysis_picks):.1f}%")
        else:
            print("   Score Range: No picks generated")'''
    
    # Apply the fix
    if old_pattern in content or "min(p['confidenceScore'] for p in analysis_picks)" in content:
        # Use a more flexible replacement approach
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if 'min(p[\'confidenceScore\'] for p in analysis_picks' in line and 'print(' in line:
                # Replace this line with our safer version
                indent = len(line) - len(line.lstrip())
                spacing = ' ' * indent
                fixed_lines.append(f'{spacing}if analysis_picks:')
                fixed_lines.append(f'{spacing}    {line.strip()}')
                fixed_lines.append(f'{spacing}else:')
                fixed_lines.append(f'{spacing}    print("   Score Range: No picks generated")')
            else:
                fixed_lines.append(line)
        
        # Write the fixed content
        backup_path = f"{script_path}.backup_{os.getpid()}"
        os.rename(script_path, backup_path)
        
        with open(script_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✅ Fixed empty picks handling in {script_path}")
        print(f"💾 Backup saved as {backup_path}")
        return True
    else:
        print(f"⚠️  Could not find the problematic line in {script_path}")
        return False

if __name__ == "__main__":
    fix_empty_picks_handling()
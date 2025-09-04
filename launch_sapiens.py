#!/usr/bin/env python3
"""
Launcher for Sapiens Watcher with Syncthing support
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_syncthing_folder():
    """Check if Syncthing folder exists"""
    sync_dir = Path('Confluences')
    if not sync_dir.exists():
        print("❌ Syncthing folder 'Confluences' not found")
        print("💡 Please set up Syncthing and create 'Confluences' folder")
        return False
    return True

def main():
    print(" Sapiens Watcher Launcher")
    print("=" * 30)
    print(f"💻 Platform: {platform.system()}")
    
    if not check_syncthing_folder():
        input("Press Enter to exit...")
        return 1
    
    # Start watcher
    script_dir = Path(__file__).parent
    watcher_script = script_dir / 'python' / 'sapiens_watcher.py'
    
    try:
        subprocess.run([
            sys.executable, str(watcher_script),
            '--watch-dir', 'Confluences/captures',
            '--output-dir', 'output',
            '--model-size', '1b',
            '--device', 'auto'
        ])
        return 0
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
        return 1

if __name__ == '__main__':
    sys.exit(main())


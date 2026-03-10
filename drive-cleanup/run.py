#!/usr/bin/env python3
"""
TAS Drive Cleanup — Master Runner
Execute phases in order: 1 -> 2 -> 3 -> 4 -> 5
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def main():
    if len(sys.argv) < 2:
        print("""
TAS Drive Cleanup — Master Runner
==================================

Usage:
  python run.py phase1          # n8n cleanup
  python run.py phase2          # Create folder structure
  python run.py phase3-test     # Test filing agent (dry run)
  python run.py phase3-once     # Run filing agent once
  python run.py phase3-watch    # Run filing agent (continuous)
  python run.py phase4a         # Audit workspace
  python run.py phase4b         # Migrate _CLAUDE folders
  python run.py phase4c         # Consolidate all old folders
  python run.py phase4d         # Delete empty folder shells
  python run.py phase4e         # Find and archive duplicates
  python run.py phase4f         # Archive old files
  python run.py phase5-once     # Loose file detector (once)
  python run.py phase5-schedule # Loose file detector (daily)
  python run.py gmail-once      # Gmail email filing agent (once)
  python run.py gmail-watch     # Gmail email filing agent (continuous)

IMPORTANT: Execute in order. Phase 1 -> 2 -> 3 -> 4 -> 5.
Phase 6 (Gmail agent) can run independently once Phase 2 folders exist.
""")
        return

    cmd = sys.argv[1].lower()

    if cmd == "phase1":
        from scripts.phase1.n8n_cleanup import run
        run()
    elif cmd == "phase2":
        from scripts.phase2.create_folders import run
        run()
    elif cmd == "phase3-test":
        from scripts.phase3.filing_agent import test_filing
        test_filing()
    elif cmd == "phase3-once":
        from scripts.phase3.filing_agent import run_once
        run_once()
    elif cmd == "phase3-watch":
        from scripts.phase3.filing_agent import run_watcher
        run_watcher()
    elif cmd == "phase4a":
        from scripts.phase4.script_a_audit import run
        run()
    elif cmd == "phase4b":
        from scripts.phase4.script_b_migrate_claude import run
        run()
    elif cmd == "phase4c":
        from scripts.phase4.script_c_consolidate import run
        run()
    elif cmd == "phase4d":
        from scripts.phase4.script_d_delete_empties import run
        run()
    elif cmd == "phase4e":
        from scripts.phase4.script_e_dedup import run
        run()
    elif cmd == "phase4f":
        from scripts.phase4.script_f_archive_old import run
        run()
    elif cmd == "phase5-once":
        from scripts.phase5.loose_file_detector import run_once
        run_once()
    elif cmd == "phase5-schedule":
        from scripts.phase5.loose_file_detector import run_scheduled
        run_scheduled()
    elif cmd == "gmail-once":
        from scripts.phase6.gmail_agent import run_once
        run_once()
    elif cmd == "gmail-watch":
        from scripts.phase6.gmail_agent import run_watcher
        run_watcher()
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'python run.py' without arguments for help.")


if __name__ == "__main__":
    main()

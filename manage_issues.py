import json
import os
import sys
import argparse

# Constants for the file path
ISSUES_FILE = 'fix_items.json'

def load_issues():
    """Loads tasks from the fix_items.json file."""
    if not os.path.exists(ISSUES_FILE):
        return []
    try:
        with open(ISSUES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_issues(issues):
    """Saves tasks back to the fix_items.json file."""
    with open(ISSUES_FILE, 'w') as f:
        json.dump(issues, f, indent=2)

# --- AI / CLI INTERFACE ---

def update_status(task_id, new_status):
    """Machine-executable update for AI tools."""
    tasks = load_issues()
    updated = False
    for task in tasks:
        if task.get('id') == task_id:
            task['status'] = new_status.upper()
            updated = True
            break
    if updated:
        save_issues(tasks)
        print(f"SUCCESS: {task_id} -> {new_status.upper()}")
    else:
        print(f"ERROR: Task {task_id} not found")

def list_tasks_raw(filter_status=None):
    """Clean, pipe-delimited output for AI context parsing."""
    tasks = load_issues()
    for t in tasks:
        if filter_status and t.get('status') != filter_status.upper():
            continue
        print(f"{t['id']}|{t['status']}|{t['task']}")

# --- HUMAN / INTERACTIVE INTERFACE ---

def interactive_menu():
    """Rich UI for human navigation with selection IDs."""
    while True:
        tasks = load_issues()
        print(f"\n{'#':<4} {'ID':<10} {'PH':<3} {'STATUS':<12} {'TASK'}")
        print("-" * 75)
        for idx, t in enumerate(tasks, 1):
            print(f"[{idx:<2}] {t['id']:<10} {t.get('phase','-'):<3} {t['status']:<12} {t['task']}")
        
        choice = input("\nEnter # to Edit, 'q' to Quit: ").strip().lower()
        if choice == 'q': break
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(tasks):
                task = tasks[idx]
                print(f"\n--- {task['id']}: {task['task']} ---")
                print(f"Notes: {task.get('notes')}")
                print("[1] DONE  [2] IN_PROGRESS  [3] OPEN  [0] CANCEL")
                s = input("Select Status: ")
                mapping = {"1": "DONE", "2": "IN_PROGRESS", "3": "OPEN"}
                if s in mapping:
                    task['status'] = mapping[s]
                    save_issues(tasks)

# --- ENTRY POINT ---

def main():
    parser = argparse.ArgumentParser(description="Talus Trace Task Manager (Dual-Mode)")
    parser.add_argument("--list", action="store_true", help="AI: List tasks in machine-readable format")
    parser.add_argument("--update", help="AI: Update task using ID:STATUS")
    
    # If arguments are passed, use AI mode; otherwise, go Interactive
    args = parser.parse_args()

    if args.list:
        list_tasks_raw()
    elif args.update:
        try:
            t_id, status = args.update.split(':')
            update_status(t_id, status)
        except ValueError:
            print("Usage: --update ID:STATUS")
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
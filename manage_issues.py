import json
import os
import sys
import argparse
from datetime import datetime

FILE_PATH = "fix_items.json"
ARCHIVE_PATH = "fix_items_archive.json"

def _load(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            content = f.read()
            if not content.strip():
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []


def _save(path, payload):
    with open(path, 'w') as f:
        json.dump(payload, f, indent=2)


def load_issues():
    return _load(FILE_PATH)


def save_issues(issues):
    _save(FILE_PATH, issues)


def load_archive():
    return _load(ARCHIVE_PATH)


def save_archive(issues):
    _save(ARCHIVE_PATH, issues)

def add_issue(type, title, description):
    issues = load_issues()
    new_id = 1
    if issues:
        new_id = max(i.get('id', 0) for i in issues) + 1
    
    issue = {
        "id": new_id,
        "type": type,
        "title": title,
        "description": description,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "notes": []
    }
    issues.append(issue)
    save_issues(issues)
    print(f"✅ Added issue #{new_id}: [{type.upper()}] {title}")

def add_note(issue_id, note):
    issues = load_issues()
    found = False
    for i in issues:
        if i['id'] == int(issue_id):
            if 'notes' not in i:
                i['notes'] = []
            
            timestamp = datetime.now().isoformat()
            i['notes'].append({
                "timestamp": timestamp,
                "content": note
            })
            found = True
            break
    if found:
        save_issues(issues)
        print(f"✅ Added note to issue #{issue_id}")
    else:
        print(f"❌ Issue #{issue_id} not found.")

def view_issue(issue_id):
    issues = load_issues()
    issue = next((i for i in issues if i['id'] == int(issue_id)), None)
    
    if not issue:
        print(f"❌ Issue #{issue_id} not found.")
        return

    print("\n" + "="*60)
    print(f"#{issue['id']} [{issue['type'].upper()}] {issue['title']}")
    print(f"Status: {issue['status']}")
    print(f"Created: {issue['created_at']}")
    print("-" * 60)
    print(f"Description:\n{issue['description']}")
    
    if 'notes' in issue and issue['notes']:
        print("-" * 60)
        print("Notes:")
        for note in issue['notes']:
            print(f"[{note['timestamp']}] {note['content']}")
    print("="*60 + "\n")

def list_issues():
    issues = load_issues()
    if not issues:
        print("No issues found.")
        return
    
    print(f"{'ID':<4} {'Type':<10} {'Status':<10} {'Title'}")
    print("-" * 60)
    for i in issues:
        print(f"{i['id']:<4} {i['type']:<10} {i['status']:<10} {i['title']}")

def update_status(issue_id, status):
    issues = load_issues()
    found = False
    for i in issues:
        if i['id'] == int(issue_id):
            i['status'] = status
            found = True
            break
    if found:
        save_issues(issues)
        print(f"✅ Updated issue #{issue_id} status to '{status}'")
    else:
        print(f"❌ Issue #{issue_id} not found.")


def archive_closed(statuses=("closed",)):
    issues = load_issues()
    archive = load_archive()

    moved = []
    remaining = []
    now = datetime.now().isoformat()
    status_set = set(statuses)

    for item in issues:
        if item.get("status") in status_set:
            if "archived_at" not in item:
                item["archived_at"] = now
            moved.append(item)
        else:
            remaining.append(item)

    if not moved:
        print("No issues to archive.")
        return

    archive.extend(moved)
    save_archive(archive)
    save_issues(remaining)
    print(f"✅ Archived {len(moved)} issue(s) to {ARCHIVE_PATH}")

def interactive_mode():
    while True:
        print("\n📋 Talus Trace Issue Tracker")
        print("1. List Issues")
        print("2. Add Issue")
        print("3. Update Issue Status")
        print("4. Add Note")
        print("5. View Issue Details")
        print("6. Archive Closed Issues")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == "1":
            print("\n")
            list_issues()
        elif choice == "2":
            print("\n--- Add New Issue ---")
            print("Select Type:")
            print("1. Bug")
            print("2. Feature")
            print("3. Todo")
            t_choice = input("Select type (1-3): ").strip()
            
            type_map = {"1": "bug", "2": "feature", "3": "todo"}
            if t_choice not in type_map:
                print("❌ Invalid selection.")
                continue
            
            i_type = type_map[t_choice]
            title = input("Title: ").strip()
            desc = input("Description: ").strip()
            add_issue(i_type, title, desc)
        elif choice == "3":
            print("\n--- Update Issue Status ---")
            list_issues()
            print("")
            try:
                i_id = int(input("Issue ID: ").strip())
                print("Select New Status:")
                print("1. Open")
                print("2. In-Progress")
                print("3. Staging (Ready for Review)")
                print("4. Resolved")
                print("5. Closed")
                s_choice = input("Select status (1-5): ").strip()
                
                status_map = {"1": "open", "2": "in-progress", "3": "staging", "4": "resolved", "5": "closed"}
                if s_choice not in status_map:
                    print("❌ Invalid selection.")
                    continue
                
                update_status(i_id, status_map[s_choice])
            except ValueError:
                print("❌ Invalid ID.")
        elif choice == "4":
            print("\n--- Add Note ---")
            list_issues()
            try:
                i_id = int(input("Issue ID: ").strip())
                note = input("Note: ").strip()
                add_note(i_id, note)
            except ValueError:
                print("❌ Invalid ID.")
        elif choice == "5":
            print("\n--- View Issue Details ---")
            list_issues()
            try:
                i_id = int(input("Issue ID: ").strip())
                view_issue(i_id)
            except ValueError:
                print("❌ Invalid ID.")
        elif choice == "6":
            archive_closed()
        elif choice == "7":
            print("👋 Bye!")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Manage fix_items.json")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new issue")
    add_parser.add_argument("type", choices=["bug", "feature", "todo"], help="Type of issue")
    add_parser.add_argument("title", help="Short title")
    add_parser.add_argument("description", help="Detailed description")

    list_parser = subparsers.add_parser("list", help="List all issues")

    update_parser = subparsers.add_parser("update", help="Update issue status")
    update_parser.add_argument("id", type=int, help="Issue ID")
    update_parser.add_argument("status", choices=["open", "in-progress", "staging", "resolved", "closed"], help="New status")

    note_parser = subparsers.add_parser("note", help="Add a note to an issue")
    note_parser.add_argument("id", type=int, help="Issue ID")
    note_parser.add_argument("content", help="Note content")

    view_parser = subparsers.add_parser("view", help="View issue details")
    view_parser.add_argument("id", type=int, help="Issue ID")

    archive_parser = subparsers.add_parser("archive", help="Archive closed issues to fix_items_archive.json")
    archive_parser.add_argument("--statuses", nargs="+", default=["closed"], help="Statuses to archive (default: closed)")

    args = parser.parse_args()

    if args.command == "add":
        add_issue(args.type, args.title, args.description)
    elif args.command == "list":
        list_issues()
    elif args.command == "update":
        update_status(args.id, args.status)
    elif args.command == "note":
        add_note(args.id, args.content)
    elif args.command == "view":
        view_issue(args.id)
    elif args.command == "archive":
        archive_closed(tuple(args.statuses))
    else:
        interactive_mode()

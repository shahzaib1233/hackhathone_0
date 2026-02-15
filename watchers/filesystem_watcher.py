"""
File System Watcher for Bronze Tier AI Employee

Monitors the /Inbox folder and moves new files to /Needs_Action with metadata.

Install: pip install watchdog
Run: python watchers/filesystem_watcher.py
Test: Drop any file in /Inbox folder
"""

import os
import time
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class InboxHandler(FileSystemEventHandler):
    """Handles file creation events in the Inbox folder."""
    
    def __init__(self, inbox_dir, needs_action_dir):
        self.inbox_dir = inbox_dir
        self.needs_action_dir = needs_action_dir
    
    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if not event.is_directory:
            self.process_new_file(event.src_path)
    
    def process_new_file(self, file_path):
        """Process a new file by copying it to Needs_Action and creating metadata."""
        try:
            # Get the filename
            filename = os.path.basename(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create new filename with FILE_ prefix
            name, ext = os.path.splitext(filename)
            new_filename = f"FILE_{name}{ext}"
            new_filepath = os.path.join(self.needs_action_dir, new_filename)
            
            # Copy file to Needs_Action with FILE_ prefix
            shutil.copy2(file_path, new_filepath)
            print(f"[INFO] Copied {filename} to {new_filename} in Needs_Action")
            
            # Create metadata .md file with YAML frontmatter
            metadata_filename = f"FILE_{name}_metadata.md"
            metadata_filepath = os.path.join(self.needs_action_dir, metadata_filename)
            
            with open(metadata_filepath, 'w') as meta_file:
                meta_file.write("---\n")
                meta_file.write(f"type: file_drop\n")
                meta_file.write(f"original_name: {filename}\n")
                meta_file.write(f"size: {file_size}\n")
                meta_file.write(f"status: pending\n")
                meta_file.write(f"timestamp: {datetime.now().isoformat()}\n")
                meta_file.write("---\n")
                
            print(f"[INFO] Created metadata file: {metadata_filename}")
            
            # Optionally, remove the original file from Inbox after processing
            # os.remove(file_path)
            # print(f"[INFO] Removed {filename} from Inbox")
            
        except Exception as e:
            print(f"[ERROR] Failed to process file {file_path}: {str(e)}")


def main():
    """Main function to start the file system watcher."""
    # Define directory paths
    project_root = os.path.dirname(os.path.abspath(__file__))  # This will be the watchers directory
    project_root = os.path.dirname(project_root)  # Go up one level to project root
    inbox_dir = os.path.join(project_root, "Inbox")
    needs_action_dir = os.path.join(project_root, "Needs_Action")
    
    # Check if required directories exist
    if not os.path.exists(inbox_dir):
        print(f"[ERROR] Inbox directory does not exist: {inbox_dir}")
        print("[INFO] Please create the Inbox directory first.")
        return
    
    if not os.path.exists(needs_action_dir):
        print(f"[ERROR] Needs_Action directory does not exist: {needs_action_dir}")
        print("[INFO] Please create the Needs_Action directory first.")
        return
    
    # Create the event handler and observer
    event_handler = InboxHandler(inbox_dir, needs_action_dir)
    observer = Observer()
    observer.schedule(event_handler, inbox_dir, recursive=False)
    
    print(f"[INFO] Starting file system watcher...")
    print(f"[INFO] Monitoring: {inbox_dir}")
    print(f"[INFO] Destination: {needs_action_dir}")
    print(f"[INFO] Press Ctrl+C to stop")
    
    observer.start()
    
    try:
        while True:
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        observer.stop()
        print("\n[INFO] Stopping file system watcher...")
    
    observer.join()
    print("[INFO] File system watcher stopped.")


if __name__ == "__main__":
    main()
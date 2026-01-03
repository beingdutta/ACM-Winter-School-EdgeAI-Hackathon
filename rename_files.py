import os

def rename_files_sequentially(directory=".", prefix="file"):
    """
    Renames all files in the specified directory sequentially.
    
    Args:
        directory (str): The path to the directory containing files to rename.
        prefix (str): The prefix for the new file names.
    """
    # Verify directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    # Get list of files
    try:
        files = os.listdir(directory)
    except OSError as e:
        print(f"Error accessing directory: {e}")
        return

    # Filter out directories and keep only files
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    
    # Sort files to ensure deterministic renaming order
    files.sort()
    
    script_name = os.path.basename(__file__)

    count = 1
    for filename in files:
        # Skip this script file if it's in the target directory
        if filename == script_name:
            continue
            
        # Get the file extension
        _, extension = os.path.splitext(filename)
        
        # Create new filename with padding (e.g., file_001.txt)
        new_filename = f"{prefix}_{count:03d}{extension}"
        
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_filename)
        
        # Prevent overwriting existing files
        if os.path.exists(new_path):
            print(f"Skipping {filename}: Target {new_filename} already exists.")
            continue

        try:
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")
            count += 1
        except OSError as e:
            print(f"Error renaming {filename}: {e}")

if __name__ == "__main__":
    target_dir = input("Enter directory path (leave empty for current): ").strip() or "."
    file_prefix = input("Enter filename prefix (default 'file'): ").strip() or "file"
    rename_files_sequentially(target_dir, file_prefix)
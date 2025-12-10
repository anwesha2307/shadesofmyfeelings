import os
import shutil
import subprocess
import sys

def main():
    # 1. Get repo path dynamically (folder where this script lives)
    repo_path = os.path.dirname(os.path.abspath(__file__))

    # 2. Ask user for source folder name
    src = input("Enter the source folder name to copy from (example: 3): ").strip()
    src_folder = os.path.join(repo_path, src)

    # 3. Ask user for new folder name
    dst = input("Enter the NEW folder name to create (example: 4): ").strip()
    dst_folder = os.path.join(repo_path, dst)

    # 4. Validate source folder exists
    if not os.path.isdir(src_folder):
        print(f"Source folder does not exist: {src_folder}")
        sys.exit(1)

    # 5. Check if destination folder already exists
    if os.path.exists(dst_folder):
        print(f"Destination folder already exists: {dst_folder}")
        sys.exit(1)

    # 6. Copy source → destination
    print(f"Copying '{src}' → '{dst}' ...")
    shutil.copytree(src_folder, dst_folder)
    print("Copy complete!")

    # 7. Git: add new folder
    print(f"Running: git add {dst}")
    subprocess.check_call(["git", "add", dst], cwd=repo_path)

    # 8. Commit
    commit_message = f"Copy folder {src} to {dst}"
    print(f"Running: git commit -m \"{commit_message}\"")
    subprocess.check_call(["git", "commit", "-m", commit_message], cwd=repo_path)

    # 9. Push
    print("Running: git push origin main")
    subprocess.check_call(["git", "push", "origin", "main"], cwd=repo_path)

    print(f"All done! Folder '{dst}' created, committed, and pushed.")

if __name__ == "__main__":
    main()

import os
import shutil
import subprocess
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python copy_and_commit.py <source_folder> <dest_folder>")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]

    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    src_folder = os.path.join(repo_path, src)
    dst_folder = os.path.join(repo_path, dst)

    if not os.path.isdir(src_folder):
        print(f"Source folder does not exist: {src_folder}")
        sys.exit(1)

    if os.path.exists(dst_folder):
        print(f"Destination folder already exists: {dst_folder}")
        sys.exit(1)

    print(f"Copying '{src}' → '{dst}' ...")
    shutil.copytree(src_folder, dst_folder)
    print("Copy complete.")

    # Git add/commit/push
    subprocess.check_call(["git", "config", "user.name", "automation-bot"])
    subprocess.check_call(["git", "config", "user.email", "bot@example.com"])

    subprocess.check_call(["git", "add", dst], cwd=repo_path)

    commit_message = f"Copy folder {src} to {dst}"
    subprocess.check_call(["git", "commit", "-m", commit_message], cwd=repo_path)
    subprocess.check_call(["git", "push", "origin", "main"], cwd=repo_path)

    print("All done! Folder copied, committed, and pushed.")

if __name__ == "__main__":
    main()

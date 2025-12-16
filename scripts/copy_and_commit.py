import os
import shutil
import subprocess
import sys


def main():
    # Expected usage:
    # python copy_and_commit.py <repo_path> <source_folder> <dest_folder>
    if len(sys.argv) != 4:
        print("Usage: python copy_and_commit.py <repo_path> <source_folder> <dest_folder>")
        sys.exit(1)

    repo_path = sys.argv[1]
    src = sys.argv[2]
    dst = sys.argv[3]

    # Make repo_path absolute (so it works no matter where you run from)
    repo_path = os.path.abspath(repo_path)

    # Build absolute paths to folders inside the target repo
    src_folder = os.path.join(repo_path, src)
    dst_folder = os.path.join(repo_path, dst)

    # Validate source exists and is a directory
    if not os.path.isdir(src_folder):
        print(f"Source folder does not exist: {src_folder}")
        sys.exit(1)

    # Prevent overwriting destination
    if os.path.exists(dst_folder):
        print(f"Destination folder already exists: {dst_folder}")
        sys.exit(1)

    print(f"Copying '{src}' → '{dst}' inside repo: {repo_path}")
    shutil.copytree(src_folder, dst_folder)
    print("Copy complete.")

    # Git add/commit inside the target repo
    subprocess.check_call(["git", "config", "user.name", "automation-bot"], cwd=repo_path)
    subprocess.check_call(["git", "config", "user.email", "bot@example.com"], cwd=repo_path)

    subprocess.check_call(["git", "add", dst], cwd=repo_path)

    commit_message = f"Copy folder {src} to {dst}"
    subprocess.check_call(["git", "commit", "-m", commit_message], cwd=repo_path)

    print("All done! Folder copied and committed.")


if __name__ == "__main__":
    main()

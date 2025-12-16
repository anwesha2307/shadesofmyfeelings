import os
import shutil
import subprocess
import sys


def resolve_repo_path(repo_path: str) -> str:
    """
    If repo_path is relative, resolve it relative to GitHub Actions workspace
    (GITHUB_WORKSPACE) when available, otherwise resolve relative to cwd.
    """
    if os.path.isabs(repo_path):
        return repo_path

    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        return os.path.abspath(os.path.join(workspace, repo_path))

    return os.path.abspath(repo_path)


def main():
    # Usage:
    # python copy_and_commit.py <repo_path> <source_folder> <dest_folder>
    if len(sys.argv) != 4:
        print("Usage: python copy_and_commit.py <repo_path> <source_folder> <dest_folder>")
        sys.exit(1)

    repo_path = resolve_repo_path(sys.argv[1])
    src = sys.argv[2]
    dst = sys.argv[3]

    # Sanity check: repo_path must exist
    if not os.path.isdir(repo_path):
        print(f"Repo path does not exist or is not a directory: {repo_path}")
        sys.exit(1)

    # Sanity check: must be a git repo (actions/checkout creates .git by default)
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.exists(git_dir):
        print(f"Not a git repository (missing .git): {repo_path}")
        print("Tip: ensure the target repo is checked out with actions/checkout and path is correct.")
        sys.exit(1)

    src_folder = os.path.join(repo_path, src)
    dst_folder = os.path.join(repo_path, dst)

    if not os.path.isdir(src_folder):
        print(f"Source folder does not exist: {src_folder}")
        sys.exit(1)

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

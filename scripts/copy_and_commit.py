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


def safe_join(base_dir: str, user_path: str) -> str:
    """
    Join base_dir + user_path safely, preventing path traversal outside base_dir.
    """
    # Treat empty or "." as base_dir
    if user_path.strip() in ("", "."):
        joined = os.path.abspath(base_dir)
    else:
        joined = os.path.abspath(os.path.join(base_dir, user_path))

    base_abs = os.path.abspath(base_dir)

    # Ensure joined is within base_abs
    common = os.path.commonpath([base_abs, joined])
    if common != base_abs:
        raise ValueError(f"Unsafe path (escapes repo root): {user_path}")

    return joined


def main():
    # Usage:
    # python copy_and_commit.py <repo_path> <source_folder> <destination_path> <dest_folder>
    if len(sys.argv) != 5:
        print("Usage: python copy_and_commit.py <repo_path> <source_folder> <destination_path> <dest_folder>")
        sys.exit(1)

    repo_path = resolve_repo_path(sys.argv[1])
    src = sys.argv[2]
    destination_path = sys.argv[3]
    dest_folder_name = sys.argv[4]

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

    # Resolve source folder safely within repo
    try:
        src_folder = safe_join(repo_path, src)
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    if not os.path.isdir(src_folder):
        print(f"Source folder does not exist: {src_folder}")
        sys.exit(1)

    # Resolve destination parent path safely within repo, then final destination folder
    try:
        dest_parent_abs = safe_join(repo_path, destination_path)
        dst_folder_abs = safe_join(dest_parent_abs, dest_folder_name)
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    # Compute git-relative path for add/commit messaging
    dst_folder_rel = os.path.relpath(dst_folder_abs, repo_path)

    # Make sure parent exists
    os.makedirs(dest_parent_abs, exist_ok=True)

    if os.path.exists(dst_folder_abs):
        print(f"Destination folder already exists: {dst_folder_abs}")
        sys.exit(1)

    print(f"Copying '{src}' → '{dst_folder_rel}' inside repo: {repo_path}")
    shutil.copytree(src_folder, dst_folder_abs)
    print("Copy complete.")

    # Git add/commit inside the target repo
    subprocess.check_call(["git", "config", "user.name", "automation-bot"], cwd=repo_path)
    subprocess.check_call(["git", "config", "user.email", "bot@example.com"], cwd=repo_path)

    subprocess.check_call(["git", "add", dst_folder_rel], cwd=repo_path)

    commit_message = f"Copy folder {src} to {dst_folder_rel}"
    subprocess.check_call(["git", "commit", "-m", commit_message], cwd=repo_path)

    print("All done! Folder copied and committed.")


if __name__ == "__main__":
    main()

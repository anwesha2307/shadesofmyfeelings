from __future__ import annotations

import argparse
from pathlib import Path
import sys
import pandas as pd
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString


def read_key_values(input_path: Path, key_col: str, value_col: str, sheet: str | None) -> dict[str, str]:
    suffix = input_path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(input_path, sheet_name=sheet, dtype=str)
    elif suffix == ".csv":
        df = pd.read_csv(input_path, dtype=str)
    else:
        raise ValueError(f"Unsupported input type: {suffix}. Use .csv, .xlsx, or .xls")

    if key_col not in df.columns or value_col not in df.columns:
        raise ValueError(
            f"Missing columns. Found: {list(df.columns)}. "
            f"Expected key_col='{key_col}', value_col='{value_col}'."
        )

    df = df[[key_col, value_col]].copy()
    df[key_col] = df[key_col].astype(str).str.strip()
    df[value_col] = df[value_col].fillna("").astype(str)

    df = df[df[key_col] != ""]

    # If duplicate keys exist, later rows override earlier ones
    return dict(zip(df[key_col], df[value_col]))


def load_yaml(yaml: YAML, path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)
        return {} if data is None else data


def dump_yaml(yaml: YAML, path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


def update_one_yaml(
    yaml_path: Path,
    updates: dict[str, str],
    add_missing: bool,
) -> bool:
    """
    Returns True if file changed, False otherwise.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    before = load_yaml(yaml, yaml_path)

    # Work on a copy-like structure (ruamel uses CommentedMap; still ok)
    after = before

    changed = False
    for k, v in updates.items():
        if (k in after) or add_missing:
            new_val = SingleQuotedScalarString(v)
            if k not in after or str(after[k]) != str(new_val):
                after[k] = new_val
                changed = True

    if changed:
        dump_yaml(yaml, yaml_path, after)

    return changed


def resolve_targets(targets: list[str]) -> list[Path]:
    """
    Targets can be:
      - file paths: config/app.yml
      - directories: configs/
      - glob patterns: configs/**/*.yml
    """
    resolved: list[Path] = []

    for t in targets:
        p = Path(t)

        # Glob pattern if it contains wildcard chars
        if any(ch in t for ch in ["*", "?", "["]):
            resolved.extend([Path(x) for x in sorted(Path().glob(t))])
            continue

        if p.is_dir():
            resolved.extend(sorted(list(p.rglob("*.yml")) + list(p.rglob("*.yaml"))))
            continue

        # Regular file
        resolved.append(p)

    # De-duplicate while preserving order
    seen = set()
    uniq: list[Path] = []
    for p in resolved:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)

    return uniq


def main() -> int:
    parser = argparse.ArgumentParser(description="Update one or many YAML files using key/value data from CSV/Excel.")
    parser.add_argument("--input", required=True, help="Path to input CSV/XLSX with key/value columns.")
    parser.add_argument("--targets", required=True, nargs="+",
                        help="YAML file(s), directory(ies), or glob(s) to update. "
                             "Examples: config/app.yml configs/ 'configs/**/*.yml'")
    parser.add_argument("--key-col", default="key", help="Column name for keys (default: key)")
    parser.add_argument("--value-col", default="value", help="Column name for values (default: value)")
    parser.add_argument("--sheet", default=None, help="Excel sheet name (optional). Ignored for CSV.")
    parser.add_argument("--no-add-missing", action="store_true",
                        help="If set, do NOT add keys that don't already exist in the YAML.")
    parser.add_argument("--fail-if-no-changes", action="store_true",
                        help="If set, exit non-zero when nothing was updated (useful for CI).")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2

    updates = read_key_values(input_path, args.key_col, args.value_col, args.sheet)

    yaml_files = resolve_targets(args.targets)
    if not yaml_files:
        print("ERROR: no YAML targets found from --targets", file=sys.stderr)
        return 2

    total_changed = 0
    for y in yaml_files:
        try:
            changed = update_one_yaml(
                yaml_path=y,
                updates=updates,
                add_missing=not args.no_add_missing,
            )
            if changed:
                total_changed += 1
                print(f"UPDATED: {y}")
            else:
                print(f"NO CHANGE: {y}")
        except Exception as e:
            print(f"ERROR updating {y}: {e}", file=sys.stderr)
            return 1

    print(f"\nDone. Files changed: {total_changed} / {len(yaml_files)}")

    if args.fail_if_no_changes and total_changed == 0:
        print("ERROR: no files changed (fail-if-no-changes enabled)", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Lint Sigma rules — quick check for required fields + parseable YAML."""
import sys
from pathlib import Path
import yaml

REQUIRED = {"title", "id", "description", "logsource", "detection", "level"}

def main(directory: str) -> int:
    p = Path(directory)
    if not p.exists():
        print(f"Directory not found: {p}")
        return 0  # nothing to validate
    failed = 0
    for f in sorted(p.glob("*.yml")):
        try:
            doc = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            print(f"FAIL  {f.name}: invalid YAML: {e}")
            failed += 1
            continue
        missing = REQUIRED - set(doc.keys())
        if missing:
            print(f"FAIL  {f.name}: missing required fields: {missing}")
            failed += 1
        else:
            print(f"OK    {f.name}")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "detections/sigma"))

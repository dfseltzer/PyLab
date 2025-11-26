"""
Validate SCPI command set JSON files against the SCPI_Schema.json.

Usage:
    python -m pylab.cli.validate_scpi [path ...]

If no paths are provided, all *.json files under pylab/data are validated.
"""

import json
import sys
from pathlib import Path

import jsonschema


def load_schema(schema_path: Path):
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(path: Path, schema) -> list[str]:
    errors = []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as ve:
        errors.append(f"{path}: {ve.message}")
    except Exception as e:
        errors.append(f"{path}: failed to load/parse ({e})")
    return errors


def find_scpi_files(root: Path):
    return sorted(root.glob("*.json"))


def main(argv=None):
    argv = argv or sys.argv[1:]
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "pylab" / "data"
    schema_path = data_dir / "SCPI_Schema.json"

    if not schema_path.exists():
        print(f"Schema not found at {schema_path}")
        return 1

    schema = load_schema(schema_path)

    targets = [Path(arg) for arg in argv] if argv else find_scpi_files(data_dir)

    all_errors: list[str] = []
    for path in targets:
        if path.is_dir():
            for sub in sorted(path.glob("*.json")):
                all_errors.extend(validate_file(sub, schema))
        else:
            all_errors.extend(validate_file(path, schema))

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("All SCPI JSON files validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

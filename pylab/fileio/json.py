from pathlib import Path
from ..utilities import load_data_file

def validate_scpi_command_file(path: str | Path) -> tuple[bool, list[str]]:
    """
    Validate a SCPI command-set JSON file against pylab/data/SCPI_Schema.json.
    Returns (True, []) when valid, otherwise (False, [error messages]).

    Inputs:
    - path: Path to the SCPI command-set JSON file to validate, or name 
    of a data file in pylab/data/ to load.
    """
    schema = load_data_file("SCPI_Schema")

    errors: list[str] = []
    target = Path(path)
    try:
        data = load_data_file(target.name if target.name else str(target))
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as ve:
        errors.append(f"{target}: {ve.message}")
    except Exception as e:
        errors.append(f"{target}: failed to load/parse ({e})")

    return len(errors) == 0, errors

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed; SCPI command file validation will be unavailable.")
    def validate_scpi_command_file(*args, **kwargs):
        raise ImportError("jsonschema not installed; SCPI command file validation is unavailable.")
"""Export OpenAPI schema to JSON file."""

import json
from pathlib import Path

from app.main import create_app


def export_openapi_schema(output_path: str = "../docs/openapi.json") -> None:
    """Export the OpenAPI schema to a JSON file.

    Args:
        output_path: Path to write the OpenAPI JSON file (relative to api/ directory)
    """
    app = create_app()
    openapi_schema = app.openapi()

    # Resolve path relative to this script's directory
    script_dir = Path(__file__).parent
    output_file = (script_dir / ".." / ".." / output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write schema to file
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✓ OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    export_openapi_schema()

"""Generate docs from configuration files."""

import typing
from typing import get_origin
from types import UnionType
from pathlib import Path

from matbii.config import Configuration


def get_type_name(_type: type):
    """Get the name of a type (and handle union types/nested types)."""
    if get_origin(_type) is UnionType:
        return str(_type)
    if hasattr(_type, "__args__"):
        return (
            f"{_type.__name__}[{','.join([get_type_name(t) for t in _type.__args__])}]"
        )
    return _type.__name__


def generate_docs(model):
    """Generate documentation from Configuration classes."""
    name = model.__name__.replace("Configuration", "")
    result = f"### {name} Configuration\n"
    for field_name, field_model in model.__fields__.items():
        if not field_model.is_required():
            default = field_model.get_default()
            default = f'"{default}"' if isinstance(default, str) else default
            default = f" Defaults to: `{default}`."
        else:
            default = ""
        result += f"- `{field_name} ({get_type_name(field_model.annotation)}{', optional' if field_model.is_required() else ''})`: {field_model.description}{default}\n"

    for m in typing.get_type_hints(model).values():
        if hasattr(m, "__fields__"):
            result += "\n"
            result += generate_docs(m)

    return result


if __name__ == "__main__":
    DOCS_PATH = (Path(__file__).parent.parent.parent / "docs").resolve()
    print(DOCS_PATH)

    with open((DOCS_PATH / "configuration_doc.md").as_posix(), "w") as f:
        f.write(generate_docs(Configuration))

    with open((DOCS_PATH / "configuration_default.md").as_posix(), "w") as f:
        f.write(Configuration().model_dump_json(indent=1))

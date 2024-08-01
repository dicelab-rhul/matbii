"""Generate docs from configuration files."""

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


if __name__ == "__main__":
    DOCS_PATH = (Path(__file__).parent.parent.parent / "docs").resolve()

    from matbii.config import Configuration

    def schema_to_md(name: str, schema: dict):
        """Convert json schema to markdown."""
        name = name.replace("Configuration", " Configuration")
        markdown = f"### {name}\n"
        markdown += f"{schema['description']}\n\n"
        # TODO include description?

        for name, property in schema["properties"].items():
            if "$ref" in property:
                # this is a reference type
                type = (
                    property["$ref"]
                    .rsplit("/")[-1]
                    .replace("Configuration", " Configuration")
                )
                link = f"#{type}".replace(" ", "-").lower()
                markdown += f"- `{name} (`[`{type}`]({link})`)`\n"
                continue

            type = property.get("type", "")

            if not type:
                type = " | ".join([t["type"] for t in property.get("anyOf")])
            title = name  # property.get("title", name.capitalize())
            description = property.get("description")
            if not description:
                description = "<MISSING DOC>"

            if "default" in property:
                default = property["default"]
                if default is None:
                    default = "null"
                elif type == "string":
                    default = f"'{default}'"
                markdown += f"- `{title} ({type}) = {default}:`\n"
            else:
                markdown += f"- `{title} ({type})` _required_:\n"
            markdown += f"{description}\n"
        return markdown

    for name, field in Configuration.model_fields.items():
        md = schema_to_md(
            field.annotation.__name__, field.annotation.model_json_schema()
        )
        admon = f'??? quote "example.json" \n```\n"{name}": {field.annotation().model_dump_json(indent=2)}\n```'.replace(
            "\n", "\n    "
        )
        print(admon)
        md = schema_to_md("Configuration", Configuration.model_json_schema())

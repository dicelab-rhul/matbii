"""mkdocs macros."""

import subprocess
import re
import griffe
from itertools import islice
from typing import Any
from pydantic import BaseModel
from collections.abc import Generator

from matbii.config import Configuration
from icua.agent import attempt  # noqa # check that this is at the path we expect


def get_attempts(fqcn: str) -> Generator[str, Any, None]:
    """Get all the attempt methods (those annotated with "@attempt") for the given class.

    The class will typically be an actuator.

    Args:
        fqcn (str): the fully qualified path of the class.

    Yields:
        Generator[str, Any, None]: each attempt method signature NAME(*PARAMS)
    """
    ATTEMPT_DECORATOR_PATH = "icua.agent.attempt"  # if this moves we are in trouble...

    for member_name, member in griffe.load(fqcn, resolve_aliases=True).members.items():
        if any(
            d.value.canonical_path == ATTEMPT_DECORATOR_PATH for d in member.decorators
        ):
            # has the attempt decorator, this is an attempt method!
            def get_params_doc(member):
                params = member.parameters
                for param in islice(params, 1, None, None):
                    yield f"{param.name}: {param.annotation}"

            doc = f"`{member_name}({', '.join(get_params_doc(member))})`"
            yield doc


def options_to_markdown(lines):
    """Convert table of options to markdown list (deprecated)."""
    # List to store each row of the table
    rows = []

    # Temporarily store command and accumulate description lines
    current_command = None
    description_lines = []

    # Process each line
    for line in lines:
        line = line.strip()
        if line.startswith("-"):
            # If there's a current command, save it before starting a new one
            if current_command:
                # Join accumulated descriptions
                description = " ".join(description_lines).strip()
                # Extract command details
                match = re.match(r"(-\w\s\w+),\s(--\w+\s\w+)", current_command)
                if match:
                    short, long = match.groups()
                    short_opt, short_arg = short.split(" ")
                    long_opt, long_arg = long.split(" ")
                    # Append the formatted row to the list
                    rows.append(
                        f"| `{short_opt} {short_arg}`, `{long_opt} {long_arg}` | {description} |"
                    )
                # Reset description
                description_lines = []

            # Update current command
            current_command = line
        else:
            # Accumulate description lines
            description_lines.append(line)

    # Handle the last command and description
    if current_command and description_lines:
        description = " ".join(description_lines).strip()
        match = re.match(r"(-\w\s\w+),\s(--\w+\s\w+)", current_command)
        if match:
            short, long = match.groups()
            short_opt, short_arg = short.split(" ")
            long_opt, long_arg = long.split(" ")
            rows.append(
                f"| `{short_opt} {short_arg}`, `{long_opt} {long_arg}` | {description} |"
            )

    # Define the header and separator for the Markdown table
    header = "| Option  | Description |"
    separator = "|---------|-------------|"

    # Join all the parts into the final table
    return f"{header}\n{separator}\n" + "\n".join(rows)


def schema_to_md_table(name: str, schema: dict):
    """Convert json schema to markdown table."""
    markdown = f"## {name}\n"
    markdown += f"{schema['description']}\n\n"
    # TODO include description?
    markdown += "| Property | Type | Default | Description |\n"
    markdown += "|----------|------|---------|-------------|\n"
    for name, property in schema["properties"].items():
        type = property.get("type", "")
        if not type:
            type = " | ".join([t["type"] for t in property.get("anyOf")])
        title = name  # property.get("title", name.capitalize())
        if "default" in property:
            default = property["default"]
            if default is None:
                default = "null"
            elif type == "string":
                default = f"'{default}'"
            default = f"`{default}`"
        else:
            default = "_required_"
        description = property.get("description", "<MISSING DOC>")
        markdown += f"|`{title}` | `{type}` | {default} | {description} |\n"
    return markdown


def schema_to_md(schema: dict, indent: str = ""):
    """Convert json schema to markdown."""
    markdown = []
    # markdown.append(f"{title_prefix} {name}")
    # markdown.append(f"{schema['description']}\n")
    # TODO include description?
    defs = schema.get("$defs", dict())

    def _unpack_types(types):
        for t in types:
            if "$ref" in t:
                yield t["$ref"].rsplit("/")[-1]
            elif "type" in t:
                yield t["type"]

    for name, property in schema["properties"].items():
        if "$ref" in property:
            # this is a reference type
            type = property["$ref"].rsplit("/")[-1]
            markdown.append(f"- `{name}`: {type}")
            continue

        type = property.get("type", None)
        types = []
        if type is None and "anyOf" in property:
            types = list(_unpack_types(property.get("anyOf")))
            type = " | ".join(types)
        elif type is None and "allOf" in property:
            types = list(_unpack_types(property.get("allOf")))
            type = " | ".join(types)

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
            markdown.append(f"- `{title} ({type}) = {default}:`")
        else:
            markdown.append(f"- `{title} ({type})` _required_:")
        markdown.append(f"{description}\n")

        # render sub types
        for type in types:
            tproperty = defs.get(type, None)
            if tproperty:
                markdown.append("    " + schema_to_md(tproperty, indent + "    "))
    return f"\n{indent}".join(markdown)


def configuration_to_md(
    base_model: type[BaseModel], indent: int = 1, show_example: bool = True
):
    """Compile the default entry point config as markdown with examples."""
    result = []

    # main_schema = Configuration.model_json_schema()
    markdown = ""  # "## Main Configuration\n\n"
    # markdown += f"{main_schema['description']}\n\n"
    # markdown += schema_to_md(main_schema)
    result.append(markdown)
    for name, field in base_model.model_fields.items():
        schema = field.annotation.model_json_schema()
        markdown = f"{schema['description']}\n\n" + schema_to_md(schema)
        if show_example:
            example = admonition(
                "Example",
                f'```\n"{name}": {field.annotation().model_dump_json(indent=indent+1)}\n```',
                admon="example",
            )
        markdown = admonition(
            field.annotation.__name__, markdown + example, admon="info", indent=indent
        )
        result.append(markdown)
        # admon = f'??? quote "Example" \n```\n"{name}": {field.annotation().model_dump_json(indent=2)}\n```'.replace(
        #     "\n", "\n    "
        # )

    # this is the default config file!
    result.append(
        "The default configuration file can be found below, you can simply copy it and modify as needed."
    )
    admon = f'??? example "default-configuration.json"\n```\n{Configuration().model_dump_json(indent=2)}\n```'.replace(
        "\n", "\n    "
    )
    result.append(admon)
    result = "\n\n".join(result)
    return result


def admonition(title: str, data: str, indent: int = 1, admon: str = "quote"):
    """Quick admonition macro."""
    indent: str = "\n" + "    " * indent
    return indent.join(f'??? {admon} "{title}"\n\n{data}\n'.split("\n"))


def define_env(env):
    """Entry point for mkdocs macros."""

    @env.macro
    def list_attempt_methods(fqcn: str):
        """Create a list of all the attempt methods for the given (Actuator) class."""
        return "- " + "\n- ".join(get_attempts(fqcn))

    @env.macro
    def cmd_help():
        """Get command line options for matbii."""
        # Command to run Python module as a script
        command = ["python", "-m", "matbii", "--help"]
        # Run the command
        stdout = subprocess.run(command, text=True, capture_output=True).stdout
        lines = stdout.split("options:")[1].splitlines()[2:]
        return options_to_markdown(lines)

    @env.macro
    def admonition(title: str, data: str, indent: int = 1, admon: str = "quote"):
        """Quick admonition macro."""
        indent: str = "\n" + "    " * indent
        return indent.join(f'??? {admon} "{title}"\n\n{data}\n'.split("\n"))

    @env.macro
    def indent(data: str, indent: int = 1):
        """Indent a markdown string, this is useful when using macros inside admonitions."""
        indent: str = "\n" + "    " * indent
        return data.replace("\n", indent)

    @env.macro
    def default_entry_config():
        return configuration_to_md(Configuration)


if __name__ == "__main__":
    # print(configuration_to_md())
    result = configuration_to_md(Configuration)
    print(result)

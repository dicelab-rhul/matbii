"""mkdocs macros."""

import subprocess
import re
from matbii.config import Configuration


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

    for name, property in schema["properties"].items():
        if "$ref" in property:
            # this is a reference type
            type = (
                property["$ref"].rsplit("/")[-1]
                # .replace("Configuration", " Configuration")
            )
            # link = f"#{type}".replace(" ", "-").lower()
            markdown.append(f"- `{name}`: {type}")
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
            markdown.append(f"- `{title} ({type}) = {default}:`")
        else:
            markdown.append(f"- `{title} ({type})` _required_:")
        markdown.append(f"{description}\n")
    return f"\n{indent}".join(markdown)


def define_env(env):
    """Entry point for mkdocs macros."""

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
    def admonition(title: str, data: str, indent: int = 1):
        indent: str = "\n" + "    " * indent
        return indent.join(f'??? quote "{title}"\n\n{data}\n'.split("\n"))

    @env.macro
    def default_entry_config():
        result = []
        main_schema = Configuration.model_json_schema()
        markdown = "## Main Configuration\n\n"
        markdown += f"{main_schema['description']}\n\n"
        # markdown += schema_to_md(main_schema)
        result.append(markdown)
        for name, field in Configuration.model_fields.items():
            schema = field.annotation.model_json_schema()
            markdown = f"{schema['description']}\n\n" + schema_to_md(schema)
            example = admonition(
                "Example",
                f'```\n"{name}": {field.annotation().model_dump_json(indent=2)}\n```',
            )
            markdown = admonition(field.annotation.__name__, markdown + example)
            result.append(markdown)
            # admon = f'??? quote "Example" \n```\n"{name}": {field.annotation().model_dump_json(indent=2)}\n```'.replace(
            #     "\n", "\n    "
            # )

        # this is the default config file!
        result.append(
            "The default configuration file can be found below, you can simply copy it and modify as needed."
        )
        admon = f'??? quote "default-configuration.json"\n```\n{Configuration().model_dump_json(indent=2)}\n```'.replace(
            "\n", "\n    "
        )
        result.append(admon)
        result = "\n\n".join(result)
        return result

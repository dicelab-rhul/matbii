def table_to_list(markdown_table):
    """Converts a Markdown table into a Markdown list with each row formatted as: 'Field Name (Type) = Default: Description'."""
    # Split the table into lines and remove the header and separator lines
    lines = markdown_table.strip().split("\n")[2:]

    # Prepare the markdown list
    markdown_list = []

    # Process each line of the table
    for line in lines:
        # Extract columns by splitting line by '|', and strip whitespace from each column
        columns = [col.strip() for col in line.split("|")[1:-1]]
        # Extract individual column data
        field_name = columns[0]
        field_type = columns[1]
        default_value = columns[2]
        description = columns[3]

        # Format the list item
        list_item = (
            f"    - `{field_name} ({field_type}) = {default_value}:` {description}"
        )
        markdown_list.append(list_item)

    return "\n".join(markdown_list)


with open(
    "C:/Users/brjw/Documents/repos/dicelab/matbii/docs/resource_management_config.md"
) as f:
    rm = table_to_list(f.read())

    with open(
        "C:/Users/brjw/Documents/repos/dicelab/matbii/docs/getting_started/resource_management_config.md",
        "w",
    ) as f:
        f.write(rm)


with open(
    "C:/Users/brjw/Documents/repos/dicelab/matbii/docs/system_monitoring_config.md"
) as f:
    rm = table_to_list(f.read())

    with open(
        "C:/Users/brjw/Documents/repos/dicelab/matbii/docs/getting_started/system_monitoring_config.md",
        "w",
    ) as f:
        f.write(rm)


with open("C:/Users/brjw/Documents/repos/dicelab/matbii/docs/tracking_config.md") as f:
    rm = table_to_list(f.read())

    with open(
        "C:/Users/brjw/Documents/repos/dicelab/matbii/docs/getting_started/tracking_config.md",
        "w",
    ) as f:
        f.write(rm)

"""Script to get svg image for each task."""

import json
from pathlib import Path
from jinja2 import FileSystemLoader, Environment
import matbii.tasks.resource_management  # noqa # required import for cerberus ruleset
from star_ray.utils._templating import Validator

root_path = "C:/Users/brjw/Documents/repos/dicelab/matbii/matbii/tasks/"
tasks = ["resource_management", "tracking", "system_monitoring"]

for task in tasks:
    path = Path(root_path, task, task).with_suffix(".schema.json")
    # Load schema from a JSON file
    with open(path.as_posix()) as schema_file:
        schema = json.load(schema_file)
        v = Validator(schema)
        context = v.normalized({})

    file_loader = FileSystemLoader(path.parent.as_posix())
    env = Environment(loader=file_loader)
    template = env.get_template(path.with_name(task).with_suffix(".svg.jinja").name)
    result = template.render(context)

    out_path = (Path(__file__).parent / task).with_suffix(".svg")
    with open(out_path.as_posix(), "w") as f:
        f.write(result)

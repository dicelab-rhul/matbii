from cerberus import Validator, rules_set_registry

rules_set_registry.add(
    "hex_color",
    {"type": "string", "regex": r"^#?[0-9a-fA-F]+$", "default": "#ff69b4"},
)

schema = {
    "foo": {"schema": "hex_color"},
    "foop": {"schema": "hex_color", "default": "#ffffff"},
    "bar": {"type": "integer"},
    "baz": {"type": "dict", "schema": {"a": {"type": "integer"}}},
    # "bar": {"type": "integer", "required": True},
}

v = Validator(schema)

document = {"foo": "#ff9900", "bar": 10, "baz": {"a": 10}}


if v.validate(document):
    result = v.normalized(document)
    print(f"{result} is valid.")
else:
    print(f"Invalid.", v.errors)

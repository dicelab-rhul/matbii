import deepmerge

from deepmerge import always_merger

base = {"foo": ["bar"]}
next = {"foo": ["baz"]}

expected_result = {"foo": ["bar", "baz"]}
result = always_merger.merge(base, next)


assert expected_result == result


base = {"foo": {"a": "bar", "b": "faz"}}
next = {"foo": {"a": "baz"}}

expected_result = {"foo": {"a": "baz", "b": "faz"}}
result = always_merger.merge(base, next)
print(result)
assert expected_result == result

import griffe

cls_docs = griffe.load(
    "icua.event.MouseButtonEvent", resolve_aliases=True, resolve_external=True
)


cls_docs = griffe.load(
    "matbii.config.LoggingConfiguration", resolve_aliases=True, resolve_external=True
)


def get_pydantic_attributes(path: str):
    def _resolve_attribute(alias):
        while alias.is_alias:
            alias = alias.target
        return alias

    def _resolve_annotation(annotation):
        for x in annotation.iterate():
            if isinstance(x, str):
                yield x
            elif isinstance(x, griffe.ExprName):
                yield x.name
            else:
                raise ValueError(f"Unknown annotation element: {x}")

    def _attributes_from_docstring(cls_docs: griffe.Alias, parser: str = "google"):
        kind = griffe.DocstringSectionKind.attributes
        attrs = next(
            filter(lambda x: x.kind == kind, cls_docs.docstring.parse(parser)), None
        )
        if attrs:
            for attr in attrs.value:
                yield dict(
                    name=attr.name,
                    description=attr.description,
                    annotation=str(attr.annotation).removesuffix("[").removeprefix("]"),
                )

    def _resolve_attributes_from_docstring(cls_docs, parser: str = "google"):
        cls_docs = griffe.load(path, resolve_aliases=True, resolve_external=True)
        attrs = {
            cls_docs.path: list(_attributes_from_docstring(cls_docs, parser=parser))
        }
        for base in cls_docs.resolved_bases:
            attrs[base.path] = list(_attributes_from_docstring(base, parser=parser))
        return attrs

    def _resolve_attributes(cls_docs, parser: str = "google"):
        # attrs = {}
        for name, member in cls_docs.all_members.items():
            attr = _resolve_attribute(member)
            if attr.is_attribute:
                print(attr.as_dict())
                # print(attr.annotation.is_classvar)

    # doc_attrs = _resolve_attributes_from_docstring(cls_docs)
    # attrs = _resolve_attributes(cls_docs)

    # this is a pydantic attribute


print(get_pydantic_attributes("matbii.config.LoggingConfiguration"))
# print(get_pydantic_attributes("icua.event.MouseButtonEvent"))


# for k, v in cls_docs.all_members.items():
#     if v.is_attribute and not v.is_alias:
#         print(v)
#         print(v.as_dict())
#     if v.is_attribute and v.is_alias:
#         print(v)

# if v.target.is_alias:
#     print(k, v.target.target.value)
#     value = v.target.target.value
#     if value:
#         print(type(value), value.as_dict())
# def get_attempt_methods(obj):
#     methods = inspect.getmembers(obj, predicate=inspect.ismethod)
#     methods = [m[1] for m in methods]
#     return list(filter(lambda x: hasattr(x, "is_attempt"), methods))


# a = get_attempt_methods(SystemMonitoringActuator())

# t = typing.get_type_hints(a[0])

# sections = parse(Docstring(a[0].__doc__), "google")
# print(sections)
# print([s.as_dict() for s in sections])

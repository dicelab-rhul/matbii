"""Generate the code reference pages and navigation."""

from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()
package = "matbii"
root = Path(__file__).parent.parent.parent
assert root.name == package
src = root / package
for path in sorted(src.rglob("*.py")):
    if path.name.startswith("_") and path.name != "__init__.py":
        continue  # ignore files starting with underscores (except __init__ files) these are private!
    module_path = path.relative_to(root).with_suffix("")
    # doc_path = path.relative_to(root).with_suffix(".md")
    full_doc_path = Path("reference", path.relative_to(src).with_suffix(".md"))
    parts = tuple(module_path.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
        full_doc_path = full_doc_path.with_name("index.md")
        modules = [
            p
            for p in module_path.parent.glob("*.py")
            if p.with_suffix("").name != module_path.name
        ]
        packages = [
            p
            for p in module_path.parent.glob("*")
            if p.is_dir() and not p.name.startswith("_")
        ]
        # print(module_path)
        # print(modules)
        # print(packages)

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"::: {ident}\n")
            if len(modules) + len(packages) > 0:
                # contains many .py files or sub pakages, treat __init__.py as a toc file
                fd.write("    options:\n")
                fd.write("      members: false\n")
                fd.write("      show_submodules: false\n")
                if packages:
                    fd.write("### Packages\n")
                    for p in packages:
                        fd.write(f"- [{p.as_posix()}][{'.'.join(p.parts)}]\n")
                if modules:
                    fd.write("### Modules\n")
                    for p in modules:
                        fd.write(
                            f"- [{p.as_posix()}][{'.'.join(p.with_suffix('').parts)}]\n"
                        )
            else:
                pass  # only __init__.py, treat this as its own file, display everything.
    else:
        # normal .py file, show documentation!
        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

# with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
#     n = list(nav.build_literate_nav())
#     nav_file.writelines(n)
#     for i in n:
#         print("??")

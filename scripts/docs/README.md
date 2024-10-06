# Dev guide to generating documentation

Documentation for this package is generated using the mkdocs package. It uses the script `gen_ref_pages.py` to generate the API reference. Other useful documentation macros are defined in `macros.py`.

### Test

To test documentation generation use:
```
mkdocs serve
```

### Deploy

To deploy documentation use: 

```
mike deploy <VERSION> latest -u
```

Then push the gh-pages branch:

```
git checkout gh-pages
git push
```

This directory contains example configurations for running matbii. Test them out with;
```
python -m matbii --example <EXAMPLE>
```

Below we run the example "only-tracking" and then generate a summary of the results.
```
python -m matbii --example only-tracking
python -m matbii --script summary --path only-tracking-logs/<LOG_DIR>
```
The summary will be saved in the log directory in the summary subdirectory.

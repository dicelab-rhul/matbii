## Install

`matbii` is avaliable as a [pypi](https://pypi.org/project/matbii/) package and can be installed with pip (recommended):
```
pip install matbii
```
or can easily be installed from source (for the latest pre-release updates):
```
git clone https://github.com/dicelab-rhul/matbii.git
pip install ./matbii
```

!!! note
    It is always a good idea to use the latest version of `icua` to get the latest fixes and features, update with: 
    ```
    pip install -U icua
    ```

## Run

Run with default configuration:
```
python -m matbii
```

??? warning "Errors on Windows"
    You might encounter the following error when running for the first time:

    ```
    ERROR: 'star-ray-pygame' requires a cairo installation which may not be installed automatically on some systems.
    Cause:
        no library called "cairo-2" was found
        no library called "cairo" was found
        no library called "libcairo-2" was found
        cannot load library 'libcairo.so.2': error 0x7e.  Additionally, ctypes.util.find_library() did not manage to locate a library called 'libcairo.so.2'
        cannot load library 'libcairo.2.dylib': error 0x7e.  Additionally, ctypes.util.find_library() did not manage to locate a library called 'libcairo.2.dylib'
        cannot load library 'libcairo-2.dll': error 0x7e.  Additionally, ctypes.util.find_library() did not manage to locate a library called 'libcairo-2.dll'

    ACTION REQUIRED: Please ensure the required binaries are installed and accessible via your PATH environment variable.
        >> On Windows: Install the latest GTK-3 runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases, use the default install path!
        >> See 'star-ray-pygame' README for more information: https://github.com/dicelab-rhul/star-ray-pygame.
    ```

    **To remedy:** install the latest [GTK-3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases). Make sure to use the **default install directory** so that `matbii` can find the installation.


### Default entry point

The default entry point for `matbii` (`python -m matbii <OPTIONS>` which will use [`matbii.__main__.py`](https://github.com/dicelab-rhul/matbii/blob/main/matbii/__main__.py)) is highly configurable and a good place to start. A full list of command line arguments is given below. The most important option is `-c` which specifies a path to a configuration file (details on [next page](configuration.md)).

### Command line arguments

{{ cmd_help() }}

All options except `-c` will override some option that is specified in the configuation file.

See [next page](configuration.md) for details on the main configuration file.

??? info "Custom entry points (advanced)"
    Some experiments may require more advanced setups and you may wish to define your own entry point. The [`__main__.py`](https://github.com/dicelab-rhul/matbii/blob/main/matbii/__main__.py) file should serve as inspiration for this. For more details see the [documentation for advanced users](/matbii/advanced/custom_entry_points.md). It is recommended to read on to see what is offered by default before attempting to build you own entry point.















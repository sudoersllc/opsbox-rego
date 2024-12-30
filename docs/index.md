# Opsbox Plugins
Welcome to the Opsbox plugins directory. This repository contains a collection of plugins designed to extend the functionality of Opsbox. Each plugin is defined in its own `pyproject.toml` file, which specifies the dependencies required for that plugin.

## Installing Plugins
### Through PyPI

Most of the packages in this directory are already distributed! Simply download them from PyPI, using the package name desired.

To install in UV, simply do the following:

`uv add opsbox-<package-name>`

### Local Build

1. *Sync UV environment*
2. *Run build.py*
3. *Enjoy dists!*

#### Sync UV environment
To begin, we first need to have a good testing/build environment.

In the root of the git directory, run `uv sync`. This will install everything needed.

#### Run build.py
Next, run the bulk build script using `uv run build.py`

#### Enjoy!
The build script will copy all the distributions to the root /dist folder.

Enjoy your distributions!

## Plugin Types

This repository contains various types of plugins, each serving a different purpose within Opsbox:

- **Assistants**: These plugins provide recommendations and strategies based on gathered data.
- **AWS Plugins**: These plugins offer checks and functionalities specific to AWS services.
- **Handlers**: These plugins handle various types of operations within Opsbox.
- **Outputs**: These plugins define different output formats for Opsbox results.

## Using Plugins with Opsbox

### Packages
Packages are autodetected by opsbox if they are in the same environment.

### Individual Modules
Once you have installed the necessary dependencies for the plugins in OpsBox's , you can point the main Opsbox program to this directory using the `--plugin_dir` option. Ensure you have installed the prerequisites for Opsbox before proceeding.

```sh
main.py ... --plugin_dir path/to/this/repository
```

This will allow Opsbox to load and utilize the plugins contained in this directory.

## Conclusion

This directory provides a comprehensive set of plugins to enhance the capabilities of Opsbox. By following the installation instructions and pointing Opsbox to this directory, you can leverage these plugins to optimize your operations.

For more information, refer to the individual plugin documentation and the Opsbox main documentation.
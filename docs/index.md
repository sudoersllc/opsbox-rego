# Opsbox Plugins

Welcome to the Opsbox plugins directory. This repository contains a collection of plugins designed to extend the functionality of Opsbox. Each plugin is defined in its own `pyproject.toml` file, which specifies the dependencies required for that plugin.

## Installing Plugins

To install the dependencies for any of the plugins, you can use [uv](https://docs.astral.sh/uv/)(https://docs.astral.sh/uv/). Below is an example of how to install the dependencies for a plugin in the Opsbox environment:

```sh
# Navigate to the directory containing the pyproject.toml file
cd path/to/plugin_directory

# Install the dependencies using uv
uv sync
```

For example, to install the dependencies for the `general-handler` plugin:

```sh
cd aws_providers
uv sync
```

### Installing in an Existing Environment

If you want to install the dependencies in an existing environment, you can use the following command:

```sh
# Activate your existing environment
source path/to/your/env/bin/activate  # On Windows, use `path\to\your\env\Scripts\activate`

# Navigate to the directory containing the pyproject.toml file
cd path/to/plugin_directory

# Install the dependencies using Poetry
uv sync
```

## Plugin Types

This repository contains various types of plugins, each serving a different purpose within Opsbox:

- **Assistants**: These plugins provide recommendations and strategies based on gathered data.
- **AWS Plugins**: These plugins offer checks and functionalities specific to AWS services.
- **Handlers**: These plugins handle various types of operations within Opsbox.
- **Outputs**: These plugins define different output formats for Opsbox results.

## Using Plugins with Opsbox

Once you have installed the necessary dependencies for the plugins, you can point the main Opsbox program to this directory using the `--plugin_dir` option. Ensure you have installed the prerequisites for Opsbox before proceeding.

```sh
main.py ... --plugin_dir path/to/this/repository
```

This will allow Opsbox to load and utilize the plugins contained in this directory.

## Conclusion

This directory provides a comprehensive set of plugins to enhance the capabilities of Opsbox. By following the installation instructions and pointing Opsbox to this directory, you can leverage these plugins to optimize your operations.

For more information, refer to the individual plugin documentation and the Opsbox main documentation.
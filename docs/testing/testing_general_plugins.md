# Testing General Handler Plugin Types in OpsBox Using Pytest

This document will guide you through testing general handler plugin types, including **input**, **output**, and **provider** plugins, using the provided `MockPlugin` and `MockConfig` utilities. We will cover how to set up and run tests, and provide examples for each plugin type.

## Overview

The **General Handler** in OpsBox is responsible for managing different plugin types, such as input, output, and provider plugins. When testing these plugins, it is important to verify that:

- **Hooks are properly registered and implemented** for each plugin type.
- **Data processing functions** correctly for input, output, and provider plugins.
- **Configurations are loaded correctly** and the plugins interact as expected with the OpsBox system.

This document will demonstrate how to use the provided mock utilities and `pytest` to test these plugin types.

### Mocks

We will use the following mocks to facilitate testing:

- **`MockPlugin`**: Produces a mock plugin object with a given type, class, and configuration.
- **`MockConfig`**: Creates a mock configuration file for testing, combining overrides and base configuration.

### Plugin Types Tested:

1. **Input Plugin**: Processes incoming data and passes it to the next stage in the pipeline.
2. **Output Plugin**: Processes the results from other plugins and outputs the final result.
3. **Provider Plugin**: Gathers data from an external source (e.g., AWS, databases) and makes it available for further processing.

---

## Setting Up the Test Environment

First, ensure that `pytest` is installed:

```bash
uv add pytest
```

Ensure your project and mocks are properly set up. Then, use the provided `MockPlugin` and `MockConfig` functions to simulate plugins and configurations.

---

## Example Test for Input Plugins

Input plugins are responsible for processing incoming data and passing it along the pipeline.

### Example Hook Specification (if needed):

```python
class InputSpec:
    """Base contract for input plugins."""
    
    @hookspec
    def process(self, data: list[Result]) -> list[Result]:
        """Process input data."""
```

### Test for Input Plugin

```python
import pytest
from core.plugins import PluginInfo, Result
from general_handler import GeneralHandler
from mock_plugin_utils import MockPlugin, MockConfig

class ExampleInputPlugin:
    """A simple input plugin that processes data."""
    
    def grab_config(self):
        return ExampleInputConfig
    
    def set_data(self, config):
        self.config = config
    
    def process(self, data: list[Result]) -> list[Result]:
        """Simple data processor."""
        return [{"processed_data": "processed_" + item["input_data"]} for item in data]

class ExampleInputConfig(BaseModel):
    input_data_key: str

def test_input_plugin():
    """Test that the input plugin processes data correctly."""
    
    # Mock the plugin configuration
    mock_config = {
        "input_data_key": "input_data"
    }
    
    # Create a mock input plugin
    plugin = MockPlugin(ExampleInputPlugin, "input", mock_config)
    
    # Create a mock general handler
    handler = GeneralHandler()
    
    # Mock input data
    data = [{"input_data": "raw_data"}]
    
    # Process the input plugin using the handler
    results = handler.process_plugin(plugin, data, registry=None)
    
    assert results == [{"processed_data": "processed_raw_data"}]
```

### Explanation

- **MockPlugin**: Creates a mock input plugin with the specified configuration.
- **process_plugin**: This test simulates the input plugin processing some data and checks if the output is correct.

---

## Example Test for Output Plugins

Output plugins receive processed results and usually present them in a specific format or send them to a destination.

### Example Hook Specification (if needed):

```python
class OutputSpec:
    """Base contract for output plugins."""
    
    @hookspec
    def process_results(self, results: list[Result]) -> None:
        """Process and output the results."""
```

### Test for Output Plugin

```python
class ExampleOutputPlugin:
    """A simple output plugin that processes results."""
    
    def grab_config(self):
        return ExampleOutputConfig
    
    def set_data(self, config):
        self.config = config
    
    def process_results(self, results: list[Result]) -> None:
        """Simulates sending processed results somewhere."""
        # Just print the results for this test case (or log them)
        for result in results:
            print(f"Output: {result['processed_data']}")

class ExampleOutputConfig(BaseModel):
    output_target: str

def test_output_plugin(mocker):
    """Test that the output plugin processes results correctly."""
    
    # Mock configuration
    mock_config = {
        "output_target": "console"
    }
    
    # Create a mock output plugin
    plugin = MockPlugin(ExampleOutputPlugin, "output", mock_config)
    
    # Mock the general handler
    handler = GeneralHandler()
    
    # Mock processed results from prior steps
    processed_data = [{"processed_data": "final_data"}]
    
    # Mock print function (or logging) to capture output
    mocker.patch("builtins.print")
    
    # Process the output plugin
    handler.process_plugin(plugin, processed_data, registry=None)
    
    # Verify that the correct output was produced
    print.assert_called_with("Output: final_data")
```

### Explanation

- **MockPlugin**: Creates a mock output plugin with a basic configuration.
- **process_plugin**: Simulates the output plugin processing and printing the final results.
- **mocker**: Used to capture the `print` output (you can also use logging or other methods).

---

## Example Test for Provider Plugins

Provider plugins gather data from external sources, such as APIs or databases, and make it available to the rest of the pipeline.

### Example Hook Specification (if needed):

```python
class ProviderSpec:
    """Base contract for provider plugins."""
    
    @hookspec
    def gather_data(self) -> Result:
        """Gathers data from external sources."""
```

### Test for Provider Plugin

```python
class ExampleProviderPlugin:
    """A simple provider plugin that gathers data."""
    
    def grab_config(self):
        return ExampleProviderConfig
    
    def set_data(self, config):
        self.config = config
    
    def gather_data(self) -> Result:
        """Simulates gathering data from an external source."""
        return {"gathered_data": "external_data"}

class ExampleProviderConfig(BaseModel):
    api_key: str

def test_provider_plugin():
    """Test that the provider plugin gathers data correctly."""
    
    # Mock configuration for the provider plugin
    mock_config = {
        "api_key": "mock_api_key"
    }
    
    # Create a mock provider plugin
    plugin = MockPlugin(ExampleProviderPlugin, "provider", mock_config)
    
    # Process the provider plugin and gather data
    result = plugin.plugin_obj.gather_data()
    
    # Assert that the gathered data is correct
    assert result == {"gathered_data": "external_data"}
```

### Explanation

- **MockPlugin**: Creates a mock provider plugin that simulates gathering data from an external source.
- **process_plugin**: Simulates the provider plugin gathering data and returning it for further processing.

---

## Running the Tests

You can run all of these tests using `pytest`. For example, to run the entire test suite:

```bash
pytest
```

Or to run a specific test file:

```bash
pytest test/test_input_plugin.py
```

You can also run specific test functions:

```bash
pytest test/test_input_plugin.py::test_input_plugin
```

---

## Conclusion

By using the provided `MockPlugin` and `MockConfig`, you can easily simulate various plugins (input, output, and provider) and their interactions with the OpsBox system. The tests in this guide demonstrate how to ensure these plugins function correctly in the context of the general handler.
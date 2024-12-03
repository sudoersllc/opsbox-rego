
# Building Plugins for Opsbox

Creating plugins for Opsbox is a straightforward process with a few key steps. Let's walk through them!

## Tip
Opsbox uses the **Pluggy** library for plugin management, loading, and validation. If you're familiar with Pluggy, this workflow will feel familiar.

## Steps to Build Plugins

1. **Specify your hookimpl**
2. **Define configurations (optional)**
3. **Define activation (optional)**
4. **Add plugin toml file**
5. **Use results model**
5. **Add more!**

### Specify Your Hookimpl

Pluggy operates using a system of **hook specifications** ("hookspecs"), which define methods to be implemented. To create a plugin, you implement methods from these hookspecs and designate these methods as **hook implementations**.

To specify a hook implementation, import `HookimplMarker` from Pluggy and set the project to `"opsbox"`:

```python
from pluggy import HookimplMarker

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")
```

### Implement Basespec

Opsbox plugins can optionally:
- Specify configuration through a Pydantic model.
- Specify delayed activation that executes *after* setting plugin data.

All hook implementations should be collected from a single class, meaning **all hook implementations should be within the same class**.

#### Example Implementation

```python
from pydantic import BaseModel, Field
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class CostAssistant:
    
    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration Pydantic model."""
        class OAICostConfig(BaseModel):
            oai_assistant_id: str = Field(..., description="The ID of the OpenAI assistant")
            oai_vector_store_id: str = Field(..., description="The ID of the OpenAI vector store")
            oai_key: str = Field(..., description="The OpenAI API key")
        return OAICostConfig

    @hookimpl
    def set_data(self, model: BaseModel) -> None:
        """Set the plugin's data."""
        self.config = model

    @hookimpl
    def activate(self) -> None:
        """Activate the plugin by initializing the OpenAI client."""
        self.client = OpenAI(api_key=self.config.oai_key)
```

### Define Configuration (Optional)

To define the expected configuration for your plugin, implement the `grab_config` and `set_data` methods. These methods should return a Pydantic model with necessary attributes and set class data, respectively. The model attributes for will be checked for upon startup in the applications configuration parameters.

#### Example Configuration

```python
from pydantic import BaseModel, Field
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class CostAssistant:
    
    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration Pydantic model."""
        class OAICostConfig(BaseModel):
            oai_assistant_id: str = Field(..., description="The ID of the OpenAI assistant")
            oai_vector_store_id: str = Field(..., description="The ID of the OpenAI vector store")
            oai_key: str = Field(..., description="The OpenAI API key")
        return OAICostConfig

    @hookimpl
    def set_data(self, model: BaseModel) -> None:
        """Set the plugin's data."""
        self.config = model
```

### Define Activation (Optional)

Sometimes, you need to initialize data *before* processing but *after* setting the class' data. Use an `activate` function to achieve this.

#### Example Activation

```python
from openai import OpenAI
from pydantic import BaseModel, Field
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class CostAssistant:
    
    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration Pydantic model."""
        class OAICostConfig(BaseModel):
            oai_assistant_id: str = Field(..., description="The ID of the OpenAI assistant")
            oai_vector_store_id: str = Field(..., description="The ID of the OpenAI vector store")
            oai_key: str = Field(..., description="The OpenAI API key")
        return OAICostConfig

    @hookimpl
    def set_data(self, model: BaseModel) -> None:
        """Set the plugin's data."""
        self.config = model

    @hookimpl
    def activate(self) -> None:
        """Activate the plugin by initializing the OpenAI client."""
        self.client = OpenAI(api_key=self.config.oai_key)
```

### Define plugin info toml file
Each plugin should include a TOML file with essential information. The TOML file should be in the following format:

```toml
[info]
name = "Plugin Name"
module = "plugin_module"
class_name = "PluginClassInModule"
type = "assistant"
uses = ["general"]
```

Where:
- `name` is what you'll refer to the plugin as (**please no spaces!**)
- `module` is the name of your python module (normally found from your *<module_name>.py file*)
- `class_name` is the class *in* the module that corresponds to your plugin.
- `type` is the type of the plugin. This allows us to dispatch plugins to the right handler.
- `uses` is a list of used plugins, handlers, etc.

For Rego checks, include additional information:

```toml
...

uses = ["provider_name", "rego"]
[rego]
rego_file = "path/to/regofile.rego"
description = "Description of policy results"
```

(More info can be found in the creating rego plugins document!)

It helps to put all your plugin info and modules into a new folder in the plugin directory.

### Define other hookspecs
In order to implement the various *types* of plugins in Opsbox, you need to implement their respective hooks. 

All plugins can use hookspecs defined in **BaseSpec**. These include those that implement basic optional features such as delayed activation and configuration gathering.

For the two base handlers, the following hookspecs exist:

***General Handler***
- **InputSpec**, Hooks that implement methods to generate formatted results
- **ProviderSpec**, Hooks that implement methods to gather data that other plugins can rely on
- **OutputSpec**, Hooks that implement methods to output formatted result data
- **AssistantSpec**, Hooks that implement methods to transform formatted data

***Rego Handler***
- **RegoSpec**, Hooks that implement methods to generate formatted results from Rego check outputs.

***Read the documentation for rego and handler plugins!*** 
They require a bit more than other plugin types.

Check out some more of these documents for more info on how to structure various types of plugins.

### Utilize the Result Models

OpsBox uses `Result` models to represent the outputs of plugins, especially when data needs to be passed between plugins in the pipeline.

#### Understanding the Result Model

The `Result` model is defined as follows:

```python
from pydantic import BaseModel

class Result(BaseModel):
    """A model representing the results of a plugin's processing.

    Attributes:
        relates_to (str): The entity the result relates to.
        result_name (str): The name of the result.
        result_description (str): A description of the result.
        details (dict | list[dict]): Additional details of the result.
        formatted (str): A formatted string representation of the result.
    """
    relates_to: str
    result_name: str
    result_description: str
    details: dict | list[dict]
    formatted: str
```

#### How to Use the Result Model in Your Plugin

When your plugin processes data and produces output that needs to be passed to subsequent plugins, you should encapsulate that output in a `Result` object.

##### Example

Suppose you have an input plugin that gathers data and needs to output it for assistant plugins to process.

```python
from pydantic import BaseModel
from core.plugins import Result
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class ExampleInputPlugin:
    @hookimpl
    def process(self, data):
        # Simulate data gathering
        gathered_data = {
            "key1": "value1",
            "key2": "value2"
        }

        # Create a Result object
        result = Result(
            relates_to="ExampleInputPlugin",
            result_name="GatheredData",
            result_description="Data gathered from the example input plugin.",
            details=gathered_data,
            formatted=str(gathered_data)
        )

        # Return the result in a list
        return [result]
```

In an assistant plugin, you can process the results from previous plugins:

```python
from core.plugins import Result
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class ExampleAssistantPlugin:
    @hookimpl
    def process_input(self, input_results: list[Result]) -> list[Result]:
        processed_results = []
        for result in input_results:
            # Perform some processing on result.details
            processed_data = {k: v.upper() for k, v in result.details.items()}

            # Create a new Result object
            new_result = Result(
                relates_to=result.relates_to,
                result_name="ProcessedData",
                result_description="Data processed by the assistant plugin.",
                details=processed_data,
                formatted=str(processed_data)
            )
            processed_results.append(new_result)
        return processed_results
```

Finally, an output plugin can take the processed results and output them accordingly:

```python
from core.plugins import Result
from pluggy import HookimplMarker

hookimpl = HookimplMarker("opsbox")

class ExampleOutputPlugin:
    @hookimpl
    def process_results(self, results: list[Result]) -> None:
        for result in results:
            # Output the formatted result
            print(f"Output from {result.relates_to}: {result.formatted}")
```

#### Best Practices

- **Consistency**: Ensure that all plugins return their outputs encapsulated in `Result` objects for consistency across the pipeline.
- **Information Preservation**: Include meaningful information in all fields of the `Result` model to aid in debugging and downstream processing.
- **Avoid Data Loss**: When processing results, be careful not to inadvertently discard important information in the `details` or other fields.

### Add More!

Feel free to extend your plugins with additional functionality as needed. You can define more methods, utilize other libraries, and customize your plugin to fit your specific requirements.

---

## Additional Notes

- **Testing Your Plugin**: It's a good idea to write tests for your plugin to ensure it behaves as expected within the OpsBox framework.
- **Documentation**: Document your plugin's functionality, configuration options, and any dependencies it may have.
- **Contribution**: If you believe your plugin could benefit others, consider contributing it back to the OpsBox community!
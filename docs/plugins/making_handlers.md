# Creating Handlers for OpsBox

Handlers are the orchestrators within the OpsBox Plugin System. They manage and coordinate various types of plugins, ensuring that each plugin operates seamlessly within the defined pipeline. This document will guide you through the process of creating handlers, understanding their types, and integrating them effectively into your OpsBox setup.

## Before You Start

Before you begin creating handlers, it's essential to have a solid understanding of **Plugin Basics**. Please refer to the [Development Basics](./development_basics.md) document, which covers:

- Setting up a proper **hook implementation marker** to register hook implementations
- Defining expected user configuration values through a **Pydantic model**
- Initializing plugin classes through the `activate()` hook implementation

## Steps to Create Handlers

1. **Specify Your Hook Implementations**
2. **Define Handler Configurations (optional)**
3. **Implement the Handler Class**
4. **Add Handler TOML File**
5. **Register and Activate the Handler**
6. **Integrate the Handler into the Plugin Pipeline**
7. **Add More!**

### Specify Your Hook Implementations

Handlers in OpsBox utilize **hook specifications** ("hookspecs") to define the contracts they must adhere to. These hookspecs ensure that handlers can manage and process different types of plugins effectively.

To specify hook implementations, import `HookimplMarker` from Pluggy and set the project name to `"opsbox"`:

```python
from pluggy import HookimplMarker

# Define a hook implementation marker
hookimpl = HookimplMarker("opsbox")
```

### Define Handler Configurations (Optional)

While not mandatory, defining configurations for your handler can provide flexibility and control over how it manages different plugin types. Use Pydantic models to define and validate these configurations.

#### Example Configuration

```python
from pydantic import BaseModel, Field

class HandlerConfig(BaseModel):
    log_level: str = Field("INFO", description="Logging level for the handler")
    timeout: int = Field(30, description="Timeout for plugin processing in seconds")
```

### Implement the Handler Class

Create a handler class that implements the required hookspecs. This class will manage specific types of plugins based on your configuration.

#### `process_plugin` Method

The process_plugin method is the cornerstone of a handler's functionality within the OpsBox Plugin System. It is responsible for executing a specific plugin based on its type (e.g., input, output, assistant, provider, rego). This method receives three primary parameters:

- plugin (PluginInfo): Contains metadata and configuration details about the plugin to be processed.
- prior_results (list[Result]): A list of results produced by previously executed plugins in the pipeline.
- registry (Registry): The central registry managing all active plugins and their interactions.

This function describes the flow of the plugin, and executes code according to it's own defined hookspecs on plugin objects that implement them.

To do this, we use `PluginInfo` objects.

#### `PluginInfo` Object

The `PluginInfo` object is a core component of the OpsBox Plugin System, encapsulating all essential metadata and configuration details for each plugin. It serves as a standardized structure that includes attributes such as the plugin's name, module, class name, type (e.g., `input`, `output`, `assistant`), path to its TOML configuration file, and any dependencies it may have (`uses`). Additionally, it holds references to the instantiated plugin object and its validated configuration data. By utilizing the `PluginInfo` object, OpsBox ensures consistent management, loading, and execution of plugins within the system.

**Key Attributes:**

- **name** (`str`): Unique identifier for the plugin.
- **module** (`str`): Python module where the plugin class is defined.
- **class_name** (`str`): Name of the plugin class within the module.
- **type** (`str`): Category of the plugin (e.g., `input`, `output`).
- **toml_path** (`str`): File path to the plugin's TOML configuration.
- **plugin_obj** (`Any | None`): Instance of the loaded plugin class.
- **config** (`BaseModel | None`): Validated configuration data for the plugin.
- **uses** (`list[str]`): List of other plugins this plugin depends on.
- **extra** (`dict[str, Any] | None`): Additional metadata or information.

**Example Usage:**

```python
from core.plugins import PluginInfo

plugin_info = PluginInfo(
    name="example_input",
    module="example_input",
    class_name="ExampleInputPlugin",
    type="input",
    toml_path="path/to/example_input.toml",
    uses=["provider_plugin"],
    extra={"handler": {"handles"=["input", "output", "assistant"]}}
)
```

By leveraging the `PluginInfo` object, developers can easily access and manage plugin-specific information.

#### Example General Handler

```python
# general_handler.py
from pluggy import HookimplMarker, PluginManager
from core.plugins import PluginInfo, Result, Registry
from loguru import logger

hookimpl = HookimplMarker("opsbox")

class GeneralHandler:
    """General handler for Python plugins."""

    @hookimpl
    def add_hookspecs(self, manager: PluginManager):
        """Add the hookspecs to the manager."""
        from core.base_hooks import AssistantSpec, OutputSpec, ProviderSpec, InputSpec
        manager.add_hookspecs(AssistantSpec)
        manager.add_hookspecs(OutputSpec)
        manager.add_hookspecs(ProviderSpec)
        manager.add_hookspecs(InputSpec)

    @hookimpl
    def process_plugin(self, plugin: PluginInfo, prior_results: list[Result], registry: Registry) -> list[Result]:
        """Process the plugin based on its type."""
        logger.debug(f"GeneralHandler processing plugin {plugin.name}")
        if plugin.type == "input":
            # Process input plugin
            return plugin.plugin_obj.process(prior_results)
        elif plugin.type == "output":
            # Process output plugin
            plugin.plugin_obj.process_results(prior_results)
            return prior_results
        elif plugin.type == "assistant":
            # Process assistant plugin
            return plugin.plugin_obj.process_input(prior_results)
        else:
            logger.warning(f"Unknown plugin type: {plugin.type}")
            return prior_results
```

### Add Handler TOML File

Each handler must include a TOML file with essential information. This file informs the OpsBox system about the handler's metadata and the types of plugins it manages.

#### Example Handler TOML

```toml
[info]
name = "general"
module = "general_handler"
class_name = "GeneralHandler"
type = "handler"

[handler]
handles = ["input", "output", "assistant"]
```

**Explanation:**

- **[info] Section**:
  - `name`: Unique name of the handler (`"general"`).
  - `module`: Name of the Python module containing the handler (`"general_handler"`).
  - `class_name`: Name of the handler class (`"GeneralHandler"`).
  - `type`: Must be `"handler"` to designate this plugin as a handler.

- **[handler] Section**:
  - `handles`: List of plugin types this handler manages (`"input"`, `"output"`, `"assistant"`).

For specialized handlers like the **Rego Handler**, the TOML file may include additional sections to handle specific plugin types.

### Register and Activate the Handler

Ensure that your handler is placed in the designated `plugin_dir` and that the OpsBox `Registry` is aware of it. The `Registry` will automatically load and register handlers based on their TOML configurations.

### Integrate the Handler into the Plugin Pipeline

Once the handler is registered and activated, it will manage the execution of plugins based on their types. Handlers ensure that each plugin is processed correctly within the pipeline.

#### Example Pipeline Execution

```python
# Produce the pipeline based on active plugins
pipeline = registry.produce_pipeline()

# Execute the pipeline, managed by the registered handlers
registry.process_pipeline(pipeline)
```

**Output:**

```
Activating GeneralHandler with log_level=DEBUG and timeout=60
Activating ExampleInputPlugin with data source: SampleSource
Processing plugin example_input
Processing data: [{'key1': 'value1', 'key2': 'value2'}]
```

### Add More!

Feel free to extend your handlers with additional functionalities as needed. You can define more methods, utilize other libraries, and customize your handler to fit specific requirements.

## FAQs
### **Q1: Can a Handler manage multiple Plugin Types?**

**A1:**  
**Yes**, a single Handler can manage multiple plugin types. In the handler's TOML configuration file, list all the plugin types it handles under the `[handler]` section's `handles` attribute. This allows the Handler to process various plugin types within the same pipeline.

**Example:**

```toml
[handler]
handles = ["input", "output", "assistant", "transformer"]
```

---

### **Q2: How does the `process_plugin` Method Work?**

**A2:**  
The `process_plugin` method is the core function of a Handler. It dictates how each plugin is executed based on its type. This method receives three parameters:

- **`plugin` (`PluginInfo`)**: Metadata and configuration of the plugin to be processed.
- **`prior_results` (`list[Result]`)**: Results from previously executed plugins.
- **`registry` (`Registry`)**: The central registry managing all plugins.

**Functionality:**

1. **Identify Plugin Type:** Determines the type of the plugin (e.g., `input`, `output`).
2. **Execute Plugin Logic:** Calls the appropriate method on the plugin object based on its type.
3. **Return Results:** Outputs a list of `Result` objects for further processing.

**Example Implementation:**

```python
@hookimpl
def process_plugin(self, plugin: PluginInfo, prior_results: list[Result], registry: Registry) -> list[Result]:
    logger.debug(f"CustomHandler processing plugin {plugin.name}")
    if plugin.type == "transformer":
        return plugin.plugin_obj.transform(prior_results)
    else:
        logger.warning(f"Unhandled plugin type: {plugin.type}")
        return prior_results
```

---

### **Q3: How Do Handlers Interact with the Registry and Plugin Pipeline?**

**A3:**  
Handlers are integrated into the OpsBox Plugin Pipeline through the `Registry`. When the `Registry` initializes, it loads all handlers based on their TOML configurations. During pipeline execution:

1. **Pipeline Production:** The `Registry` compiles an ordered list of active plugins.
2. **Handler Invocation:** For each plugin, the corresponding Handler's `process_plugin` method is invoked.
3. **Result Management:** Handlers process plugins and return `Result` objects, which are then passed to subsequent plugins as needed.

This interaction ensures that each plugin is executed in the correct context and sequence, maintaining the pipeline's integrity.

---

### **Q4: Can Handlers Be Specialized for Specific Plugin Types?**

**A4:**  
**Yes**, Handlers can be specialized to manage specific plugin types, enhancing modularity and scalability. For example, a **Rego Handler** can be created to exclusively manage `rego` plugins, ensuring that policy compliance checks are handled separately from other plugin types.

**Example:**

```toml
# rego_handler.toml
[info]
name = "rego_handler"
module = "rego_handler"
class_name = "RegoHandler"
type = "handler"

[handler]
handles = ["rego"]
```

---

### **Q5: What Should I Do If My Handler Fails During Execution?**

**A5:**  
If a Handler encounters an error during execution:

1. **Logging:** The system logs the error details using `loguru`, providing insights into what went wrong.
2. **Graceful Degradation:** Depending on the severity, the system may skip the faulty handler or halt the entire pipeline to prevent inconsistent states.
3. **Debugging:** Review the logs to identify and address the issue within the Handler's implementation.
4. **Retry Mechanism:** Implement retry logic within the Handler if appropriate, to handle transient errors.

**Best Practice:** Always include robust error handling within your Handlers to manage exceptions gracefully and maintain system stability.

---

### **Q6: How Can I Extend the HandlerSpec with Additional Methods?**

**A6:**  
To extend the `HandlerSpec` with additional methods:

1. **Define New Hookspecs:**
   - Add new methods annotated with `@hookspec` in `core/base_hooks.py`.

   ```python
   # core/base_hooks.py
   class CustomSpec:
       @hookspec
       def custom_method(self, data: Any) -> Any:
           """A custom hook method."""
   ```

2. **Register the New Hookspecs:**
   - Update the Handler's `add_hookspecs` method to include the new hookspecs.

   ```python
   @hookimpl
   def add_hookspecs(self, manager: PluginManager):
       from core.base_hooks import CustomSpec
       manager.add_hookspecs(CustomSpec)
   ```

3. **Implement the New Methods in the Handler:**
   - Define the corresponding hook implementations in your Handler class.

   ```python
   @hookimpl
   def custom_method(self, data: Any) -> Any:
       # Implement custom logic
       return processed_data
   ```

4. **Update Handler Configuration:**
   - Ensure that your handler's TOML file and any related configurations accommodate the new methods.

---

### **Q7: Can Multiple Handlers Manage the Same Plugin Type?**

**A7:**  
While it's technically possible to have multiple Handlers manage the same plugin type, it's generally **not recommended** as it can lead to conflicts and unpredictable behaviors. Instead, designate a single Handler to manage each plugin type to maintain clarity and control within the pipeline.

**Recommendation:**  
Ensure that each plugin type is managed by only one Handler to avoid overlapping responsibilities and potential processing issues.

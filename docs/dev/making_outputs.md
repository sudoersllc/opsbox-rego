# Creating Output Plugins for Opsbox

Output plugins in Opsbox are designed to process and handle the data collected from provider plugins and formatted by Rego checks. They play a crucial role in the final stage of the pipeline, ensuring that the processed results are delivered to their intended destinations, such as databases, files, or issue tracking systems.


## Before You Start

If you haven't read the **Plugin Basics** document, please take a moment to do so! It provides essential information for successfully gathering data, including:

- Setting up a proper **hookimpl marker** to register hook implementations
- Defining expected user configuration values through a **Pydantic model**
- Initializing plugin classes through the `activate()` hook implementation


## Defining Hook Implementations

Output plugins implement the hooks from `OutputSpec`. The key method to implement is `process_results(self, results: list["Result"]) -> None`.

### Hook Specification

Here is the definition from the `OutputSpec` class:

```python
class OutputSpec:
    """Base contract for outputs.
    Outputs are plugins that process the data from the providers."""

    @hookspec
    def process_results(self, results: list["FormattedResult"]) -> None:
        """Output the data from the plugin."""
```

### Example Implementation

Below is an example implementation of an output plugin that writes results to a text file:

```python
from pluggy import HookimplMarker
from core.plugins import Result
import os

hookimpl = HookimplMarker("opsbox")

class TextFileOutput:
    
    @hookimpl
    def process_results(self, results: list[Result]) -> None:
        """
        Write the formatted results to a text file.

        Args:
            results (list[FormattedResult]): A list of formatted results to be written to a file.
        """
        output_directory = "output_files"
        os.makedirs(output_directory, exist_ok=True)

        for result in results:
            file_path = os.path.join(output_directory, f"{result['check_name']}.txt")
            with open(file_path, "w") as file:
                file.write(result["formatted"])
```

### Explanation

1. **Hook Implementation**: The `process_results` method processes a list of `Result` items.
2. **Writing to File**: For each formatted result, it creates a text file and writes the check name, description, result, details, and formatted output to the file.
3. **Output Directory**: Ensures that the output directory exists and writes each result to a separate file.

By following these guidelines, you can create efficient output plugins for Opsbox, ensuring your formatted results are processed and delivered to their intended destinations. Happy coding! 🚀

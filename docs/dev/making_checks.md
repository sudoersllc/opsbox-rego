
# Creating Rego Check Plugins for Opsbox

Rego check plugins are vital for gathering data from a provider plugin, applying a defined policy, and formatting the raw result into a readable format. Let's explore how to create one!

## Before You Start

If you haven't read the **Plugin Basics** and **Providers** documents, please take a moment to do so. They provide essential information for successfully gathering data, including:

- Setting up a proper **hookimpl marker** to register hook implementations
- Information on setting up your plugin info document
- Details on providers to help you get started

While Rego checks don't typically use `activate` or configuration models, feel free to include them if needed!

## Requirements

Rego check plugins require three things:

1. **A configuration file** detailing the location of the Rego file, the provider to gather data from, and the meaning of the check results.
2. **A Rego file** with a policy that returns meaningful results from the provider data.
3. **A Python class** with a hook implementation that converts the Rego check results into a human-readable format.

## Configuration File

In addition to the `[info]` section of your TOML file, you also need to include a `[rego]` header:

```toml
[info]
name = "Plugin Name"
module = "plugin_module"
class_name = "PluginClassInModule"
type = "rego"
uses = ["rego"]

[rego]
rego_file = "path/to/regofile.rego"
description = "Description of policy results"
```

- **type** must be `"rego"`.
- **uses** list must contain `"rego"`.

- **rego_file** points to the rego file.
- **description** describes the rego check itself.

These fields tell Opsbox what it needs to know to accurately manage Rego checks.

## Defining Hook Implementations

Rego checks implement the hooks from `RegoSpec`. The key method to implement is `report_findings(self, data: "Result") -> "Result"`. This hook takes in a Result with rego-proccessed details from the rego check speicified and formats it into an LLM-usable text format, returning the result.

### Example Rego Policy

Here’s an example Rego policy for the `idle_instances` check:

```rego
package aws.cost.idle_instances

default allow = false

allow {
    instance := input.instances[_]
    instance.state == "running"
    instance.avg_cpu_utilization < 5  # Threshold for low CPU utilization
}

details := [instance | instance := input.instances[_]; instance.state == "running"; instance.avg_cpu_utilization < 5]
```

The `details` dictionary of a rego check can be accessed using the `details` part of the input Result object.

### Example Implementation

Below is an example of the `idle_instances` plugin:

```python
import yaml
from loguru import logger
from core.plugins import Result


class IdleInstances:
    """Plugin for identifying idle EC2 instances."""

    def report_findings(self, data: Result) -> Result:
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details
        instances = []
        for instance in findings:
            instance_obj = {
                instance["instance_id"]: {
                    "region": instance["region"],
                    "state": instance["state"],
                    "avg_cpu_utilization": instance["avg_cpu_utilization"],
                    "instance_type": instance["instance_type"],
                    "operating_system": instance["operating_system"],
                }
            }
            instances.append(instance_obj)
        try:
            instance_yaml = yaml.dump(instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting instance details: {e}")

        template = """The following EC2 instances are idle, with an average CPU utilization of less than 5%.
The data is presented in the following format:
- instance_id:
    region: region
    state: running
    avg_cpu_utilization:

{instances}"""

        if instances:
            return Result(
                relates_to="ec2",
                result_name="idle_instances",
                result_description="Idle EC2 Instances",
                details=data.details,
                formatted=template.format(instances=instance_yaml),
            )
        else:
            return Result(
                relates_to="ec2",
                result_name="idle_instances",
                result_description="Idle EC2 Instances",
                details=data.details,
                formatted="No idle EC2 instances found.",
            )

```

In this example, `report_findings` processes the `Result`, formats it using YAML, and returns a `Result`.

By following these guidelines, you can create effective Rego check plugins for Opsbox, making your cloud infrastructure management more insightful and automated. Happy coding! 🚀

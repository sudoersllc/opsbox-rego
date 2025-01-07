# Creating Provider Plugins for OpsBox

Provider plugins are the backbone of OpsBox, enabling the system to gather data from various infrastructure backends such as AWS and Azure (*Azure support is not yet implemented*). These plugins provide a seamless interface for collecting data, which is then utilized by rego checks and input plugins to enhance functionality and compliance.

## Before You Start

Before you begin developing a Provider plugin, it's essential to familiarize yourself with the **Plugin Basics** documentation. This foundational guide covers:

- **Setting Up the Hook Implementation Marker:** Learn how to register your plugin's hook implementations using Pluggy.
- **Defining User Configuration Values:** Utilize **Pydantic models** to specify and validate the configuration parameters your plugin requires.
- **Initializing Plugin Classes:** Implement the `activate()` hook to initialize your plugin effectively.

Additionally, ensure you have the necessary configuration and client setup to access the service data required by your plugin.

## Required Hooks

Provider plugins in OpsBox are specialized plugins that implement the `ProviderSpec` methods defined within the `general` handler. The primary method you need to implement is `gather_data`, which is responsible for collecting data from your services.

### Hook Specification

The `gather_data` method is designed to probe your services for data and return a `Result` object. This `Result` serves as the input for subsequent rego checks and input plugins.

```python
class ProviderSpec:
    @hookspec
    def gather_data(self) -> Result:
        """Gather data for the plugin."""
```

### Example Implementation

Below is an example from the production `ec2` plugin's `gather_data` function. This example demonstrates how to collect data related to AWS EC2 instances, volumes, and Elastic IPs.

```python
from pluggy import HookimplMarker
from pydantic import BaseModel, Field

hookimpl = HookimplMarker("opsbox")

class EC2Provider:
    ...
    @hookimpl
    def gather_data(self):
        """
        Gathers data related to AWS EC2 instances, volumes, and Elastic IPs.

        Returns:
            Result: A Result object containing the gathered data in the following format:
                {
                    "input": {
                        "volumes": [
                            {
                                "volume_id": "vol-1234567890abcdef0",
                                "state": "available",
                                "size": 8,
                                "create_time": "2021-06-01T00:00:00",
                                "region": "us-west-1"
                            },
                            ...
                        ],
                        "instances": [
                            {
                                "instance_id": "i-1234567890abcdef0",
                                "state": "running",
                                "avg_cpu_utilization": 0.0,
                                "region": "us-west-1"
                            },
                            ...
                        ]
                    }
                }
        """
        # Implementation for gathering data from AWS EC2
        # Example placeholder implementation
        data = {
            "input": {
                "volumes": [
                    {
                        "volume_id": "vol-1234567890abcdef0",
                        "state": "available",
                        "size": 8,
                        "create_time": "2021-06-01T00:00:00",
                        "region": "us-west-1"
                    },
                    # Additional volume data...
                ],
                "instances": [
                    {
                        "instance_id": "i-1234567890abcdef0",
                        "state": "running",
                        "avg_cpu_utilization": 0.0,
                        "region": "us-west-1"
                    },
                    # Additional instance data...
                ]
            }
        }
        result = Result(
            relates_to="EC2Provider",
            result_name="EC2Data",
            result_description="Collected data from AWS EC2 instances and volumes.",
            details=data,
            formatted=str(data)
        )
        return result
```

## Plugin Configuration

Each Provider plugin must include a TOML configuration file that provides essential metadata and specifies its dependencies. This configuration ensures that OpsBox can correctly load and manage the plugin.

### Example `provider_plugin.toml`

```toml
[info]
name = "ec2_provider"
module = "ec2_provider"
class_name = "EC2Provider"
type = "provider"
uses = ["general"]
```

**Configuration Breakdown:**

- **[info] Section:**
  - `name`: Unique identifier for the plugin (`"ec2_provider"`).
  - `module`: Name of the Python module where the plugin class is defined (`"ec2_provider"`).
  - `class_name`: Name of the plugin class within the module (`"EC2Provider"`).
  - `type`: Specifies the plugin type (`"provider"`), allowing OpsBox to dispatch it to the appropriate handler.
  - `uses`: Lists dependencies required by the plugin (`["general"]`).


## FAQs
### Q1: How Do Provider Plugins Handle Large Data Volumes?
**A1**:  
Handling large data volumes efficiently is vital for Provider Plugins to maintain performance and prevent bottlenecks. Here are strategies to manage large datasets:

#### Pagination:
Retrieve data in manageable chunks rather than all at once to reduce memory consumption.

**Example:**

```python
def gather_data(self) -> Result:
    all_data = []
    paginator = self.ec2_client.get_paginator('describe_instances')
    for page in paginator.paginate():
        all_data.extend(page['Reservations'])
    return Result(..., details={"instances": all_data}, ...)
```

#### Streaming:
Stream data directly to consumers or storage to avoid loading everything into memory.

#### Data Filtering:
Collect only the necessary data by applying filters during the data gathering process.

**Example:**

```python
def gather_data(self) -> Result:
    filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
    response = self.ec2_client.describe_instances(Filters=filters)
    # Process filtered data
    return Result(...)
```

#### Compression:
Compress data before storing or transmitting to reduce size.

#### Asynchronous Processing:
Utilize asynchronous programming to handle data gathering tasks concurrently, improving throughput.

**Example with asyncio:**

```python
import asyncio

async def gather_data(self) -> Result:
    tasks = [self.fetch_data(instance_id) for instance_id in self.instance_ids]
    results = await asyncio.gather(*tasks)
    # Aggregate results
    return Result(...)
```

#### Efficient Data Structures:
Use optimized data structures and algorithms to process data efficiently.

#### Resource Management:
Monitor and manage system resources (CPU, memory) to prevent overloads during large data operations.

#### Best Practices:
- **Benchmarking**: Regularly benchmark your data gathering methods to identify and address performance issues.
- **Scalability**: Design your Provider Plugins to scale horizontally if necessary, distributing data processing across multiple instances.
- **Monitoring**: Implement monitoring to track data processing metrics and detect potential bottlenecks early.

---

### Q2: Can Provider Plugins Have Dependencies?
**A2**:  
Yes, Provider Plugins can specify dependencies using the `uses` field in their TOML configuration files. This allows a Provider Plugin to depend on other plugins, such as handlers or additional data sources. Managing dependencies ensures that all required plugins are loaded and initialized in the correct order before the Provider Plugin executes its data gathering logic.

**Example:**

```toml
[info]
name = "ec2_provider"
module = "ec2_provider"
class_name = "EC2Provider"
type = "provider"
uses = ["general"]
```

In this example, the `ec2_provider` plugin depends on the general handler and a hypothetical `credentials_manager` plugin.

---

### Q3: Can I Use Multiple Provider Plugins in OpsBox?
**A3**:  
Yes, OpsBox supports the use of multiple Provider Plugins simultaneously. This allows you to gather data from various infrastructure backends within the same pipeline. Each Provider Plugin operates independently, collecting data from its designated source, which can then be utilized by other plugins for processing and compliance checks.

**Example Scenario**:

- **Provider Plugins**:
    - `ec2_provider`: Gathers data from AWS EC2 instances.
    - `s3_provider`: Gathers data from AWS S3 buckets.
  
- **Pipeline Flow**:
    - `idle_instances` collects EC2 data.
    - `unused_storage` collects S3 data.
    - Input Plugins format the data.
    
## Best Practices

- **Consistent Naming:** Ensure that plugin names are unique and descriptive to avoid conflicts and enhance readability.
- **Secure Credentials:** Never hard-code sensitive information like API keys. Use secure methods to inject credentials into your plugin configuration.
- **Comprehensive Documentation:** Document your plugin's purpose, configuration options, and any dependencies to aid other developers and users.
- **Error Handling:** Implement robust error handling within the `gather_data` method to gracefully manage failures and provide meaningful log messages.
- **Testing:** Rigorously test your Provider plugin to ensure it accurately collects and formats data as expected.
---

By following this guide, you can effectively create Provider plugins that integrate seamlessly with OpsBox, ensuring reliable data collection and enhancing the overall functionality of your infrastructure management workflows.
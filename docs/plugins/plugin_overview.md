
# Opsbox Plugin System Overview

Welcome to Opsbox, where our plugin-based architecture makes cloud infrastructure management seamless and efficient! Let’s dive into how Opsbox uses its flexible plugin system to keep everything composable and extendable.

## Types of Plugins

At the core of Opsbox are *handlers*, plugins that specify and handle other types of plugins.
They implement functions that can handle many plugin types and structures.

Right now we have 2 handlers built, the **general** and **rego** handlers.

Let's go over these handlers and what they can be used for.

### *General Handler*
These plugins use the general handler, which handles code not specifically related to rego checks and general-use plugins that don't need to define their own hookspecs.

##### 1. Providers
Providers act as data sources (e.g., EC2, S3, etc.). They gather information from external sources and forward them to plugins that use them.

##### 2. Inputs
Inputs can collect data from a plugin and proccess them or produce their own data, but they are always the start of a pipeline. They provide formatted results that other plugins can use.

##### 3. Assistants
Assistants process, transform, and enhance the results from inputs. They act as intermediaries, refining the data for better analysis and decision-making.

##### 4. Outputs
Outputs handle the final formatted results, directing them to specified destinations (e.g., Jira, text files, etc.).

### *Rego Handler*
Allows for connection and proccessing of rego-formatted inputs called rego checks into the pipeline.
Rego-based plugins use the Open Policy Agent to execute and gather details from associated rego code. 

##### Check
A rego check collects data from a provider and executes given rego code on that data using a trusted OPA server.

By combining these plugin types, you can create a seamless pipeline for automatically generating and managing cloud infrastructure.

## Building a Pipeline
A pipeline in Opsbox is a series of plugins executed in a defined sequence to produce desired outcomes. Each pipeline consists of three main components:

### 1. Input Plugins
These are the primary inputs/checks you want to run. They form the foundation of your analysis and are specified as a comma-separated list in the first argument.

### 2. Assistants
These plugins process the results from the input results. They are executed in left-to-right order, refining and expanding upon the data.

### 3. Outputs
Outputs handle the final results, directing them to their intended destinations. These are also specified as a comma-separated list.

### Pipeline Definition Format
Pipelines are defined using the following format:
```
check_1,check_2-assistant_1-assistant_2-output_1,output_2
```

### Example Pipeline
Suppose we want to analyze idle EC2 instances, have an OpenAI assistant provide cost-saving recommendations, and output the results to Jira and a text file. Our pipeline would look like this:
```
idle_instances-cost_savings-text_file,jira
```

In this example:

- `idle_instances` is our Rego check input.
- `cost_savings` is our cost-analyzing assistant.
- `text_file,jira` are our output destinations.

With Opsbox’s flexible plugin system, you can create powerful, automated pipelines tailored to your cloud infrastructure needs! 🚀
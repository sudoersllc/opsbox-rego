# Guide for Testing Plugins That Use the Rego Handler in OpsBox

This guide explains how to test **plugins that use the Rego handler** in OpsBox using `pytest`. Rego plugins are designed to apply policy checks written in Rego, using Open Policy Agent (OPA) to evaluate data gathered by provider plugins. The **Rego handler** manages the execution of these Rego plugins, including policy uploads, evaluation, and result formatting.

We will cover testing both the Rego handler and plugins that use it, utilizing mocks and test fixtures to simulate the execution of Rego policies in a controlled environment.

---

## Key Concepts

When testing plugins that use the Rego handler, focus on these key aspects:

- **Rego Policy Execution**: Ensure the plugin runs its Rego policy file using OPA and applies the check on the given test data.
- **Result Formatting**: Confirm that the results of the policy checks are processed and formatted as expected.

---

## Testing Setup

Before running tests, make sure `pytest` is installed:

```bash
uv add pytest
```
---

## Example Rego Plugin

Here’s a basic Rego plugin that applies a compliance check using a Rego policy file.

### Rego Plugin Code

```python
class ComplianceRegoPlugin:
    """A Rego plugin that applies compliance checks."""

    def grab_config(self):
        return ComplianceRegoConfig
    
    def set_data(self, config):
        """Set configuration data for the Rego plugin."""
        self.config = config

    def report_findings(self, result: Result) -> Result:
        """Format and report the findings from the Rego check."""
        result.formatted = f"Compliance check {self.config.rego_file}: {result.result_description}"
        return result

class ComplianceRegoConfig(BaseModel):
    rego_file: str
    description: str
```

This plugin uses a Rego policy file (`rego_file`) to apply compliance checks and formats the result with `report_findings`.

---

## Testing Rego Plugin Using the Rego Handler

We will create tests to validate the entire flow of the Rego plugin using the Rego handler, including:

- Gathering data from a provider.
- Applying a Rego policy.
- Formatting the results.

### Example Test: Running a Rego Plugin with Provider Data

This test simulates how a Rego plugin gathers data from a provider plugin and applies a compliance check using the Rego handler.

```python
import pytest
from core.plugins import Result, PLuginFlow
from rego_handler import RegoHandler
from tests.mocks import MockPlugin, MockConfig

class MockProviderPlugin:
    """A mock provider plugin that gathers data."""

    def grab_config(self):
        return ProviderConfig

    def set_data(self, config):
        self.config = config

    def gather_data(self):
        """Simulates gathering data from an external source."""
        return Result(
            relates_to="provider",
            result_name="ProviderData",
            result_description="Gathered data from provider",
            details={"is_compliant": {"status": "compliant"}},
            formatted=""
        )

class ProviderConfig(BaseModel):
    api_key: str

def test_compliance_rego_plugin():
    """Test the Rego plugin with provider data."""

    # Mock the Rego plugin configuration
    mock_rego_extra = {
        "rego":{
            "rego_file": "compliance_policy.rego",
            "description": "Check compliance of provider data"
        }
    }

    # Mock the provider plugin configuration
    mock_provider_config = {
        "api_key": "mock_api_key"
    }

    # Create a mock provider plugin
    provider_plugin = MockPlugin(
        MockProviderPlugin, 
        "provider", 
        mock_provider_config
        )

    # Create a mock Rego plugin
    rego_plugin = MockPlugin(
        ComplianceRegoPlugin, 
        "rego", 
        {},
        uses = [provider_plugin.name],
        extra = mock_rego_extra
        )

    # Mock the Rego handler
    handler = RegoHandler()

    # make a fake plugin flow
    mock_flow = PluginFlow(input_plugins=[rego_plugin.name])

    # Mock registry with provider plugin
    mock_registry = MockRegistry(flow = mock_flow, plugins = [provider_plugin,])

    # Step 1: Run the Rego plugin to check compliance on provider data
    results = handler.process_plugin(rego_plugin, [], mock_registry)

    # Assert the results of the policy check
    assert results[0].result_name == "provider" 
    assert results[0].details == {"compliance_data": {"status": "compliant"}}
    assert results[0].formatted == "Compliance check compliance_policy.rego: Check compliance of provider data"
```

### Explanation

- **MockPlugin**: We use `MockPlugin` to simulate both the **provider plugin** (which gathers data) and the **Rego plugin** (which applies the policy).
- **MockRegistry**: Simulates the registry that contains the provider plugin, allowing the Rego handler to access the provider's data.
- **handler.process_plugin**: This method is the key function being tested. It triggers the Rego plugin to gather data from the provider and apply the Rego policy.

### Expected Output

The Rego plugin should gather data from the provider and apply the compliance policy. It will format the result based on the findings and return a compliant or non-compliant result.

---

## Testing Rego Policy Upload and Removal

We need to verify that the Rego policy is correctly uploaded to OPA before the check and removed after the check.

### Example Test: Policy Upload and Cleanup

```python
from unittest import mock
import requests

def test_rego_policy_upload_and_cleanup(mocker):
    """Test that the Rego policy is uploaded and removed from OPA correctly."""

    # Mock Rego handler configuration
    mock_rego_config = {
        "opa_upload_url": "http://localhost:8181/v1/policies",
        "opa_apply_url": "http://localhost:8181/v1/data"
    }

    # Mock Rego plugin
    rego_plugin = MockPlugin(ComplianceRegoPlugin, "rego", {"rego_file": "compliance_policy.rego", "description": "Compliance check"})

    # Create the Rego handler and set its config
    handler = RegoHandler()
    handler.set_data(mock_rego_config)

    # Mock the OPA policy upload and delete requests
    mocker.patch("requests.put", return_value=mock.Mock(status_code=200))
    mocker.patch("requests.delete", return_value=mock.Mock(status_code=200))

    # Use temp_policy to simulate policy upload and cleanup
    with handler.temp_policy(rego_plugin.extra["rego"], Path("/path/to/compliance_policy.rego"), handler.config.opa_upload_url):
        pass  # Simulate applying the policy

    # Assert that the policy was uploaded
    requests.put.assert_called_once_with(
        "http://localhost:8181/v1/policies/compliance_policy",
        data=mock.ANY,
        headers={"Content-Type": "text/plain"},
        timeout=20
    )

    # Assert that the policy was removed
    requests.delete.assert_called_once_with(
        "http://localhost:8181/v1/policies/compliance_policy",
        headers={"Content-Type": "text/plain"},
        timeout=20
    )
```

### Explanation

- **Mock OPA Requests**: We mock OPA API requests (`requests.put` and `requests.delete`) to simulate the upload and removal of Rego policies.
- **temp_policy**: This context manager in the handler is tested to ensure that the policy is uploaded before use and deleted after the check.

### Expected Output

The policy should be successfully uploaded and then removed after the Rego check is completed.

---

## Running the Tests

To run all the tests for plugins that use the Rego handler, use:

```bash
pytest
```

You can run specific tests with:

```bash
pytest test/test_compliance_rego_plugin.py
```

You can also run specific functions in a test file:

```bash
pytest test/test_compliance_rego_plugin.py::test_compliance_rego_plugin
```

---

## Conclusion

In this guide, we demonstrated how to:

1. **Test Rego plugins** using the Rego handler, verifying that they can apply policies and gather data from provider plugins.
2. **Test Rego policy uploads and cleanup**, ensuring that policies are correctly handled by OPA before and after checks.
3. **Use mocks** like `MockPlugin`, `MockRegistry`, and `MockConfig` to simulate plugin behavior and test interactions with the Rego handler.

These tests ensure that Rego plugins function as expected in the OpsBox pipeline, correctly applying policies to data and formatting results in compliance checks.
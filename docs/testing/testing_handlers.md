## Creating New Tests for Handlers

When writing new tests for handlers, ensure that you cover the following components:

1. **Hook Registration**: Test that the handler correctly registers and processes hooks from plugins.
2. **Process Plugin Logic**: Verify that the `process_plugin` method works correctly and invokes the appropriate plugin functionality based on the plugin type.
3. **Plugin Loading**: Ensure that the handler can load and manage plugins correctly.

### Example: Test for Handler Hook

```python
import pytest
from pluggy import PluginManager
from opsbox.general_handler import GeneralHandler

@pytest.fixture
def plugin_manager():
    """Fixture for setting up the plugin manager."""
    manager = PluginManager("opsbox")
    return manager

def test_add_hookspecs(plugin_manager):
    """Test that the handler correctly registers hooks."""
    handler = GeneralHandler()
    handler.add_hookspecs(plugin_manager)
    assert plugin_manager.get_hookspecs() is not None
```

### Example: Test for `process_plugin`

```python
def test_process_plugin(plugin_manager):
    """Test that the handler processes plugins correctly."""
    handler = GeneralHandler()
    plugin = MockPlugin(type="input")
    handler.process_plugin(plugin, prior_results=[], registry=MockRegistry())
    assert plugin.was_processed == True
```

In this example, `MockPlugin` is a class from the `tests/mocks.py` file used to simulate plugins in the sysyem.

### Running Your New Tests

After creating new tests, you can run them just like any other test:

```bash
pytest test/general_handler/test_hooks.py
```
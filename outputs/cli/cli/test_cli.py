import pytest
from unittest.mock import patch
from opsbox import Result
from .cli.cli import CLIOutput # type: ignore

@pytest.fixture
def cli_plugin():
    return CLIOutput()

def test_proccess_results(cli_plugin):
    @pytest.fixture
    def cli_plugin():
        return CLIOutput()

    def test_proccess_results(cli_plugin):
        results = [
            Result(
                relates_to="case1",
                result_name="res1",
                result_description="description1",
                details={"foo": "bar"},
                formatted="some formatted text"
            ),
            Result(
                relates_to="case2",
                result_name="res2",
                result_description="description2",
                details={"baz": 123},
                formatted="other formatted text"
            ),
        ]

        with patch("opsbox.cli.console.print") as mock_print, patch("opsbox.cli.console.rule") as mock_rule:
            cli_plugin.proccess_results(results)
            
            mock_rule.assert_any_call("CLI output")
            mock_print.assert_any_call("\n[bold green]You have 2 results from the following plugins:[/bold green] [red]['res1', 'res2'][/red]\n")
            
            for result in results:
                mock_rule.assert_any_call(f"[bold cyan]{result.result_name}[/bold cyan]")
                mock_print.assert_any_call(result.details)
                mock_rule.assert_any_call()

    def test_proccess_results_empty(cli_plugin):
        results = []

        with patch("opsbox.cli.console.print") as mock_print, patch("opsbox.cli.console.rule") as mock_rule:
            cli_plugin.proccess_results(results)
            
            mock_rule.assert_any_call("CLI output")
            mock_print.assert_any_call("\n[bold green]You have 0 results from the following plugins:[/bold green] [red][][/red]\n")
            cli_plugin.proccess_results(results)
            
            mock_rule.assert_any_call("CLI output")
            mock_print.assert_any_call("\n[bold green]You have 0 results from the following plugins:[/bold green] [red][][/red]\n")

from pluggy import HookimplMarker
from loguru import logger
from opsbox import Result
from opsbox.cli import console
from rich.pretty import Pretty

hookimpl = HookimplMarker("opsbox")


class CLIOutput:
    """Plugin for outputting results to the CLI."""

    def __init__(self):
        pass

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Prints the check results.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """
        console.rule("CLI output")
        resultant_plugins = [item.result_name for item in results]
        console.print(
            f"\n[bold green]You have {len(results)} results from the following plugins:[/bold green] [red]{resultant_plugins}[/red]\n"
        )
        for result in results:
            console.rule(f"[bold cyan]{result.result_name}[/bold cyan]")
            console.print(Pretty(result.details))
            console.rule()

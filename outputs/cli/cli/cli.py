from pluggy import HookimplMarker
from loguru import logger
from core.plugins import Result

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
        logger.info("Check Results:")
        for result in results:
            logger.info(result.details)

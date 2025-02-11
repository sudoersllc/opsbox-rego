from pluggy import HookimplMarker
from pydantic import BaseModel, Field
import os
from loguru import logger
from opsbox import Result
from typing import Annotated
import textwrap


hookimpl = HookimplMarker("opsbox")

class TextFileOutput:
    """
    Plugin for writing results to text files.
    """
    def __init__(self):
        pass
    
    @hookimpl
    def grab_config(self):
        """
        Return the plugin's configuration
        """
        class TextFileConfig(BaseModel):
            """Configuration for the CLI output."""
            output_folder: Annotated[
                str | None, 
                Field(default="./findings/", description="The folder to output the results to.")
            ]
            pass
        return TextFileConfig
    
    @hookimpl
    def activate(self):
        """
        Initialize the plugin.
        """
        #check if the output folder exists
        if not os.path.exists(self.model.output_folder):
            os.makedirs(self.model.output_folder) # create the folder if it doesn't exist


    @hookimpl
    def set_data(self, model: BaseModel):
        """
        Set the data for the plugin based on the model.
        """
        self.model = model
        
    def proccess_results(self, results: list["Result"]):
        """
        Writes the check results.

        Args:
            results (list[Result]): The formatted results from the checks.
        """
        logger.info("Writing results to text files")
        logger.success(results)
        for result in results:
            module_out = f"{self.model.output_folder}/{result.relates_to}"
            if not os.path.exists(module_out):
                os.makedirs(module_out)
            with open(f"{module_out}/{result.result_name}.txt", "w", encoding="utf-8") as f:
                logger.info(f"Writing results for {result.result_name} to {module_out}/{result.result_name}.txt")
                clean_text = textwrap.dedent(result.formatted)
                f.write(clean_text)
        logger.success("Results written to text files!")
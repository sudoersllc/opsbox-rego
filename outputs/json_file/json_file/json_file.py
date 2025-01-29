from pluggy import HookimplMarker
from pydantic import BaseModel, Field
import os
from loguru import logger
from opsbox import Result
from typing import Annotated
import json


hookimpl = HookimplMarker("opsbox")

class JSONFileOutput:
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
        class JSONFileConfig(BaseModel):
            """Configuration for the CLI output."""
            output_folder: Annotated[
                str | None, 
                Field(default="./findings/", description="The folder to output the results to.", required=False)
            ]
            pass
        return JSONFileConfig
    
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
        Writes the check results as JSON files.

        Args:
            results (List[Result]): The formatted results from the checks.
        """
        logger.info("Writing results to JSON files")
        logger.debug(f"Total results to process: {len(results)}")

        for result in results:
            # Define the output directory path
            module_out = os.path.join(self.model.output_folder, result.relates_to)
            
            # Create the directory if it doesn't exist
            os.makedirs(module_out, exist_ok=True)
            
            # Define the JSON file path
            json_file_path = os.path.join(module_out, f"{result.result_name}.json")
            
            logger.info(f"Writing results for '{result.result_name}' to '{json_file_path}'")
            
            try:
                # Convert the Result object to a dictionary using Pydantic's .dict()
                result_data = result.dict()

                # Optionally, if you want to exclude None values or use other Pydantic features:
                # result_data = result.dict(exclude_none=True)

                # Write the dictionary to a JSON file with indentation for readability
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, indent=2)
                    
                logger.debug(f"Successfully wrote JSON for '{result.result_name}'")
                    
            except TypeError as e:
                logger.error(f"Failed to serialize Result '{result.result_name}' to JSON: {e}")
            except IOError as e:
                logger.error(f"IO error while writing to '{json_file_path}': {e}")
        
        logger.info("Results successfully written to JSON files!")
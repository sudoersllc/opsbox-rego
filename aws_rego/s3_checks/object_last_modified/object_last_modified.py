from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ObjectLastModifiedConfig(BaseModel):
    s3_last_modified_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago an object has to remain unmodified for it to be considered old. Default is 90 days.",
        ),
    ]


class ObjectLastModified:
    """Plugin for identifying S3 objects that have not been modified in a long time."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return ObjectLastModifiedConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()

    @hookimpl
    def inject_data(self, data: "Result") -> "Result":
        """Inject data into the plugin.

        Args:
            data (Result): The data to inject into the plugin.

        Returns:
            Result: The data with the injected values.
        """
        timestamp = int(self.conf["s3_last_modified_date_threshold"].timestamp())
        data.details["input"]["s3_last_modified_date_threshold"] = timestamp
        return data
    
    def format_data(self, input: "Result") -> dict:
        """Format the data for the plugin.

        Args:
            input (Result): The input data to format.

        Returns:
            dict: The formatted data.
        """
        # Format the data as needed
        details = input.details["input"]
        total = len(details["objects"])
        std_and_old = [obj for obj in details["objects"] if obj["StorageClass"] == "STANDARD" and obj["LastModified"] < self.conf["s3_last_modified_date_threshold"].timestamp()]
        percentage = (len(std_and_old) / total) * 100 if total > 0 else 0
        formatted_data = {
            "percentage_standard_and_old": percentage,
            "standard_and_old_objects": std_and_old,
            "total_objects": total,
        }
        return formatted_data

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result containing the findings.
        """
        findings = self.format_data(data)

        standard_and_old_objects = []
        if findings:
            objects = findings.get("standard_and_old_objects", [])
            for obj in objects:
                if isinstance(obj, dict) and "Key" in obj and "StorageClass" in obj:
                    object_obj = {obj["Key"]: {"StorageClass": obj["StorageClass"]}}
                    standard_and_old_objects.append(object_obj)
                else:
                    logger.error(f"Unexpected format for object: {obj}")
        try:
            objects_yaml = yaml.dump(standard_and_old_objects, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting bucket details: {e}")
            raise e

        # Correctly access percentage and handle missing keys
        percentage_old = findings.get("percentage_standard_and_old", 0)
        template = """The following S3 objects have not been modified for a long time:
{objects}
Percentage of total old objects: {percentage_old}%"""

        if findings:
            return Result(
                relates_to="s3",
                result_name="object_last_modified",
                result_description="S3 Objects that have not been modified in a long time",
                details=findings,
                formatted=template.format(
                    objects=objects_yaml, percentage_old=percentage_old
                ),
            )
        else:
            return Result(
                relates_to="s3",
                result_name="object_last_modified",
                result_description="S3 Objects that have not been modified in a long time",
                details=findings,
                formatted="No old S3 objects found.",
            )

from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class ObjectLastModified:
    """Plugin for identifying S3 objects that have not been modified in a long time."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            Result: The formatted result containing the findings.
        """
        findings = data.details

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
                details=data.details,
                formatted=template.format(objects=objects_yaml, percentage_old=percentage_old),
            )
        else:
            return Result(
                relates_to="s3",
                result_name="object_last_modified",
                result_description="S3 Objects that have not been modified in a long time",
                details=data.details,
                formatted="No old S3 objects found.",
            )

import yaml
from loguru import logger
from opsbox import Result


class StrayEbs:
    """Formatting for the stray_ebs rego check."""

    def format_results(self, input: Result) -> dict:
        input = input.details["input"]
        details = [volume for volume in input["volumes"] if volume["state"] != "in-use"]
        return details


    def report_findings(self, data: Result) -> Result:
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        volumes = []
        findings = self.format_results(data)
        for volume in findings:
            volume_obj = {
                volume["volume_id"]: {
                    "create_time": volume["create_time"],
                    "region": volume["region"],
                    "state": volume["state"],
                    "size": f"{volume['size']}MB",
                    "tags": volume["tags"],
                }
            }
            volumes.append(volume_obj)
            try:
                volume_yaml = yaml.dump(volumes, default_flow_style=False)
            except Exception as e:
                logger.error(f"Error formatting volume details: {e}")
            template = """The following EBS volumes are unused. please check if they can be deleted or downsized: \n 
 
{volumes}"""

        result = data
        if findings:
            result.formatted = template.format(volumes=volume_yaml)
        else:
            result.formatted = "No stray EBS volumes found."
        return Result(
            relates_to="ec2",
            result_name="stray_ebs",
            result_description="Stray EBS Volumes",
            details=volumes,
            formatted=result.formatted,
        )

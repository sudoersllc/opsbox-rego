import yaml
from loguru import logger

from core.plugins import Result


class StrayInstances:
    """Formatting for the stray_instances rego check."""

    def report_findings(self, data: Result) -> Result:
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """

        volumes = []
        print(data.details)
        formatted = ""
        if volumes:
            for volume in data.details:
                logger.success(volume)
                volume_obj = {
                    volume["volume_id"]: {
                        "create_time": volume["create_time"],
                        "region": volume["region"],
                        "state": volume["state"],
                        "size": f"{volume['size']}MB",
                    }
                }
                volumes.append(volume_obj)
                try:
                    volume_yaml = yaml.dump(volumes, default_flow_style=False)
                except Exception as e:
                    logger.error(f"Error formatting volume details: {e}")
                template = """The following EBS volumes are unused. 

                The data is presented in the following format:
                - volume_id:
                    create_time: create_time in ISO format
                    region: aws_region
                    state: current_state
                    size: size_in_mb

                {volumes}"""

            formatted = template.format(volumes=volume_yaml)
        else:
            formatted = "No Stray EC2 Instances."

        item = Result(
            relates_to="ec2",
            result_name="stray_instances",
            result_description="Stray EC2 Instances",
            details=data.details,
            formatted=formatted,
        )
        return item

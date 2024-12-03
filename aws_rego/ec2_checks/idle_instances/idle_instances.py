import yaml
from loguru import logger
from core.plugins import Result


class IdleInstances:
    """Plugin for identifying idle EC2 instances."""

    def report_findings(self, data: Result) -> Result:
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details
        instances = []
        for instance in findings:
            instance_obj = {
                instance["instance_id"]: {
                    "region": instance["region"],
                    "state": instance["state"],
                    "avg_cpu_utilization": instance["avg_cpu_utilization"],
                    "instance_type": instance["instance_type"],
                    "operating_system": instance["operating_system"],
                    "tags": instance["tags"],
                }
            }
            instances.append(instance_obj)
        try:
            instance_yaml = yaml.dump(instances, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting instance details: {e}")

        template = """The following EC2 instances are idle, with an average CPU utilization of less than 5%.
The data is presented in the following format:
- instance_id:
    region: region
    state: running
    avg_cpu_utilization:

{instances}"""

        if instances:
            return Result(
                relates_to="ec2",
                result_name="idle_instances",
                result_description="Idle EC2 Instances",
                details=data.details,
                formatted=template.format(instances=instance_yaml),
            )
        else:
            return Result(
                relates_to="ec2",
                result_name="idle_instances",
                result_description="Idle EC2 Instances",
                details=data.details,
                formatted="No idle EC2 instances found.",
            )

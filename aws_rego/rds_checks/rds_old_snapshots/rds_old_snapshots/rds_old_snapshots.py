from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RDSOldSnapshots:
    """Plugin for identifying old RDS instances."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = data.details

        old_snapshots = []
        if findings:
            snapshot = findings.get("rds_old_snapshots", [])
            for snapshot in snapshot:
                old_snapshots.append(
                    f"Snapshot: {snapshot['SnapshotIdentifier']} is older than a year. Created on: {snapshot['SnapshotCreateTime']}"  # noqa: E501
                )
            logger.success(f"Found {len(snapshot)} old snapshots.")
        try:
            old_snapshots_yaml = yaml.dump(old_snapshots, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error formatting idle_instances details: {e}")
            old_snapshots = ""

        template = """The following snapsshots have been created more than a year ago and should be checked for deletion:

{old_snapshots}"""  # noqa: E501

        if findings:
            return Result(
                relates_to="rds",
                result_name="old_snapshots",
                result_description="Old RDS Snapshots",
                details=data.details,
                formatted=template.format(old_snapshots=old_snapshots_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="old_snapshots",
                result_description="Old RDS Snapshots",
                details=data.details,
                formatted="No old RDS snapshots found.",
            )

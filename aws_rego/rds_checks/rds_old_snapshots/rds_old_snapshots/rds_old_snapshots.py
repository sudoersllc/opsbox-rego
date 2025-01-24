from pluggy import HookimplMarker
import yaml
from loguru import logger
from core.plugins import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RDSOldSnapshotsConfig(BaseModel):
    rds_old_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago a snapshot was created to be considered old. Default is 90 days.",
        ),
    ]

class RDSOldSnapshots:
    """Plugin for identifying old RDS instances."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return RDSOldSnapshotsConfig

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
        timestamp = int(self.conf["rds_old_date_threshold"].timestamp() * 1e9)
        data.details["input"]["rds_old_date_threshold"] = timestamp
        return data

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

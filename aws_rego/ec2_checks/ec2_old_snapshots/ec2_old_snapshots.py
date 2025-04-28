from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class EC2OldSnapshotsConfig(BaseModel):
    ec2_snapshot_old_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=90)),
            description="How long ago a snapshot was created to be considered old. Default is 90 days.",
        ),
    ]


class EC2OLD:
    """Plugin for identifying idle RDS instances."""

    @hookimpl
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""
        return EC2OldSnapshotsConfig

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model.

        Args:
            model (BaseModel): The model containing the data for the plugin."""
        self.conf = model.model_dump()


    def filter_snapshots(self, input: "Result") -> list:
        """Filter the snapshots based on the threshold.

        Args:
            input (Result): The input data containing the snapshots.

        Returns:
            list: A list of filtered snapshots.
        """
        # Filter snapshots older than the threshold
        details = input.details["input"]
        old_snapshots = [
            snapshot
            for snapshot in details["snapshots"]
            if datetime.fromisoformat(snapshot["start_time"]).timestamp() < self.conf["ec2_snapshot_old_threshold"].timestamp()
        ]
        details = {"ec2_old_snapshots": old_snapshots}
        return details


    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """
        findings = self.filter_snapshots(data)

        old_snapshots = []
        if findings:
            snapshot = findings.get("ec2_old_snapshots", [])
            for snapshot in snapshot:
                old_snapshots.append(
                    f"Snapshot: {snapshot['snapshot_id']} is older than a year. Created on: {snapshot['start_time']}"  # noqa: E501
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
                relates_to="ec2",
                result_name="old_snapshots",
                result_description="Old EC2 Snapshots",
                details=findings,
                formatted=template.format(old_snapshots=old_snapshots_yaml),
            )
        else:
            return Result(
                relates_to="ec2",
                result_name="old_snapshots",
                result_description="Old EC2 Snapshots",
                details=findings,
                formatted="No old EC2 snapshots found.",
            )

    @hookimpl
    def rego_location(self):
        return "ec2_old_snapshots.rego"

    @hookimpl
    def this_uses(self):
        return "opsbox_ec2_provider"

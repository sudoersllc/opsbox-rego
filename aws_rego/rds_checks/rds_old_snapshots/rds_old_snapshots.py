from pluggy import HookimplMarker
import yaml
from loguru import logger
from opsbox import Result
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime, timedelta
from typing import Dict, List

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class RDSOldSnapshotsConfig(BaseModel):
    rds_old_date_threshold: Annotated[
        datetime,
        Field(
            default=(datetime.now() - timedelta(days=10)),
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

    def find_old_rds_snapshots(self, result_obj: "Result") -> Dict[str, List[Dict]]:
        """
        Filter RDS snapshots that are older than the specified threshold date.
        
        Args:
            result_obj: Result object containing input data at result_obj.details["input"]
                - Input data should have 'rds_snapshots' as a list of lists of snapshot dictionaries
        
        Returns:
            A dictionary with a key 'rds_old_snapshots' containing the list of old snapshots
        """
        # Get the input data from the Result object
        input_data = result_obj.details["input"]

        # Flatten the nested list of snapshots
        flattened_snapshots = []
        for sublist in input_data.get('rds_snapshots', []):
            for snapshot in sublist:
                flattened_snapshots.append(snapshot)
        
        # Filter snapshots older than the threshold date
        old_snapshots = []
        
        # Use the configuration's threshold date directly
        threshold_date = self.conf["rds_old_date_threshold"].timestamp()
        
        for snapshot in flattened_snapshots:
            snapshot_create_time = datetime.fromisoformat(
                snapshot.get('SnapshotCreateTime').replace('Z', '+00:00')
            ).timestamp()

            if snapshot_create_time < threshold_date:
                old_snapshots.append(snapshot)
        
        # Combine results into a single report
        details = {"rds_old_snapshots": old_snapshots}
        logger.success(f"Found {len(old_snapshots)} old snapshots.")

        return details
    
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
        findings = self.find_old_rds_snapshots(data)

        old_snapshots = []
        if findings:
            snapshot = findings.get("rds_old_snapshots", [])
            for snapshot in snapshot:
                old_snapshots.append(
                    f"Snapshot: {snapshot['SnapshotIdentifier']} is older than a year. Created on: {snapshot['SnapshotCreateTime']}"  # noqa: E501
                )
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
                details=findings,
                formatted=template.format(old_snapshots=old_snapshots_yaml),
            )
        else:
            return Result(
                relates_to="rds",
                result_name="old_snapshots",
                result_description="Old RDS Snapshots",
                details=findings,
                formatted="No old RDS snapshots found.",
            )

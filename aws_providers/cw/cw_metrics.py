import boto3
from pydantic import BaseModel, Field
from pluggy import HookimplMarker
from concurrent.futures import ThreadPoolExecutor, as_completed


from opsbox import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class CWAvailableMetrics:
    """Plugin for gathering data related to AWS Cloudwatch Metrics.

    Attributes:
        client (boto3.client): The boto3 client for Cloudwatch.
        credentials (dict): A dictionary containing AWS access key, secret access key, and region.
    """

    @hookimpl
    def grab_config(self) -> BaseModel:
        """Return the configuration model for the plugin."""

        class CWConfig(BaseModel):
            """Configuration for the AWS Cloudwatch Metrics plugin."""

            aws_access_key_id: str = Field(..., description="AWS access key ID")
            aws_secret_access_key: str = Field(..., description="AWS secret access key")
            aws_region: str = Field(..., description="AWS region")

        return CWConfig

    @hookimpl
    def activate(self) -> None:
        """Activate the plugin."""
        credentials = self.credentials
        self.client = boto3.client(
            "cloudwatch",
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
            region_name=credentials["aws_region"],
        )

    @hookimpl
    def set_data(self, model: dict):
        """Set the credentials for the plugin."""
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self) -> "Result":
        """Gather the data for the plugin

        Returns:
            dict: The data in a format that can be used by the rego policy.
        """
        paginator = self.client.get_paginator("list_metrics")
        metric_list = []

        # Use ThreadPoolExecutor for multithreading
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._fetch_page, page): page for page in paginator.paginate()}
            for future in as_completed(futures):
                page_result = future.result()
                metric_list.extend(page_result)

        data = Result(
            relates_to="cloudwatch_metrics",
            result_name="cw_available_metrics",
            result_description="Gathered available metrics from Cloudwatch.",
            formatted="",
            details={"metrics": metric_list},
        )

        return data

    def _fetch_page(self, page) -> list:
        """Fetch a page of metrics.

        Args:
            page (dict): The page of metrics.

        Returns:
            list: The list of metrics.
        """
        # This method is called in a separate thread for each page
        return [metric for metric in page["Metrics"]]

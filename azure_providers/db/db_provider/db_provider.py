from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from loguru import logger
from typing import Annotated
from opsbox import Result
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.sql import SqlManagementClient

# Define a hook implementation marker for the "opsbox" plugin system
hookimpl = HookimplMarker("opsbox")


class AzureDBProvider:
    @hookimpl
    def grab_config(self):
        class AzureDBConfig(BaseModel):
            """Configuration schema for the Azure DB provider.

            Attributes:
                subscription_id (str): Azure subscription ID.
                resource_group (str): Azure resource group.
                db_name (str): Database name.
                server_name (str): Server name.
            """

            subscription_id: Annotated[str, Field(description="Azure subscription ID")]
            resource_group: Annotated[str, Field(description="Azure resource group.")]
            db_name: Annotated[str | None, Field(default=None, description="Database name. If not provided, all databases in resource group will be queried.")]
            server_name: Annotated[str | None, Field(default=None, description="Server name. If not provided, all servers in resource group will be queried.")]
            start_from: Annotated[datetime | None, Field(default=(datetime.utcnow() - timedelta(hours=48)), description="Datetime to start monitoring from. Defaults to 48 hours ago.")]

        return AzureDBConfig
    
    @hookimpl
    def activate(self) -> None:
        logger.info("Activating Azure DB provider...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        logger.info("Setting data for Azure DB provider...")
        self.credentials = model
        self.az_creds = DefaultAzureCredential()

    @hookimpl
    def gather_data(self):
        logger.info("Gathering data for Azure DB...")
        credentials = self.credentials

        logger.info("creating client")
        client = MonitorManagementClient(
            self.az_creds, credentials.subscription_id
        )

        db_uris = []

        if credentials.server_name is None or credentials.db_name is None:
            logger.info(f"Getting all servers in resource group {credentials.resource_group}")


            sql_client = SqlManagementClient(
                self.az_creds, credentials.subscription_id
            )

            servers = sql_client.servers.list_by_resource_group(credentials.resource_group)
            for server in servers:
                dbs = sql_client.databases.list_by_server(credentials.resource_group,server.name)
                logger.warning([x for x in dbs])
                db_uris.extend([record.id for record in dbs])
        else:
            db_uris.append(
                f"subscriptions/{credentials.subscription_id}/resourceGroups/{credentials.resource_group}/"
                f"providers/Microsoft.Sql/servers/{credentials.server_name}/databases/{credentials.db_name}"
            )

        metrics = [
    "cpu_percent", "physical_data_read_percent", "log_write_percent", "storage", "connection_successful", 
    "connection_failed", "connection_failed_user_error", "blocked_by_firewall", "availability", "deadlock", 
    "storage_percent", "xtp_storage_percent", "workers_percent", "sessions_percent", "sessions_count", 
    "cpu_limit", "cpu_used", "sqlserver_process_core_percent", "sqlserver_process_memory_percent", 
    "sql_instance_cpu_percent", "sql_instance_memory_percent", "tempdb_data_size", "tempdb_log_size", 
    "tempdb_log_used_percent", "app_cpu_billed", "app_cpu_percent", "app_memory_percent", 
    "allocated_data_storage", "free_amount_remaining", "free_amount_consumed"
]

        # Define the time range for the metrics
        end_time = datetime.utcnow()
        start_time = credentials.start_from

        main_dict = {}
        resources = []
        for resource_uri in db_uris:
            metrics_dict = {}
            for metric in metrics:
                logger.info(f"Retrieving metric: {metric}")
                metrics_data = client.metrics.list(
                    resource_uri,
                    timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                    interval='PT15M',  # Granularity of data points (e.g., 1 minute)
                    metricnames=metric,
                    aggregation='Average',
                )

                # average the time series data
                number_list = []
                for item in metrics_data.value:
                    for timeseries in item.timeseries:
                        for data in timeseries.data:
                            if data.average is not None:
                                number_list.append(data.average)

                if len(number_list) > 0:
                    average = sum(number_list) / len(number_list)
                else:
                    average = 0
                
                metrics_dict[metric] = average
                metrics_dict[metric+"_unit"] = metrics_data.value[0].type
            metrics_dict["uri"] = resource_uri
            resources.append(metrics_dict)

        resources = {
            'azure_sql_dbs': resources
        }

        resources= {
            "input": resources
        }
            
        result = Result(
            relates_to="Azure DB",
            result_name="Azure DB Metrics",
            result_description="Azure DB metrics",
            details=resources,
            formatted=''
        )
        return result



if __name__ == "__main__":
    import argparse

    # Initialize the Azure DB provider
    azure_db_provider = AzureDBProvider()

    # Grab the configuration for the Azure DB provider
    AzureDBConfig = azure_db_provider.grab_config()

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Azure DB Provider Configuration")
    parser.add_argument("--subscription_id", required=True, help="Azure subscription ID")
    parser.add_argument("--resource_group", required=True, help="Azure resource group")
    parser.add_argument("--db_name", required=True, help="Database name")
    parser.add_argument("--server_name", required=True, help="Server name")
    #parser.add_argument("--start_from", type=lambda s: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S'), default=(datetime.utcnow() - timedelta(hours=1)), help="Start from (ISO format)")

    args = parser.parse_args()

    # Set the configuration data for the Azure DB provider from cli args
    config = AzureDBConfig(
        subscription_id=args.subscription_id,
        resource_group=args.resource_group,
        db_name=args.db_name,
        server_name=args.server_name,
    )
    azure_db_provider.set_data(config)
    azure_db_provider.activate()

    # Gather data for the Azure DB provider
    azure_db_provider.gather_data()
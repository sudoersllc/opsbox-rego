import datetime
import yaml
from loguru import logger
from copy import deepcopy
from pydantic import BaseModel, Field

from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.program import LLMTextCompletionProgram

import boto3

from pluggy import HookimplMarker

from typing import cast

from opsbox import Result

hookimpl = HookimplMarker("opsbox")


class MetricsSubmodel(BaseModel):
    """Submodel for the metrics in the Cloudwatch Metrics plugin."""

    MetricName: str = Field(..., description="The name of the metric")
    Namespace: str = Field(..., description="The namespace of the metric")


class MetricsOutput(BaseModel):
    """Output model to give recommendations for analyzing Cloudwatch metrics for cost savings."""

    metrics_to_analyze: list[MetricsSubmodel] = Field(..., description="The metrics to analyze for cost savings.")


class Config(BaseModel):
    """Configuration for the AWS Cloudwatch Metrics plugin."""

    aws_access_key_id: str = Field(..., description="AWS access key ID")
    aws_secret_access_key: str = Field(..., description="AWS secret access key")
    aws_region: str = Field(..., description="AWS region")
    oai_key: str = Field(..., description="OpenAI API key")


class CWMetricInsights:
    """Formatting for the get_metrics rego check."""

    @hookimpl
    def activate(self) -> None:
        """Activate the plugin."""
        # setup boto3 client
        self.client = boto3.client(
            "cloudwatch",
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
            region_name=self.config.aws_region,
        )

        # setup OpenAI models
        llm = OpenAI(model="gpt-4o", api_key=self.config.oai_key, temperature=0.1)
        embedding = OpenAIEmbedding(model="text-embedding-3-small", api_key=self.config.oai_key)

        Settings.llm = llm
        Settings.embed_model = embedding

    @hookimpl
    def grab_config(self) -> BaseModel:
        """Return the configuration model for the plugin."""
        return Config

    @hookimpl
    def set_data(self, model: Config):
        """Set the credentials for the plugin."""
        self.config = model

    @hookimpl
    def process(self, data: list["Result"]) -> list["Result"]:
        """Gather data related to AWS Cloudwatch Metrics.

        Args:
            findings: CheckResult: The result of the rego check.

        Returns:
            str: The formatted result."""

        wanted_result = [result for result in data if result.result_name == "cw_available_metrics"][0]
        metrics_list = wanted_result.details.get("metrics", [])

        with open("metrics_list.json", "w") as f:
            f.write(str(metrics_list))

        # setup document for vector store index
        yaml_formatted = []

        for metric in metrics_list:
            metric_copy = deepcopy(metric)
            metric = metric_copy["MetricName"]
            del metric_copy["MetricName"]
            yaml_formatted.append({metric: metric})

        template = """Below are active cloudwatch metrics in this format-
- <MetricName>: //the name of the metric
    Dimensions:
        - Name: <Name> //the name of the dimension
        - Value : <Value> //the value of the dimension
    Namespace: <Namespace> //the namespace of the metric
...


{metrics}
"""

        document = template.format(metrics=yaml.dump(yaml_formatted, default_flow_style=False))

        logger.info("Selecting Clouwatch metrics to analyze for cost savings...")
        metrics_query = """What cloudwatch metrics should I analyze to gain insights into our deployments?
Include names of the metrics and their namespaces.
Include a chain-of-thought with reasoning."""
        doc = Document(text=document)
        logger.debug("Building the vector store index...")
        print(self.config)
        index = VectorStoreIndex.from_documents([doc], embed_model=Settings.embed_model)
        query_engine = index.as_query_engine(llm=Settings.llm)
        logger.debug("Querying the vector store index...")
        response = query_engine.query(metrics_query)

        logger.debug("Structuring the response...")
        temp_str = "Return the names of all of the mentioned metrics fomatted nicely: {metrics_to_analyze}"
        program = LLMTextCompletionProgram.from_defaults(
            output_cls=MetricsOutput,
            prompt_template_str=temp_str,
            verbose=True,
        )
        llm_response = program(metrics_to_analyze=str(response))

        # start time is 7 days ago
        start_time = datetime.datetime.now() - datetime.timedelta(days=7)
        end_time = datetime.datetime.now()

        # Get the metrics
        transformed_data: list[Document] = []

        logger.info("Fetching the metrics from Cloudwatch...")
        for metric in cast(list[MetricsSubmodel], llm_response.metrics_to_analyze):
            logger.trace(f"Fetching metric {metric}")
            response = self.client.get_metric_data(
                MetricDataQueries=[
                    {
                        "Id": "m1",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": metric.Namespace,  # Modify this based on your specific needs
                                "MetricName": metric.MetricName,
                            },
                            "Period": 300,
                            "Stat": "Average",
                        },
                        "Label": metric.MetricName,
                        "ReturnData": True,
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,  # Define end_time based on your requirements
                ScanBy="TimestampDescending",
            )

            # Process the CloudWatch data (e.g., log it, store it, analyze it)
            # save response to file
            response = response["MetricDataResults"][0]
            try:
                timestamps = response["Timestamps"]
                values = response["Values"]

                # Zipping and creating a list of dictionaries
                zipped_data = [{"timestamp": ts.isoformat(), "value": val} for ts, val in zip(timestamps, values)]
            except Exception as _:
                logger.warning(
                    f"Cloudwatch metric {metric.MetricName} in namespace {metric.Namespace} has no data available."
                )

            new_result = (
                f"Here is the time-series data for the cloudwatch metric {metric.MetricName} "
                f"in namespace {metric.Namespace}: \n{yaml.dump(zipped_data, default_flow_style=False)}"
            )
            doc = Document(
                text=new_result, metadata={"metric_name": metric.MetricName, "metric_namespace": metric.Namespace}
            )
            transformed_data.append(doc)

        logger.info("Synthesizing insights...")
        logger.debug("Building the vector store index...")

        index = VectorStoreIndex.from_documents(transformed_data, embed_model=Settings.embed_model)
        query_engine = index.as_query_engine(llm=Settings.llm)
        logger.debug("Querying the vector store index...")

        insights_query = """
**You are an extraordinary insight analysis expert.**  
Your job is to analyze the data from various Cloudwatch metrics to identify potential cost, performance, and security optimizations.

**If applicable, sort them by what would have the most impact.**  
Please include specific details on how benefits can be achieved by optimizing these metrics.  
Include all relevant metric names, their timestamps, and namespaces to ensure that the data can be easily located and referenced in the future.

**Key points to cover:**

- Identify all relevant metrics that affect performance, cost, and security.
- Sort these metrics based on their potential impact.
- Provide detailed explanations for how each metric impacts performance, cost, or security.
- Suggest actionable strategies to optimize these metrics, including any necessary steps and considerations.
- Include specific timestamps, metric names, and namespaces that can guide the user in locating this data in the future.
- Include insights into the current state of the system and how it can be improved.
- Be overly verbose if necessary, and ensure that all relevant data points are thoroughly covered.
- Provide a clear and concise summary of your findings at the end.
"""  # noqa: E501

        response = str(query_engine.query(insights_query))

        new_result = Result(
            result_name="cw_insights",
            formatted=response,
            details=wanted_result.details,
            relates_to="cw_metrics",
            result_description="Insights into the Cloudwatch metrics.",
        )
        return new_result

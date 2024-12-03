from typing import List
from llama_index.core import VectorStoreIndex, Document
from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
from core.config import AppConfig
from core.plugins import Result

# ruff: noqa: E501

hookimpl = HookimplMarker("opsbox")


class CostSavings:
    """Output model to give recommendations for cost savings."""

    query = """
You are an exceptional and highly detailed data cost savings expert. Your mission is to thoroughly analyze every piece of data available in the datastore files and uncover all possible cost-saving opportunities. It is your responsibility to ensure no data point is left unchecked, and every possible savings is identified.

Key Expectations:
Data Coverage: Review ALL types of data in the files, including but not limited to:

Snapshots
Volumes
Instances (running or stopped)
Unused or under-utilized resources
Any other storage objects or services that contribute to costs.
Thorough Review Process:

Ensure that all relevant identifiers, such as instance IDs, volume IDs, snapshot IDs, bucket names, and resource tags, are captured in your analysis. Every ID or reference that may contribute to cost analysis should be explicitly stated in your findings.
Identify and categorize each dataset by its cost impact potential, starting with those that offer the highest savings down to the smaller ones. Be specific about the criteria you use to determine the savings.
Detailed Calculations:

For each resource, break down the current cost versus the potential savings in a very detailed manner.
For each cost-saving suggestion, give a step-by-step breakdown of how those savings can be achieved. Explain the specific actions required, such as reducing storage, deleting snapshots, downsizing instances, optimizing reserved instances, etc.
For calculations, verify every assumption using cost calculation libraries or verified APIs, and detail how these calculations were arrived at (e.g., comparing current instance pricing with reserved pricing or identifying unused resources that can be removed).
Ensure you provide all related cost data points, such as hourly rates, GB per month pricing, and any other relevant unit costs.
Be Overly Verbose:

Explain each data point in great detail.
Offer insights or explanations that might not be immediately obvious. For example, explain why certain snapshots are redundant, or why a particular instance could be switched to a cheaper alternative.
Leave no stone unturned, from minor to major costs. Mention every relevant detail that could impact cost, no matter how small.
Avoid Missing Anything:

Absolutely nothing should be left out. Ensure every cost-saving opportunity is documented, including savings from:
Resource downsizing
Moving to different pricing models
Eliminating redundant resources
Snapshot and volume optimization
Networking costs
Resource tagging for better cost tracking
Others that may be hidden or not immediately obvious from the data.
Consider any related cost points, such as overhead from backups, scaling, and regional pricing differences.
Deliverables:
Present the complete breakdown of data and associated costs.
Include all IDs, such as resource IDs, volume IDs, and any other key identifiers, to ensure full traceability of the cost-saving recommendations.
For each recommendation, explicitly mention which files and datasets the recommendations pertain to.
Provide verbose explanations for each identified opportunity and detailed calculations for each cost-saving solution.
Remember, your goal is to provide a comprehensive, all-encompassing review of the entire data store, leaving nothing out. Go into as much detail as necessary, ensuring complete transparency in your findings.

"""

    @hookimpl
    def grab_config(self) -> BaseModel:
        """Return the configuration model for the plugin."""

        class cost_savingsConfig(BaseModel):
            """Configuration for the AWS Cloudwatch Metrics plugin."""

            arrigator: bool = Field(..., description="Whether to aggregate the data and generate one response.")
            discard_prior: bool = Field(
                False, description="Whether to discard the data before and leave only cost saving data."
            )

        return cost_savingsConfig

    @hookimpl
    def set_data(self, model: BaseModel):
        """Set the credentials for the plugin."""
        self.credentials = model.model_dump()

    def generate_recommendations(self, data: List["Result"]) -> List["Result"]:
        """Generate recommendations from OpenAI.

        Args:
            data: List[FormattedResult]: The data to process.
            arrigator: bool: Whether to aggregate the data and generate one response.

        Returns:
            List[FormattedResult]: The transformed data."""

        try:
            logger.info("Generating cost-saving recommendations from OpenAI")
            credentials = self.credentials
            appconfig = AppConfig()
            if appconfig.embed_model is not None:
                if credentials["arrigator"]:  # for aggregation
                    logger.trace("Generating recommendations for all items with vector index")
                    # Combine the text of all documents into one
                    divider = "\n-------------------\n"  # This is your divider line, customize as needed
                    combined_text = divider.join([item.formatted for item in data])
                    combined_doc = Document(text=combined_text)

                    # Create an index with this single combined document
                    index = VectorStoreIndex.from_documents([combined_doc], embed_model=appconfig.embed_model)
                    query_engine = index.as_query_engine(llm=appconfig.llm)

                    # Perform a single query across the combined document
                    response = query_engine.query(self.query)

                    # Extract the details from the response
                    details = []
                    for item in data:
                        if isinstance(item.details, dict):
                            details.append(item.details)
                        elif isinstance(item.details, list):
                            details.extend(item.details)

                    # Update all items with the same response
                    result = Result(
                        relates_to="cost_savings",
                        result_name="Cost Savings Aggregated",
                        result_description="Cost savings recommendations aggregated.",
                        details=details,
                        formatted=str(response),
                    )

                    # return the result
                    if credentials["discard_prior"]:
                        return [result]
                    else:
                        items = data.copy()
                        items.append(result)
                        return items
                else:
                    transformed_recs = []
                    for item in data:
                        logger.trace(f"Generating recommendations for {item.result_name} with vector index")
                        doc = Document(text=item.formatted)
                        index = VectorStoreIndex.from_documents([doc], embed_model=appconfig.embed_model)
                        query_engine = index.as_query_engine(llm=appconfig.llm)
                        response = query_engine.query(self.query)
                        item.formatted = str(response)
                        transformed_recs.append(item)

                    return transformed_recs

            else:  # no vector index
                if credentials["arrigator"]:
                    logger.trace("Generating recommendations for all items without vector index")
                    # Combine the text of all documents into one
                    divider = "\n-------------------\n"
                    combined_text = divider.join([item.formatted for item in data])
                    response = appconfig.llm.complete(combined_text + self.query)

                    # Extract the details from the response
                    details = []
                    for item in data:
                        if isinstance(item.details, dict):
                            details.append(item.details)
                        elif isinstance(item.details, list):
                            details.extend(item.details)

                    result = Result(
                        relates_to="cost_savings",
                        result_name="Cost Savings Aggregated",
                        result_description="Cost savings recommendations aggregated.",
                        details=details,
                        formatted=str(response),
                    )

                    # return the result
                    if credentials["discard_prior"]:
                        return [result]
                    else:
                        items = data.copy()
                        items.append(result)
                        return items
                else:
                    result_list = []
                    for item in data:
                        logger.trace(f"Generating recommendations for {item.result_name} without vector index")
                        response = appconfig.llm.complete(item.formatted + self.query)
                        result = Result(
                            relates_to=f"cost_savings_{item.result_name}",
                            result_name="Cost Savings",
                            result_description="Cost savings recommendations.",
                            details=item.details,
                            formatted=str(response),
                        )
                        result_list.append(result)

                    if credentials["discard_prior"]:
                        return result_list
                    else:
                        # insert list at beginning of list
                        new_list = data
                        new_list.append(result_list)
                        return new_list

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            logger.error(f"Error on line {e.__traceback__.tb_lineno}")

        return data

    def proccess_input(self, data: List["Result"]) -> List["Result"]:
        """Process the input data and generate recommendations.

        Args:
            data: List[FormattedResult]: The data to process.

        Returns:
            List[FormattedResult]: The transformed data."""

        return self.generate_recommendations(data)

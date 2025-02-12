from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger

import requests
from llama_index.core import VectorStoreIndex, Document
from opsbox import AppConfig
from llama_index.core.program import LLMTextCompletionProgram
from opsbox import Result
import json

from typing import Annotated

hookimpl = HookimplMarker("opsbox")



class PagerDutyOutput:
    """
    Plugin for sending results to PagerDuty
    """


    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """
        Return the plugin's configuration
        """


        class PagerDutyConfig(BaseModel):
            """Configuration for the PagerDuty output."""

            routing_key: Annotated[str, Field(description="The routing_key to use.")]
            create_description: Annotated[
                bool,
                Field(
                    description="Whether to create a description for pagerduty or just use the raw input as the payload.",
                    default=False,
                ),
            ]
            manual_severity: Annotated[
                str | None,
                Field(
                    description="The severity of the incident created.",
                    default="medium",
                ),
            ]

        return PagerDutyConfig

    @hookimpl
    def set_data(self, model: BaseModel):
        """
        Set the data for the plugin based on the model.
        """
        self.model = model
        self.credentials = model.model_dump()

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Send the results to PagerDuty.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """

        try:
            appconfig = AppConfig()
            credentials = self.credentials
            for result in results:
                body = ""

                if credentials["create_description"]:
                    # Create a description for the PagerDuty incident
                    if (
                        appconfig.embed_model is None
                    ):  # shove it all in if no embed model
                        templ: str = """    
                        Objective:
                        You are a meticulous PagerDuty incident creation assistant tasked with generating detailed PagerDuty payloads based on the cost savings recommendations provided to you in your vector store. Your goal is to create one payload per cost-saving recommendation, ensuring that the incident is clear, actionable, and concise for immediate attention.

                        Payload Structure:
                        Generate a PagerDuty payload in the following format:
                            "payload": {
                                "summary": "<Cost-saving recommendation summarized in one sentence>",
                                "severity": "critical",
                                "source": "<The AWS services, resources, or configurations involved>"
                            },
                        Message Generation:
                        The summary must be a single sentence that clearly states the cost-saving recommendation.
                        The source should specify the AWS service, resource, or configuration involved.
                        Guidelines:
                        Always maintain the language and phrasing used in the cost-saving recommendations as closely as possible for the summary.
                        Keep each summary concise, actionable, and no longer than a sentence.
                        Do not include implementation details, just the high-level recommendation and its source.
                    {document}
                    """  # noqa: E501
                        program = LLMTextCompletionProgram.from_defaults(
                            prompt_template_str=templ,
                            verbose=True,
                        )
                        llm_response = program(document=str(result.formatted))
                        body = llm_response
                        logger.success(body)

                        # Remove unwanted parts
                        body = body.replace("```json", "").replace("```", "").strip()

                        # Convert the string to a dictionary
                        body_dict = json.loads(body)  # Now body_dict is a dictionary

                        # Now access the 'payload' key
                        payload = body_dict["payload"]

                    else:  # use the embed model and query a simple vector store
                        docs: Document = []
                        docs.append(
                            Document(text=result.formatted, id=result.result_name)
                        )

                        index = VectorStoreIndex.from_documents(
                            docs, embed_model=appconfig.embed_model
                        )

                        # Query the index for detailed GitHub issue descriptions
                        github_query: str = """
                    **Objective:**
                    Objective:
                        You are a meticulous PagerDuty incident creation assistant tasked with generating detailed 
                        PagerDuty payloads based on the cost savings recommendations provided to you in 
                        your vector store.  Your goal is to create one payload per cost-saving recommendation,
                        ensuring that the incident is clear, actionable, and concise for immediate attention.

                        Payload Structure:
                        Generate a PagerDuty payload in the following format:
                            "payload": {
                                "summary": "<Cost-saving recommendation summarized in one sentence>",
                                "severity": "critical",
                                "source": "<The AWS services, resources, or configurations involved>"
                            },
                        Message Generation:
                        The summary must be a single sentence that clearly states the cost-saving recommendation.
                        The source should specify the AWS service, resource, or configuration involved.
                        Guidelines:
                        Always maintain the language and phrasing used in the cost-saving recommendations as closely as 
                        possible for the summary.
                        Keep each summary concise, actionable, and no longer than a sentence.
                        Do not include implementation details, just the high-level recommendation and its source.
                    """
                        logger.debug("Building the vector store index...")
                        query_engine = index.as_query_engine(llm=appconfig.llm)
                        response = query_engine.query(github_query)
                        body = str(
                            response
                        )  # Convert response to a string if necessary
                        # Remove unwanted parts
                        body = body.replace("```json", "").replace("```", "").strip()

                        # Convert the string to a dictionary
                        body_dict = json.loads(body)  # Now body_dict is a dictionary

                        # Now access the 'payload' key
                        payload = body_dict["payload"]

                else:  # just use the raw input as the payload
                    body = result.formatted
                    payload = {
                        "summary": body,
                        "severity": credentials["manual_severity"],
                        "source": f"{result.relates_to}",
                    }
                    if credentials["manual_severity"]:
                        payload["severity"] = credentials["manual_severity"]

            # Create the payload
            data = {
                "payload": {
                    "summary": payload["summary"],
                    "severity": payload["severity"],
                    "source": payload["source"],
                },
                "routing_key": self.model.routing_key,  # Make sure routing_key is set correctly
                "event_action": "trigger",
            }

            headers = {"Content-Type": "application/json"}

            # Send the POST request
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                data=json.dumps(data),
                headers=headers,
                timeout=15,
            )

            # Check the response
            if response.status_code == 202:
                print("Incident triggered successfully!")
            else:
                print(
                    f"Failed to trigger incident. Status code: {response.status_code}, Response: {response.text}"
                )

        except Exception as e:
            logger.error(f"Error sending Pagerduty: {e}")
            logger.error("Check your Pagerduty configuration and try again.")
            # log the line number of the error in the code
            logger.error(f"Error on line {e.__traceback__.tb_lineno}")
            return
        logger.success("Results sent via Pagerduty!")

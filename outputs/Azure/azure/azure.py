from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
import pandas as pd
import requests
import base64
import markdown
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.program import LLMTextCompletionProgram
from opsbox import AppConfig, Result


from typing import Annotated


hookimpl = HookimplMarker("opsbox")


class AzureOutput:
    """
    Plugin for sending check results to Azure DevOps.
    """

    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """
        Return the plugin's configuration.
        """

        class AzureDevOpsConfig(BaseModel):
            """Configuration for the Azure DevOps output."""

            azure_devops_token: Annotated[
                str, Field(description="The personal access token for Azure DevOps.")
            ]
            azure_devops_organization: Annotated[
                str, Field(description="The name of the Azure DevOps organization.")
            ]
            azure_devops_project: Annotated[
                str, Field(description="The name of the Azure DevOps project.")
            ]
            azure_devops_username: Annotated[
                str, Field(description="The username for Azure DevOps.")
            ]
            azure_devops_priority: Annotated[
                int, Field(description="The priority of the work item.", default=4)
            ]
            tags: Annotated[
                str | None,
                Field(description="The tags to apply to the work item.", default=None),
            ]
            create_description: Annotated[
                bool,
                Field(
                    description="Whether to create a description instead of an issue.",
                    default=False,
                ),
            ]

        return AzureDevOpsConfig

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
        Emails the check results to the specified email addresses.

        Args:
            results (list[Result]): The formatted results from the checks.
        """
        appconfig = AppConfig()
        azure_devops_url = f"https://dev.azure.com/{self.model.azure_devops_organization}/{self.model.azure_devops_project}/_apis/wit/workitems/$Issue?api-version=7.1-preview.3"
        base64_token = base64.b64encode(
            f"{self.model.azure_devops_username}:{self.model.azure_devops_token}".encode()
        ).decode()
        try:
            for result in results:
                # Prepare the file for upload
                file_name = f"{result['check_name']}.txt"
                with open(file_name, "w") as file:
                    file.write(result["formatted"])

                # Upload the file to Azure DevOps
                attachment_url = f"https://dev.azure.com/{self.model.azure_devops_organization}/{self.model.azure_devops_project}/_apis/wit/attachments?fileName={file_name}&api-version=7.1-preview.3"

                with open(file_name, "rb") as file_data:
                    attachment_response = requests.post(
                        attachment_url,
                        headers={
                            "Authorization": f"Basic {base64_token}",
                            "Content-Type": "application/octet-stream",
                        },
                        data=file_data,
                        timeout=15,
                    )

                if attachment_response.status_code in [200, 201]:
                    attachment_info = attachment_response.json()
                    attachment_url = attachment_info["url"]
                    print("File uploaded successfully.")
                else:
                    print(
                        f"Failed to upload file. Status Code: {attachment_response.status_code}"
                    )
                    print(attachment_response.text)
                credentials = self.credentials
                if credentials["create_description"]:
                    if appconfig.embed_model is None:
                        templ: str = """
                    **Objective:**
                    You are a meticulous Azure issue creation assistant tasked with generating detailed issue descriptions based on the cost savings recommendations provided to you in your vector store.
                    You are creating one issue per cost-saving recommendation.
                    Your goal is to create a clear, actionable, and detailed Azure issue that will help the development team implement these cost-saving measures effectively using the information from your vector store.

                    2. **Issue Body:**
                    - Write a detailed description that includes:
                        - The specific cost-saving recommendation.
                        - The AWS services, resources, or configurations involved.
                        - Relevant data points, such as resource utilization metrics or cost analysis, directly quoted from the recommendations.
                        - Specific implementation steps required to achieve the cost savings.
                        - Expected outcomes and success criteria.
                        - Potential risks or dependencies associated with the recommendation.
                    - Ensure that the language used in the issue body matches the exact wording and phrasing from the provided recommendations.

                    **Guidelines:**
                    - Maintain the exact language, wording, and phrasing used in the cost-saving recommendations for both the issue title and description.
                    - Organize the information effectively using bullet points, lists, and paragraphs as needed.
                    - Do not paraphrase or create your own language; instead, use the provided information verbatim to ensure accuracy and consistency.

                    **Output:**
                    - Provide a singular Azure issue, each with a clear detailed description, to enable the development team to start working on the cost-saving initiatives effectively.
                    {document}
                    """  # noqa: E501
                        program = LLMTextCompletionProgram.from_defaults(
                            output_cls=Document,
                            prompt_template_str=templ,
                            verbose=True,
                        )
                        program(document=str(text=result["formatted"]))
                    else:
                        docs: Document = []
                        docs.append(
                            Document(text=result["formatted"], id=result["check_name"])
                        )

                        index = VectorStoreIndex.from_documents(
                            docs, embed_model=appconfig.embed_model
                        )

                        # Query the index for detailed Azure issue descriptions
                        azure_query: str = """
                    **Objective:**
                    You are a meticulous Azure issue creation assistant tasked with generating detailed issue descriptions based on the cost savings recommendations provided to you in your vector store.
                    You are creating one issue per cost-saving recommendation.
                    Your goal is to create a clear, actionable, and detailed Azure issue that will help the development team implement these cost-saving measures effectively using the information from your vector store.

                    2. **Issue Body:**
                    - Write a detailed description that includes:
                        - The specific cost-saving recommendation.
                        - The AWS services, resources, or configurations involved.
                        - Relevant data points, such as resource utilization metrics or cost analysis, directly quoted from the recommendations.
                        - Specific implementation steps required to achieve the cost savings.
                        - Expected outcomes and success criteria.
                        - Potential risks or dependencies associated with the recommendation.
                    - Ensure that the language used in the issue body matches the exact wording and phrasing from the provided recommendations.

                    **Guidelines:**
                    - Maintain the exact language, wording, and phrasing used in the cost-saving recommendations for both the issue title and description.
                    - Organize the information effectively using bullet points, lists, and paragraphs as needed.
                    - Do not paraphrase or create your own language; instead, use the provided information verbatim to ensure accuracy and consistency.

                    **Output:**
                    - Provide a singular Azure issue, each with a clear detailed description, to enable the development team to start working on the cost-saving initiatives effectively.
                    """  # noqa: E501
                        logger.info(
                            "Querying the vector store index to create Azure issue descriptions..."
                        )
                        query_engine = index.as_query_engine(llm=appconfig.llm)
                        response = query_engine.query(azure_query)
                        body = str(response)
                else:
                    body = result["formatted"]

                # Create Azure DevOps work item

                headers = {
                    "Authorization": f"Basic {base64_token}",
                    "Content-Type": "application/json-patch+json",
                }
                body_html = markdown.markdown(body)

                # Get today's date for the title
                data = [
                    {
                        "op": "add",
                        "path": "/fields/System.Title",
                        "value": f"OpsBox Optimization Check - {pd.Timestamp.now().strftime('%Y-%m-%d')} - {result.get('check_name', 'Unnamed')}",
                    },
                    {
                        "op": "add",
                        "path": "/fields/System.Description",
                        "value": body_html,
                    },
                    {
                        "op": "add",
                        "path": "/fields/System.Tags",
                        "value": self.model.tags or "",
                    },
                    {
                        "op": "add",
                        "path": "/relations/-",
                        "value": {
                            "rel": "AttachedFile",
                            "url": attachment_url,
                            "attributes": {
                                "comment": "Attached file with detailed information"
                            },
                        },
                    },
                    {
                        "op": "add",
                        "path": "/fields/Microsoft.VSTS.Common.Priority",
                        "value": self.model.azure_devops_priority,
                    },
                ]

                # Make the POST request with optional parameters
                response = requests.post(
                    azure_devops_url, headers=headers, json=data, timeout=15
                )
                if response.status_code == 200:
                    logger.success(
                        f"Successfully created Azure DevOps work item: {response.json()['url']}"
                    )
                else:
                    logger.error(
                        f"Failed to create Azure DevOps work item: {response.status_code}"
                    )
                    logger.error(response.text)
                    logger.error(response.json())

        except Exception as e:
            logger.error(f"Error sending Ticket: {e}")
            logger.error("Check your Azure DevOps configuration and try again.")
            return
        logger.success("Results sent via Azure DevOps Tickets!")

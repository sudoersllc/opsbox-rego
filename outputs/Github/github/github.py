from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, Document
from opsbox import AppConfig
from llama_index.core.program import LLMTextCompletionProgram
from opsbox import Result
from typing import TYPE_CHECKING, Annotated

hookimpl = HookimplMarker("opsbox")

if TYPE_CHECKING:
    pass


class GithubOutput:
    """Plugin for sending check results via GitHub Tickets."""

    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class EmailConfig(BaseModel):
            """Configuration for the github output."""

            github_token: Annotated[
                str, Field(description="The token for the github user.")
            ]
            repo_owner: Annotated[
                str, Field(description="The owner of the repository.")
            ]
            repo_name: Annotated[str, Field(description="The name of the repository.")]
            labels: Annotated[
                str | None,
                Field(description="The labels to apply to the issue.", default=None),
            ]
            create_description: Annotated[
                bool,
                Field(
                    description="Whether to create a description instead of an issue.",
                    default=False,
                ),
            ]

        return EmailConfig

    @hookimpl
    def set_data(self, model: BaseModel):
        """Set the data for the plugin based on the model."""
        self.model = model
        self.credentials = model.model_dump()

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Emails the check results to the specified email addresses.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """
        try:
            appconfig = AppConfig()
            for result in results:
                body = ""
                gist_url = ""

                # Create a GitHub Gist for the formatted result
                gist_data = {
                    "description": f"Gist for {result.result_name}",
                    "public": True,
                    "files": {
                        f"{result.result_name}.txt": {"content": result.formatted}
                    },
                }

                gist_response = requests.post(
                    "https://api.github.com/gists",
                    headers={
                        "Authorization": f"token {self.model.github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json=gist_data,
                    timeout=15,
                )

                if gist_response.status_code == 201:
                    gist_url = gist_response.json().get("html_url", "")
                    logger.success(f"Successfully created Gist: {gist_url}")
                else:
                    logger.error(f"Failed to create Gist: {gist_response.status_code}")
                    logger.error(gist_response.json())

                credentials = self.credentials

                if credentials["create_description"]:
                    if appconfig.embed_model is None:
                        templ: str = """
                    **Objective:**
                    You are a meticulous GitHub issue creation assistant tasked with generating detailed issue descriptions based on the cost savings recommendations provided to you in your vector store.
                    You are creating one issue per cost-saving recommendation.
                    Your goal is to create a clear, actionable, and detailed GitHub issue that will help the development team implement these cost-saving measures effectively using the information from your vector store.

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
                    - Provide a singular GitHub issue, each with a clear detailed description, to enable the development team to start working on the cost-saving initiatives effectively.
                    {document}
                    """  # noqa: E501
                        program = LLMTextCompletionProgram.from_defaults(
                            prompt_template_str=templ,
                            verbose=True,
                        )
                        llm_response = program(document=str(result.formatted))
                        body = llm_response.choices[0].text
                    else:
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
                    You are a meticulous GitHub issue creation assistant tasked with generating detailed issue descriptions based on the cost savings recommendations provided to you in your vector store.
                    You are creating one issue per cost-saving recommendation.
                    Your goal is to create a clear, actionable, and detailed GitHub issue that will help the development team implement these cost-saving measures effectively using the information from your vector store.

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
                    - Provide a singular GitHub issue, each with a clear detailed description, to enable the development team to start working on the cost-saving initiatives effectively.
                    """  # noqa: E501
                        logger.info(
                            "Querying the vector store index to create GitHub issue descriptions..."
                        )
                        query_engine = index.as_query_engine(llm=appconfig.llm)
                        response = query_engine.query(github_query)
                        body = str(response)
                        body += f"\n\nThe detailed formatted result can be found here: {gist_url}"
                else:
                    body = result.formatted

                    # Include the Gist URL in the issue body

                issue_labels = (
                    self.model.labels.split(",") if self.model.labels else None
                )
                url = f"https://api.github.com/repos/{self.model.repo_owner}/{self.model.repo_name}/issues"
                headers = {
                    "Authorization": f"token {self.model.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                # Get today's date for the title
                data = {
                    "title": f"OpsBox Optimization Check - {pd.Timestamp.now().strftime('%Y-%m-%d')} - {getattr(result, 'result_name', 'Unnamed')}",
                    "body": body,
                    "labels": issue_labels or [],
                }
                response = requests.post(url, headers=headers, json=data, timeout=15)
                if response.status_code == 201:
                    logger.success(
                        f"Successfully created issue: {response.json()['html_url']}"
                    )
                else:
                    logger.error(f"Failed to create issue: {response.status_code}")
                    logger.error(response.json())

        except Exception as e:
            logger.error(f"Failed to send results via GitHub Tickets: {e}")
            return

        logger.success("Results sent via GitHub Tickets!")

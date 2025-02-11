from pluggy import HookimplMarker
from pydantic import BaseModel, Field
from loguru import logger
import base64
import os
import requests
import json
import copy

from llama_index.core import VectorStoreIndex, Document
from llama_index.core.program import LLMTextCompletionProgram

from typing import TYPE_CHECKING, Annotated
from opsbox import AppConfig

if TYPE_CHECKING:
    from opsbox import Result

hookimpl = HookimplMarker("opsbox")

req_timeout = 20


class TaskTicket(BaseModel):
    """Model for a Jira Task ticket.

    Args:
        summary (str): The summary of the issue.
        description (str): The description of the issue.
    """

    summary: str = Field(..., description="The summary of the task")
    description: str = Field(..., description="The description of the task")


class EpicTicket(BaseModel):
    """Model for a Jira Epic ticket.

    Args:
        summary (str): The summary of the epic.
        description (str): The description of the epic.
        epic_name (str): The name of the Epic.
        tasks (list[TaskTicket]): The tasks to be included in the Epic.
    """

    summary: str = Field(..., description="The summary of the epic")
    description: str = Field(..., description="The description of the epic")
    epic_name: str = Field(..., description="The name of the Epic")
    tasks: list[TaskTicket] = Field(
        [], description="The tasks to be included in the Epic"
    )


class SolutionsPlan(BaseModel):
    """Model for a jira solutions plan.

    Args:
        epics (list[EpicTicket]): The epics to be included in the solutions plan.
    """

    epics: list[EpicTicket]


class JiraOutput:
    """Output plugin for Jira.


    Attributes:
        model (BaseModel): The configuration model for the plugin.
        auth_headers (dict): The headers to authenticate with Jira.
        epic_link_field_id (str): The id of the Epic Link field in Jira.
        client (OpenAI): The OpenAI client.
        oai_helper (OpenAIHelper): The OpenAI helper.
    """

    def __init__(self):
        pass

    @hookimpl
    def grab_config(self):
        """Get the configuration model for the plugin.

        Returns:
            BaseModel: The configuration model for the plugin."""

        class JiraConfig(BaseModel):
            """Configuration for the Jira output."""

            JIRA_USERNAME: Annotated[
                str, Field(description="The URL of the Jira instance.", required=True)
            ]
            JIRA_EMAIL: Annotated[
                str,
                Field(
                    description="The email to authenticate to Jira with.", required=True
                ),
            ]
            JIRA_API_TOKEN: Annotated[
                str,
                Field(
                    description="The api key to authenticate to Jira with.",
                    required=True,
                ),
            ]
            JIRA_PROJECT_KEY: Annotated[
                str,
                Field(
                    description="The Jira project to create issues in.", required=True
                ),
            ]
            # jira_ticket_assistant: Annotated[
            #     str, Field(description="The open assistant to use to generate Jira tickets.", required=True)
            # ]
            # jira_ticket_vector_store_id: Annotated[
            #     str, Field(description="The vector store ID to use for the Jira ticket assistant.", required=True)
            # ]
            pass

        return JiraConfig

    @hookimpl
    @logger.catch(reraise=True)
    def activate(self):
        """Activate the plugin."""
        # jira identity token
        credentials = f"{self.model.JIRA_EMAIL}:{self.model.JIRA_API_TOKEN}".encode(
            "utf-8"
        )
        base64_credentials = base64.b64encode(credentials).decode("utf-8")

        self.auth_headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/json",
        }

        # get the epic link field id
        response = requests.get(
            f"{self.model.jira_url}/field/search?type=custom&query=Epic%20Link",
            headers=self.auth_headers,
            timeout=10,
        )
        self.epic_link_field_id = response.json()["values"][0]["id"]

    @hookimpl
    def set_data(self, model: BaseModel):
        """Set the credentials for the plugin."""
        self.model = model

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Writes the check results to Jira.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """

        logger.info("Writing results to Jira")
        for result in results:
            solution = self._generate_solution(result)
            self._upload_plan(solution, result)

        logger.success("Results written to Jira!")

    @logger.catch(reraise=True)
    def _generate_solution(self, data: "Result") -> SolutionsPlan:
        """
        Generates a list of Epics and Tasks to be created in Jira.

        Args:
            data (list[FormattedResult]): The formatted results from the checks.

        Returns:
            SolutionsPlan: The list of Epics and Tasks to be created in Jira.
        """

        # Create a vector store index from the input
        logger.info(
            f"Generating a solutions plan for Jira for check {data.result_name}"
        )
        logger.debug("Creating a vector store index from the input data...")

        if AppConfig().embed_model is None:
            templ: str = """
**Objective:**
You are a meticulous scrum planning assistant tasked with generating comprehensive semantic language epics based on the information provided to you in the documents below.
Your goal is to create well-structured and informative epics that will guide the development team in implementing these cost-saving measures effectively using the documents from your vector store.

**Epic Creation Process:**

1. **Major Category Epics:**
   - For each major category of cost-saving recommendations, such as "EC2 cost-savings" or "S3 cost-savings," create a highly detailed Epic.
   - The Epic should include:
     - A thorough description of the overarching goal.
     - Specific areas of focus within the category.
     - Expected outcomes of implementing these recommendations.
   - Ensure that the language used in the Epic matches the exact wording and phrasing from the provided recommendations.

2. **Child Tasks Under Each Epic:**
   - Under each Epic, generate multiple child tasks that break down the cost-saving recommendations into smaller, actionable items.
   - Each child task should include:
     - A clear and concise title that summarizes the task, using the exact wording from the recommendations.
     - A detailed explanation of the task, preserving the original language and phrasing from the recommendations.
     - Specific implementation details, such as the AWS services, resources, or configurations involved, as mentioned in the recommendations.
     - Any relevant data points, such as resource utilization metrics or cost analysis, directly quoted from the recommendations.
     - Expected outcomes and success criteria for the task, using the exact wording provided in the recommendations.
     - Potential risks or dependencies associated with the task, as stated in the recommendations.

**Guidelines:**
- Maintain the exact language, wording, and phrasing used in the cost-saving recommendations for both the Epic and child task descriptions.
- Include a chain-of-thought meticulously detailing the reasoning behind each cost-saving recommendation.
- Ensure that the Epics and tasks are structured logically and follow a clear hierarchy.
- Use bullet points, lists, and paragraphs to organize the information effectively. Include any relevant data points or metrics provided in the recommendations.
- Do not paraphrase or create your own language; instead, use the provided information verbatim to ensure accuracy and consistency.

**Output:**
- Provide a structured set of semantic language epics, with each Epic followed by its corresponding child tasks.
- Ensure clarity and precision in each Epic and task to enable the development team to start working on the cost-saving initiatives effectively.

Given the findings below, create a solutions plan for Jira:
-----------------------------------------------------------
{document}
"""  # noqa: E501
            program = LLMTextCompletionProgram.from_defaults(
                output_cls=SolutionsPlan,
                prompt_template_str=templ,
                verbose=True,
                llm=AppConfig().llm,
            )
            llm_response = program(document=str(text=data.formatted))
        else:
            docs: Document = []
            docs.append(Document(text=data.formatted, id=data.result_name))

            index = VectorStoreIndex.from_documents(
                docs, embed_model=AppConfig().embed_model
            )

            # query the index for epics and tasks
            aggregate_query: str = """
    **Objective:**
    You are a meticulous scrum planning assistant tasked with generating comprehensive semantic language epics based on the information provided to you in your vector store. 
    Your goal is to create well-structured and informative epics that will guide the development team in implementing these cost-saving measures effectively using the documents from your vector store.

    **Epic Creation Process:**

    1. **Major Category Epics:**
    - For each major category of cost-saving recommendations, such as "EC2 cost-savings" or "S3 cost-savings," create a highly detailed Epic.
    - The Epic should include:
        - A thorough description of the overarching goal.
        - Specific areas of focus within the category.
        - Expected outcomes of implementing these recommendations.
    - Ensure that the language used in the Epic matches the exact wording and phrasing from the provided recommendations.

    2. **Child Tasks Under Each Epic:**
    - Under each Epic, generate multiple child tasks that break down the cost-saving recommendations into smaller, actionable items.
    - Each child task should include:
        - A clear and concise title that summarizes the task, using the exact wording from the recommendations.
        - A detailed explanation of the task, preserving the original language and phrasing from the recommendations.
        - Specific implementation details, such as the AWS services, resources, or configurations involved, as mentioned in the recommendations.
        - Any relevant data points, such as resource utilization metrics or cost analysis, directly quoted from the recommendations.
        - Expected outcomes and success criteria for the task, using the exact wording provided in the recommendations.
        - Potential risks or dependencies associated with the task, as stated in the recommendations.

    **Guidelines:**
    - Maintain the exact language, wording, and phrasing used in the cost-saving recommendations for both the Epic and child task descriptions.
    - Include a chain-of-thought meticulously detailing the reasoning behind each cost-saving recommendation.
    - Ensure that the Epics and tasks are structured logically and follow a clear hierarchy.
    - Use bullet points, lists, and paragraphs to organize the information effectively. Include any relevant data points or metrics provided in the recommendations.
    - Do not paraphrase or create your own language; instead, use the provided information verbatim to ensure accuracy and consistency.

    **Output:**
    - Provide a structured set of semantic language epics, with each Epic followed by its corresponding child tasks.
    - Ensure clarity and precision in each Epic and task to enable the development team to start working on the cost-saving initiatives effectively.
    """  # noqa: E501
            logger.info("Querying the vector store index to create Jira solutions...")
            query_engine = index.as_query_engine(llm=AppConfig().llm)
            response = query_engine.query(aggregate_query)

            # format the response into a SolutionsPlan
            logger.debug("Structuring the response...")
            temp_str = "Format your response below into a solutions plan:\n{document}"
            program = LLMTextCompletionProgram.from_defaults(
                output_cls=SolutionsPlan,
                prompt_template_str=temp_str,
                llm=AppConfig().llm,
                verbose=True,
            )
            llm_response = program(document=str(response))
            return llm_response

    @logger.catch(reraise=True)
    def _upload_plan(self, plan: SolutionsPlan, data: "Result"):
        """Upload a solutions plan to Jira.

        Args:
            plan (SolutionsPlan): The solutions plan to upload.
            data (Result): The original data.

        Returns:
            None
        """
        logger.info("Uploading Solutions Plan to Jira")
        for epic in plan.epics:
            epic_key = self._create_epic(epic.summary, epic.description, epic.epic_name)
            for task in epic.tasks:
                self._create_task(task.summary, task.description, epic_key, data)

    @logger.catch(reraise=True)
    def _create_epic(self, summary: str, description: str, epic_name: str) -> str:
        """
        Creates an Epic in Jira.

        Args:
            summary (str): The summary of the Epic.
            description (str): The description of the Epic.
            epic_name (str): The name of the Epic.

        Returns:
            str: The id of the created Epic if successful.

        Raises:
            requests.HTTPError: If the request to create the Epic fails.
        """
        logger.debug(f"Uploading Epic: {epic_name}")
        # Create the payload for the request
        headers = self.auth_headers
        url = self.model.jira_url
        project_key = self.model.JIRA_PROJECT_KEY
        import re

        re.sub(r"\W+", "", description)

        payload = json.dumps(
            {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": "Epic"},
                }
            }
        )

        # Make the request to create the Epic
        response = requests.post(
            f"{url}/issue", headers=headers, data=payload, timeout=req_timeout
        )

        # Check if the request was successful
        if response.status_code != 201:
            raise requests.HTTPError(f"Error creating Epic: {response.json()}")
        elif response.status_code == 201:
            epic_id = response.json().get("id")
            logger.success(f"Epic created: {epic_id}")
            return epic_id

    @logger.catch(reraise=True)
    def _create_task(
        self, summary: str, description: str, epic_link: str, details: "Result"
    ):
        """
        Create a Jira task with the given parameters.

        Args:
            summary (str): The summary of the task.
            description (str): The description of the task.
            epic_link (str): The epic link for the task.
            details (FormattedResult): The details to be attached to the task.

        Returns:
            None
        """
        logger.debug(f"Uploading Task: {summary}")
        headers = self.auth_headers
        url = self.model.jira_url
        project_key = self.model.JIRA_PROJECT_KEY
        payload = json.dumps(
            {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": "Task"},
                    "parent": {
                        "id": epic_link,
                    },  # Assuming this is the Epic Link field
                }
            }
        )

        response = requests.post(
            f"{url}/issue", headers=headers, data=payload, timeout=req_timeout
        )
        if response.status_code == 201:
            issue_key = response.json()["key"]
            logger.success(f"Task created: {response.json().get('key')}")
            self._append_details_to_task(issue_key, details)
        if response.status_code != 201:
            logger.trace(f"Error payload: {payload}")
            if response.text:
                raise requests.HTTPError(f"Error creating Task: {response.text}")
            else:
                raise requests.HTTPError(f"Error creating Task: {response.status_code}")

    @logger.catch(reraise=True)
    def _append_details_to_task(self, issue_key: str, details: "Result"):
        """
        Attach details to an existing Jira issue.

        Args:
            issue_key (str): The key of the Jira issue to attach details to.
            details (FormattedResult): The details to be attached.

        Returns:
            None

        Raises:
            requests.HTTPError: If the request to attach the details fails.
        """
        headers = copy.deepcopy(self.auth_headers)
        headers.update({"X-Atlassian-Token": "no-check", "Accept": "application/json"})
        del headers["Content-Type"]

        logger.debug(f"Attaching details to task: {issue_key}")

        # make temp. dir if doesn't exist
        if not os.path.exists("temp"):
            os.makedirs("temp")

        # write to temp. details file
        with open(f"temp/{details.result_name}.txt", "w") as f:
            f.write(json.dumps(details.details))

        # attach to issue
        reader = open(f"temp/{details.result_name}.txt", "rb")  # noqa: SIM115
        files = {"file": (f"{details.result_name}", reader)}

        response = requests.post(
            f"{self.model.jira_url}/issue/{issue_key}/attachments",
            headers=headers,
            files=files,
            timeout=req_timeout,
        )
        reader.close()
        if response.status_code != 200:
            if response.text:
                raise requests.HTTPError(
                    f"Error attaching details to issue: {response.text}"
                )
            else:
                raise requests.HTTPError(
                    f"Error attaching details to issue: {response.status_code}"
                )

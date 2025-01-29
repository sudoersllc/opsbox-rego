from pluggy import HookimplMarker
from pydantic import BaseModel, Field
import boto3
from loguru import logger
from typing import Annotated
from opsbox import Result
import json

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class IAMProvider:
    """Plugin for gathering data related to AWS IAM users, roles, and policies."""

    @hookimpl
    def grab_config(self):
        """Return the plugin's configuration."""

        class IAMConfig(BaseModel):
            """Configuration for the AWS IAM plugin."""

            aws_access_key_id: Annotated[str, Field(description="AWS access key ID", required=False,default=None)]
            aws_secret_access_key: Annotated[str, Field(description="AWS secret access key", required=False,default=None)]
            aws_region: Annotated[str | None, Field(description="AWS region", required=False, default=None)]

        return IAMConfig

    @hookimpl
    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating IAM plugin...")

    @hookimpl
    def set_data(self, model: type[BaseModel]) -> None:
        """Set the data for the plugin based on the model."""
        logger.trace("Setting data for IAM plugin...")
        self.credentials = model.model_dump()

    @hookimpl
    def gather_data(self):
        """Gathers and structures data related to AWS IAM users, roles, and policies."""

        logger.info("Gathering data for IAM...")
        credentials = self.credentials

        # Use the specified region or default to "us-west-1"
        region = credentials["aws_region"] or "us-west-1"
        
        if credentials["aws_access_key_id"] is None:
            # Use the instance profile credentials
            iam_client = boto3.client("iam", region_name=region)
        else:
            try:
                iam_client = boto3.client(
                    "iam",
                    aws_access_key_id=credentials["aws_access_key_id"],
                    aws_secret_access_key=credentials["aws_secret_access_key"],
                    region_name=region,
                )
            except Exception as e:
                logger.error(f"Error creating IAM client: {e}")
                return Result(
                    relates_to="aws_data",
                    result_name="aws_iam_data",
                    result_description="Structured IAM data using.",
                    formatted="Error creating IAM client.",
                    details={},
                )
                

        # Prepare structured data containers
        iam_users = []
        iam_roles = []
        iam_policies = []
        credential_report_data = []

        try:
            # Pagination for account authorization details
            paginator = iam_client.get_paginator("get_account_authorization_details")
            for page in paginator.paginate():
                # Collect IAM users
                for user in page.get("UserDetailList", []):
                    iam_users.append({
                        "user_name": user["UserName"],
                        "user_id": user.get("UserId"),
                        "arn": user.get("Arn"),
                        "create_date": user.get("CreateDate", "").isoformat() if user.get("CreateDate") else None,
                        "attached_policies": user.get("AttachedManagedPolicies", []),
                    })

                # Collect IAM roles
                for role in page.get("RoleDetailList", []):
                    iam_roles.append({
                        "role_name": role["RoleName"],
                        "role_id": role.get("RoleId"),
                        "arn": role.get("Arn"),
                        "create_date": role.get("CreateDate", "").isoformat() if role.get("CreateDate") else None,
                        "attached_policies": role.get("AttachedManagedPolicies", []),
                    })

                # Collect IAM policies
                for policy in page.get("Policies", []):
                    iam_policies.append({
                        "policy_name": policy["PolicyName"],
                        "policy_id": policy.get("PolicyId"),
                        "arn": policy.get("Arn"),
                        "attachment_count": policy.get("AttachmentCount"),
                        "create_date": policy.get("CreateDate", "").isoformat() if policy.get("CreateDate") else None,
                    })

            # Get credential report
            logger.info("Fetching credential report...")
            report_response = iam_client.get_credential_report()
            credential_report_csv = report_response["Content"].decode("utf-8")
            credential_report = [
                {key: value for key, value in zip(credential_report_csv.splitlines()[0].split(","), line.split(","))}
                for line in credential_report_csv.splitlines()[1:]
            ]

            # Collect credential report data
            credential_report_data = credential_report

        except Exception as e:
            logger.error(f"Error gathering IAM data: {e}")

        # Structure the final output
        rego_ready_data = {
            "input": {
            "iam_users": iam_users,
            "iam_roles": iam_roles,
            "iam_policies": iam_policies,
            "credential_report": credential_report_data,
            }
        }

        #export iam data to json file
        with open("iam_data.json", "w") as f:
            json.dump(rego_ready_data, f)
        logger.success("IAM data successfully gathered and structured.")
        logger.debug(rego_ready_data)

        item = Result(
            relates_to="aws_data",
            result_name="aws_iam_data",
            result_description="Structured IAM data using.",
            formatted="",
            details=rego_ready_data,
        )

        return item

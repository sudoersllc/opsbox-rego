import boto3
import json
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING
import yaml

if TYPE_CHECKING:
    from core.rego import FormattedResult


from loguru import logger

class LowerCost:
    """A plugin to generate recommendations for lowering costs on AWS EC2 instances."""
    def __init__(self):
        pass

    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function.
        Attributes:
            oai_assistant_id: str: The ID of the OpenAI assistant
            oai_vector_store_id: str: The ID of the OpenAI vector store
            oai_key: str: The OpenAI API key
        Returns:
            OAICostConfig: Configuration for the OpenAI Cost
        """
        class LowerCostConfig(BaseModel):
            """Configuration for the AWS EC2 plugin."""
            aws_access_key_id: str = Field(..., description="AWS access key ID")
            aws_secret_access_key: str = Field(..., description="AWS secret access key")
            aws_region: str = Field(..., description="AWS region")
        return LowerCostConfig

    def activate(self) -> None:
        """Initialize the plugin."""
        logger.trace("Activating EC2 plugin...")

    def set_data(self, model: BaseModel) -> None:
        """Set the plugin's configuration data."""
        self.config = model

    def proccess_input(self, data: list["FormattedResult"]) -> list["FormattedResult"]:
        """Process the input data and generate recommendations."""
        data = self.generate_recommendations(data)
        return data

    def generate_recommendations(self, data: list["FormattedResult"]) ->list["FormattedResult"]:
        """
        Generate recommendations for lowering costs on AWS EC2 instances.
        Args:
            data (list[FormattedResult]): The data to process.
        Returns:
            list[FormattedResult]: The formatted recommendations.
        """
        logger.success("Generating recommendations...")

        region_to_location = {
            "us-east-1": "US East (N. Virginia)",
            "us-east-2": "US East (Ohio)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "af-south-1": "Africa (Cape Town)",
            "ap-east-1": "Asia Pacific (Hong Kong)",
            "ap-south-2": "Asia Pacific (Hyderabad)",
            "ap-southeast-3": "Asia Pacific (Jakarta)",
            "ap-southeast-5": "Asia Pacific (Malaysia)",
            "ap-southeast-4": "Asia Pacific (Melbourne)",
            "ap-south-1": "Asia Pacific (Mumbai)",
            "ap-northeast-3": "Asia Pacific (Osaka)",
            "ap-northeast-2": "Asia Pacific (Seoul)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)",
            "ca-central-1": "Canada (Central)",
            "ca-west-1": "Canada West (Calgary)",
            "cn-north-1": "China (Beijing)",
            "cn-northwest-1": "China (Ningxia)",
            "eu-central-1": "Europe (Frankfurt)",
            "eu-west-1": "Europe (Ireland)",
            "eu-west-2": "Europe (London)",
            "eu-south-1": "Europe (Milan)",
            "eu-west-3": "Europe (Paris)",
            "eu-south-2": "Europe (Spain)",
            "eu-north-1": "Europe (Stockholm)",
            "eu-central-2": "Europe (Zurich)",
            "il-central-1": "Israel (Tel Aviv)",
            "me-south-1": "Middle East (Bahrain)",
            "me-central-1": "Middle East (UAE)",
            "sa-east-1": "South America (São Paulo)",
        }

        aws_instance_downgrade_map = {
            "t2.micro": "t2.nano",
            "t2.small": "t2.micro",
            "t2.medium": "t2.small",
            "t2.large": "t2.medium",
            "t3.micro": "t3.nano",
            "t3.small": "t3.micro",
            "t3.medium": "t3.small",
            "t3.large": "t3.medium",
            "t3a.micro": "t3a.nano",
            "t3a.small": "t3a.micro",
            "t3a.medium": "t3a.small",
            "t3a.large": "t3a.medium",
            "t4g.micro": "t4g.nano",
            "t4g.small": "t4g.micro",
            "t4g.medium": "t4g.small",
            "m5.large": "m5.medium",
            "m5.xlarge": "m5.large",
            "m5.2xlarge": "m5.xlarge",
            "m5.4xlarge": "m5.2xlarge",
            "m5.8xlarge": "m5.4xlarge",
            "m5.16xlarge": "m5.8xlarge",
            "m5.24xlarge": "m5.16xlarge",
            "m5a.large": "m5a.medium",
            "m5a.xlarge": "m5a.large",
            "m5a.2xlarge": "m5a.xlarge",
            "m5a.4xlarge": "m5a.2xlarge",
            "m5a.8xlarge": "m5a.4xlarge",
            "m5a.16xlarge": "m5a.8xlarge",
            "m5a.24xlarge": "m5a.16xlarge",
            "m5n.large": "m5n.medium",
            "m5n.xlarge": "m5n.large",
            "m5n.2xlarge": "m5n.xlarge",
            "m5n.4xlarge": "m5n.2xlarge",
            "m5n.8xlarge": "m5n.4xlarge",
            "m5n.16xlarge": "m5n.8xlarge",
            "m5n.24xlarge": "m5n.16xlarge",
            "m5zn.large": "m5zn.medium",
            "m5zn.xlarge": "m5zn.large",
            "m5zn.2xlarge": "m5zn.xlarge",
            "m5zn.3xlarge": "m5zn.2xlarge",
            "m5zn.6xlarge": "m5zn.3xlarge",
            "m5zn.12xlarge": "m5zn.6xlarge",
            "c5.large": "c5.medium",
            "c5.xlarge": "c5.large",
            "c5.2xlarge": "c5.xlarge",
            "c5.4xlarge": "c5.2xlarge",
            "c5.9xlarge": "c5.4xlarge",
            "c5.18xlarge": "c5.9xlarge",
            "c5n.large": "c5n.medium",
            "c5n.xlarge": "c5n.large",
            "c5n.2xlarge": "c5n.xlarge",
            "c5n.4xlarge": "c5n.2xlarge",
            "c5n.9xlarge": "c5n.4xlarge",
            "c5n.18xlarge": "c5n.9xlarge",
            "r5.large": "r5.medium",
            "r5.xlarge": "r5.large",
            "r5.2xlarge": "r5.xlarge",
            "r5.4xlarge": "r5.2xlarge",
            "r5.8xlarge": "r5.4xlarge",
            "r5.16xlarge": "r5.8xlarge",
            "r5.24xlarge": "r5.16xlarge",
            "r5a.large": "r5a.medium",
            "r5a.xlarge": "r5a.large",
            "r5a.2xlarge": "r5a.xlarge",
            "r5a.4xlarge": "r5a.2xlarge",
            "r5a.8xlarge": "r5a.4xlarge",
            "r5a.16xlarge": "r5a.8xlarge",
            "r5a.24xlarge": "r5a.16xlarge",
            "r5n.large": "r5n.medium",
            "r5n.xlarge": "r5n.large",
            "r5n.2xlarge": "r5n.xlarge",
            "r5n.4xlarge": "r5n.2xlarge",
            "r5n.8xlarge": "r5n.4xlarge",
            "r5n.16xlarge": "r5n.8xlarge",
            "r5n.24xlarge": "r5n.16xlarge",
            "g4dn.xlarge": "g4dn.large",
            "g4dn.2xlarge": "g4dn.xlarge",
            "g4dn.4xlarge": "g4dn.2xlarge",
            "g4dn.8xlarge": "g4dn.4xlarge",
            "g4dn.12xlarge": "g4dn.8xlarge",
            "g4dn.16xlarge": "g4dn.12xlarge",
            "p3.2xlarge": "p3.large",
            "p3.8xlarge": "p3.2xlarge",
            "p3.16xlarge": "p3.8xlarge",
            "p4d.24xlarge": "p4d.12xlarge",
            "inf1.xlarge": "inf1.medium",
            "inf1.2xlarge": "inf1.xlarge",
            "inf1.6xlarge": "inf1.2xlarge",
            "inf1.24xlarge": "inf1.6xlarge"
        }


        pricing_client = boto3.client(
            "pricing",
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
            region_name=self.config.aws_region
        )

        instance_data = []
        for module in data:
            if module["module_name"] == "ec2":
                for instance in module["details"]:
                    logger.info(f"Processing instance: {instance}")
                    region = instance["region"]
                    instance_type = instance["instance_type"]
                    operating_system = instance["operating_system"]
                    if operating_system == "Linux/UNIX":
                        operating_system = "Linux"
                    tenancy = instance["tenancy"]
                    if tenancy == "default":
                        tenancy = "Shared"

                    location_name = region_to_location.get(region)
                    if not location_name:
                        logger.error(f"Unknown region: {region}")
                        continue

                    try:
                        response = pricing_client.get_products(
                            ServiceCode="AmazonEC2",
                            Filters=[
                                {"Type": "TERM_MATCH", "Field": 
                                 "instanceType", "Value": instance_type},
                                {"Type": "TERM_MATCH", "Field": 
                                 "location", "Value": location_name},
                                {"Type": "TERM_MATCH", "Field": 
                                 "operatingSystem", "Value": operating_system},
                                {"Type": "TERM_MATCH", "Field": 
                                 "tenancy", "Value": tenancy},

                            ],
                            MaxResults=1
                        )

                        #get lower cost instance type
                        lower_response = pricing_client.get_products(
                            ServiceCode="AmazonEC2",
                            Filters=[
                                {"Type": "TERM_MATCH", "Field": 
                                 "instanceType", "Value": aws_instance_downgrade_map[instance_type]},
                                {"Type": "TERM_MATCH", "Field": 
                                 "location", "Value": location_name},
                                {"Type": "TERM_MATCH", "Field": 
                                 "operatingSystem", "Value": operating_system},
                                {"Type": "TERM_MATCH", "Field": 
                                 "tenancy", "Value": tenancy},

                            ],
                            MaxResults=1
                        )


                        if not response["PriceList"]:
                            logger.error(
                                f"No pricing data found for {instance_type} in {location_name} with OS: {operating_system}"
                            )
                            continue

                        price_list = response["PriceList"][0]  # Just pick the first result to avoid multiple appends
                        parsed_item = json.loads(price_list)
                        terms = parsed_item.get("terms", {})

                        # Focus only on the 'OnDemand' pricing terms, adjust if needed
                        on_demand_terms = terms.get("OnDemand", {})
                        if on_demand_terms:
                            for term_data in on_demand_terms.values():
                                price_dimensions = term_data.get("priceDimensions", {})
                                for dimension_data in price_dimensions.values():
                                    description = dimension_data.get("description")
                                    price_per_unit = dimension_data["pricePerUnit"].get("USD")
                                    unit = dimension_data.get("unit")

                                    #get lower cost data
                                    lower_price_list = lower_response["PriceList"][0]
                                    lower_parsed_item = json.loads(lower_price_list)
                                    lower_terms = lower_parsed_item.get("terms", {})
                                    lower_on_demand_terms = lower_terms.get("OnDemand", {})
                                    for lower_term_data in lower_on_demand_terms.values():
                                        lower_price_dimensions = lower_term_data.get("priceDimensions", {})
                                        for lower_dimension_data in lower_price_dimensions.values():
                                            lower_description = lower_dimension_data.get("description")
                                            lower_price_per_unit = lower_dimension_data["pricePerUnit"].get("USD")
                                            lower_unit = lower_dimension_data.get("unit")

                                    orginal_instance = {
                                        "instance": yaml.dump(instance, default_flow_style=False),
                                        "description": description,
                                        "price_per_unit": price_per_unit,
                                        "unit": unit
                                    }

                                    lower_instance = {
                                        "description": lower_description,
                                        "price_per_unit": lower_price_per_unit,
                                        "unit": lower_unit
                                    }

                                    # create a reable message for the user

                                    message = (
                                        f"Instance {instance_type} in {location_name} with OS: {operating_system} "
                                        f"and tenancy: {tenancy} is priced at {price_per_unit} per {unit}. "
                                        f"You can save money by using {aws_instance_downgrade_map[instance_type]} "
                                        f"which is priced at {lower_price_per_unit} per {lower_unit}."
                                    )
                                    # check if price per unit and lower price per unit are 
                                    # "Hrs" and if so calculate the monthly savings
                                    if unit == "Hrs" and lower_unit == "Hrs":
                                        #both price per unit and lower price per unit  are strin
                                        price_diff = price_per_unit - lower_price_per_unit
                                        price_monthly = price_diff * 730

                                        message = (
                                            f"Instance {instance_type} in {location_name} with OS: {operating_system} and "
                                            f"tenancy: {tenancy} is priced at {price_per_unit} per {unit}. You can save money "
                                            f"by using {aws_instance_downgrade_map[instance_type]}, which is priced at {lower_price_per_unit} per {lower_unit}."
                                            f"You can save {price_diff} per hour and {price_monthly} per month."
                                        )

                                    data = {
                                        "orginal_instance": orginal_instance,
                                        "lower_instance": lower_instance,
                                        "message": message
                                    }
               
                                    instance_data.append(data)


                                    # Break after appending the first valid price
                                    break

                    except Exception as e:
                        logger.error(f"Failed to retrieve pricing data: {e}")
            try:
                formatted_data =  [{
                    "module_name": "ec2",
                    "check_name": "lower_cost",
                    "formatted": yaml.dump(instance_data, default_flow_style=False)
                    }]
                return formatted_data

            except Exception as e:
                logger.error(f"Error formatting instance details: {e}")
                    
                    

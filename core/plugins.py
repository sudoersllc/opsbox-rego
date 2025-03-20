from pydantic import BaseModel


class Result(BaseModel):
    """A dictionary representing the results of a rego check.

    Attributes:
        relates_to (str): The thing that the result relates to.
        result_name (str): The name of the result.
        result_description (str): The description of the result.
        details (dict | list[dict]): The details of the result.
        formatted (str): The formatted string of the result.
    """

    relates_to: str
    result_name: str
    result_description: str
    details: dict | list[dict]
    formatted: str

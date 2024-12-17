import json


def tag_string_to_dict(tag_string):
    """Converts a string of key-value pairs to a dictionary."""
    if isinstance(tag_string, str):
        try:
            # Attempt to parse the string as JSON
            tag_string = json.loads(tag_string)
            return tag_string
        except json.JSONDecodeError:
            # Handle the error or raise an exception
            raise ValueError("Tags provided are not in a valid JSON format.")

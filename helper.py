from dotenv import load_dotenv, find_dotenv
import os


def get_api_key(key_name: str) -> str:
    """
    Fetches the API key from the .env file.

    Args:
        key_name (str): The name of the environment variable to fetch.

    Returns:
        str: The value of the environment variable.
    """

    # Find the .env file path (returns an empty string if not found)
    dotenv_path = find_dotenv()

    # Load the .env file
    if dotenv_path:
        loaded = load_dotenv(dotenv_path)
        if not loaded:
            raise EnvironmentError(
                "Failed to load the .env file. Check file permissions and format."
            )

    # Fetch the API_KEY environment variable
    api_key = os.environ.get(key_name)
    if not api_key:
        raise ValueError(
            "API_KEY is missing or empty. Make sure it's set in your .env file."
        )

    return api_key

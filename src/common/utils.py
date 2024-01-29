import html
import re
import unicodedata

import yaml

# function to remove non-ascii characters from a string
clean_non_ascii = (
    lambda string: unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("utf-8").strip(" ")
)


def clean_string(string: str) -> str:
    """Process a string to remove html text, extra spaces ad non-ascii characters

    Args:
        string (str): input string

    Returns:
        str: output string after pre-processing
    """

    def replace_numeric(match):
        char = match.group(0)
        try:
            numeric_value = unicodedata.numeric(char)
            if numeric_value % 1 == 0:
                numeric_value = int(numeric_value)
            return str(numeric_value)
        except (TypeError, ValueError):
            return char

    # Unescape HTML and get numeric values corresponding to any unicode characters
    string = html.unescape(string)
    string = re.sub(r"[\s\n\t]+", " ", string)  # Remove unnessary spaces
    string = re.sub(r"\S+", replace_numeric, string)  # Replace numeric values with numbers/floats
    string = re.sub(r"[^\x00-\x7F]+|<.*?>", "", string)  # Remove non-ASCII and html characters

    return string.strip()


def load_yaml(file_path: str) -> dict:
    """Function to load a yaml file

    Args:
        file_path (str): path of the yaml file

    Returns:
        dict: parameter dictionary
    """
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data

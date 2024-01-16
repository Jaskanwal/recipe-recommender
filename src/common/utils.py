import unicodedata
import re
import html

# function to remove non-ascii characters from a string
clean_non_ascii = (
    lambda string: unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("utf-8").strip(" ")
)


def clean_string(string: str) -> str:
    """Apply pre-processing on a string and remove non-ascii characters, spaces, etc.

    Args:
        string (str): input string

    Returns:
        str: output cleaned string
    """
    # Remove any non-ascii characters
    string = clean_non_ascii(string)

    # Remove any triling and leading white spaces, tabs or newline characters
    string = re.sub(r"^\s+|\s+$|\n|\t", "", string)

    # Use regex to replace 2 or more consecutive spaces with a single space
    string = re.sub(r"\s{2,}", " ", string)

    # Parse HTML entity to decimal value
    string = bytes(string, "utf-8").decode("unicode-escape")
    string = html.unescape(string)
    # string = string.replace("&#189;", "0.5")

    return string

import unicodedata
import re
import html

# function to remove non-ascii characters from a string
clean_non_ascii = (
    lambda string: unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("utf-8").strip(" ")
)


def get_numeric_value(char: str) -> str:
    """Assign numeric value to a string

    Args:
        char (str): input string

    Returns:
        str: output string
    """
    try:
        numeric_value = unicodedata.numeric(char)
        if numeric_value % 1 == 0:
            numeric_value = int(numeric_value)
        return str(numeric_value)
    except (TypeError, ValueError):
        return char


# def clean_string(string: str) -> str:
#     """Apply pre-processing on a string and remove non-ascii characters, spaces, etc.

#     Args:
#         string (str): input string

#     Returns:
#         str: output cleaned string
#     """
#     # Unescape HTML
#     string = html.unescape(string)

#     # Get numeric values corresponding to any unicode characters
#     string = "".join([get_numeric_value(item) for item in string])

#     # Remove any non-ascii characters
#     string = clean_non_ascii(string)

#     # Remove any triling and leading white spaces, tabs or newline characters
#     string = re.sub(r"^\s+|\s+$|\n|\t", "", string)

#     # Use regex to replace 2 or more consecutive spaces with a single space
#     string = re.sub(r"\s{2,}", " ", string)

#     return string


def clean_string(string: str) -> str:
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

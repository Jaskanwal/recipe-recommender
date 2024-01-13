import unicodedata

# function to remove non-ascii characters from a string
clean_non_ascii = (
    lambda string: unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("utf-8").strip(" ")
)

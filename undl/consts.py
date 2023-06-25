import os

BASE_URL = "https://digitallibrary.un.org/api/v1/search"
OLD_BASE_URL = "https://digitallibrary.un.org/search"

FORMATS = {
    "bibtex": "btex",
    "marc": "hm",
    "marcxml": "xm",
    "dublincore": "xd",
    "endnote": "xe",
    "nlm": "xn",
    "refworks": "xw",
    "ris": "ris",
}

DEFAULT_FORMAT = "marcxml"

API_KEY = os.getenv("UN_API")

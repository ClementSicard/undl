import argparse
from typing import Any, Dict

from undl.client import UNDLClient


def main(args: Dict[str, Any]):
    client = UNDLClient(verbose=args["verbose"])
    client.query(
        query=args["query"],
        output_format=args["format"],
        n_results=args["n_results"],
        output_file=args["output"],
    )


def parse_args() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Query the UN Digital Library API with a Python wrapper.",
    )
    parser.add_argument(
        "query",
        help="Query string to search for.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file name.",
        default="./downloads/output.json",
    )
    parser.add_argument(
        "-n",
        "--n_results",
        type=int,
        help="Number of results",
        default=50,
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        help="Output format",
        default="marcxml",
    )

    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()
    main(args=args)

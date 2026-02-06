"""Example script to query LocalForge with retrieval-augmented context."""
import argparse

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Query LocalForge")
    parser.add_argument("query", help="Question to ask the assistant")
    parser.add_argument("--host", default="http://localhost:8000", help="Backend URL")
    args = parser.parse_args()

    response = requests.post(f"{args.host}/query", json={"query": args.query})
    response.raise_for_status()
    payload = response.json()
    print("Response:\n", payload["response"])


if __name__ == "__main__":
    main()

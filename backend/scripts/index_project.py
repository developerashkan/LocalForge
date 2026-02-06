"""Example script to index a local folder on the backend host."""
import argparse

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Index a folder into LocalForge")
    parser.add_argument("path", help="Path to the project folder")
    parser.add_argument("--host", default="http://localhost:8000", help="Backend URL")
    args = parser.parse_args()

    response = requests.post(f"{args.host}/index", json={"path": args.path})
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()

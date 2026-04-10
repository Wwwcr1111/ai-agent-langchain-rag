# pipelines/__main__.py

import argparse
from langchain_ai_agent.pipelines.doc_to_action_pipeline import run_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the document pipeline with a given path.")
    parser.add_argument(
        "--path",
        required=True,
        help="Path to a file or folder (e.g. data/raw_docs)"
    )
    args = parser.parse_args()
    run_pipeline(args.path)

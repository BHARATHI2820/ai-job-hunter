"""
Helper: run a real search and save it as a fixture for evaluate_ranking.py.

Usage:
    python -m eval.capture_fixture "GenAI Engineer" "Chennai" eval/fixtures/genai_engineer_chennai.json
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from core.sources.adzuna_source import AdzunaSource
from core.sources.indianapi_source import IndianAPISource
from core.sources.multi_source import MultiSourceJobSource, build_configured_sources


def main():
    role, location, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    source = MultiSourceJobSource(
        sources=build_configured_sources([AdzunaSource, IndianAPISource])
    )
    jobs = source.search(role, location)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"role": role, "location": location, "jobs": jobs}, f, indent=2)
    print(f"Saved {len(jobs)} job(s) to {out_path}")


if __name__ == "__main__":
    main()
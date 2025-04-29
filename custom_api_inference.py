#!/usr/bin/env python3
import os
import sys
import asyncio
import json
from pathlib import Path

# Configure custom retriever
os.environ["RETRIEVER"] = "custom"
os.environ["RETRIEVER_ENDPOINT"] = "https://clueweb22.us/search"
os.environ["RETRIEVER_ARG_K"] = "3"

from gpt_researcher import GPTResearcher

# ────────────────────────────────────────────────────────────────
# 1) Paths & Config
# ────────────────────────────────────────────────────────────────
SYSTEM_NAME = "GPTResearcher_custom"
OUTPUT_DIR = Path(SYSTEM_NAME)
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIG_PATH = "gptr_config.json"
REPORT_TYPE = "research_report"

# ────────────────────────────────────────────────────────────────
# 2) Process a single record
# ────────────────────────────────────────────────────────────────
async def process_record(rec: dict, sem: asyncio.Semaphore):
    qid, qtext = rec["id"], rec["query"]

    # Save the raw query
    (OUTPUT_DIR / f"{qid}.q").write_text(qtext, encoding="utf-8")

    async with sem:
        try:
            researcher = GPTResearcher(
                query=qtext,
                report_type=REPORT_TYPE,
                config_path=CONFIG_PATH
            )
            await researcher.conduct_research()

            # Ensure we have sources
            sources = researcher.get_research_sources()
            if not sources:
                print(f"[ERROR] No sources returned for query '{qtext}'", file=sys.stderr)
                sys.exit(1)

            # Generate and save the report
            report_md = await researcher.write_report()
            (OUTPUT_DIR / f"{qid}.a").write_text(report_md, encoding="utf-8")

        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

# ────────────────────────────────────────────────────────────────
# 3) Main: read JSONL & dispatch
# ────────────────────────────────────────────────────────────────
async def main(input_path: str, concurrency: int = 8):
    with open(input_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    sem = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(process_record(r, sem) for r in records))

# ────────────────────────────────────────────────────────────────
# 4) CLI
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GPTResearcher batch runner")
    parser.add_argument(
        "-i", "--input", required=True,
        help="Path to JSONL file with one {id,query} per line"
    )
    parser.add_argument(
        "-c", "--concurrency", type=int, default=8,
        help="Parallel research tasks"
    )
    args = parser.parse_args()
    asyncio.run(main(args.input, args.concurrency))

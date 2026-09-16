import asyncio

from agent_host.host import run_query


async def main():
    print("[TEST] Starting run_query...", flush=True)

    result = await run_query(
        "Find GenAI Engineer jobs in Chennai"
    )

    print("[TEST] run_query completed.", flush=True)
    print("[TEST] Final answer:", result.get("final_answer"), flush=True)
    print(
        "[TEST] Jobs:",
        len(result.get("last_search_results") or []),
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
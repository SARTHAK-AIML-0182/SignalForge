"""Manual test for persistent topic deduplication."""

from pathlib import Path

from app.db.database import init_db
from app.repositories import SQLiteAgentRepository, SQLiteTopicRepository
from app.services.discovery import discover_topics, DEFAULT_FEEDS


def main():
    print("=== SignalForge Deduplication Test ===\n")

    test_db = Path("data/dedup_test.db")

    # Start with a clean test database
    if test_db.exists():
        test_db.unlink()

    init_db(test_db)

    agent_repo = SQLiteAgentRepository(test_db)
    topic_repo = SQLiteTopicRepository(test_db)

    agent_id = "dedup-test-agent"

    agent_repo.save_agent(
        agent_id,
        "NOVA",
        "AI & Emerging Technology"
    )

    print("FIRST DISCOVERY")
    print("----------------")

    first = discover_topics(
        agent_id,
        repo=topic_repo,
        feeds=DEFAULT_FEEDS,
        timeout=10.0
    )

    print(f"New topics discovered: {len(first)}")

    print("\nSECOND DISCOVERY")
    print("-----------------")

    second = discover_topics(
        agent_id,
        repo=topic_repo,
        feeds=DEFAULT_FEEDS,
        timeout=10.0
    )

    print(f"New topics discovered: {len(second)}")

    stored = topic_repo.list_topics_by_agent(agent_id)

    print("\nDATABASE")
    print("--------")
    print(f"Total stored topics: {len(stored)}")

    print("\nRESULT")
    print("------")

    if len(second) == 0:
        print("PASS: Duplicate topics were rejected.")
    else:
        print(
            f"WARNING: {len(second)} topics appeared again."
        )

    # Cleanup
    if test_db.exists():
        test_db.unlink()


if __name__ == "__main__":
    main()
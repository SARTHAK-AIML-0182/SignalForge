"""Script to run live topic discovery against real RSS feeds."""

import sys
from pathlib import Path
from app.db.database import init_db
from app.repositories import SQLiteAgentRepository, SQLiteTopicRepository
from app.services.discovery import discover_topics, DEFAULT_FEEDS

# Force UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("Executing live topic discovery test against public AI feeds...\n")
    test_db = Path("data/test_live_discovery.db")
    init_db(test_db)

    agent_repo = SQLiteAgentRepository(test_db)
    agent_repo.save_agent("live-demo-agent", "NOVA", "AI & Emerging Technology")

    topic_repo = SQLiteTopicRepository(test_db)

    discovered = discover_topics("live-demo-agent", repo=topic_repo, feeds=DEFAULT_FEEDS, timeout=10.0)

    print(f"Total topics discovered live: {len(discovered)}\n")
    for idx, t in enumerate(discovered[:10], 1):
        try:
            print(f"{idx}. [{t.source_name}] {t.title}")
            print(f"   URL: {t.source_url}")
            print(f"   Discovered At: {t.discovered_at}")
            if t.description:
                snippet = t.description[:120] + "..." if len(t.description) > 120 else t.description
                print(f"   Summary: {snippet}")
            print("-" * 60)
        except UnicodeEncodeError:
            clean_title = t.title.encode("ascii", errors="replace").decode("ascii")
            print(f"{idx}. [{t.source_name}] {clean_title}")

    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
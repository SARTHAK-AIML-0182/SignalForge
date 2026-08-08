# AI Development Log

This file records prompts given to AI coding tools and the resulting development decisions during the hackathon.

## Project

SignalForge — Autonomous AI Technology Intelligence Agent

## Development Log

### Session 001

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> Initial project setup and backend architecture planning.

**Purpose:**

Establish the backend development workflow and architecture.

**Result:**

Initial repository and backend architecture being established.

### Session 002

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are working as the backend engineer for a hackathon project called SignalForge.

The project is an autonomous AI and technology persona.

The evaluator will:

1. Call POST /api/agent/init exactly once.
2. Receive an agentId.
3. Repeatedly call GET /api/agent/feed?agentId=<agentId> for approximately 48 hours.
4. No further prompts or API calls will be given to the agent after initialization.

The backend must therefore autonomously discover topics, evaluate them, write posts, remember previous activity, and publish new posts over time without depending on GET /feed requests to trigger generation.

Backend responsibilities:

- FastAPI HTTP server
- POST /api/agent/init
- GET /api/agent/feed
- SQLite persistence
- autonomous background agent loop
- topic discovery from live sources
- editorial judgment
- persona-consistent writing
- memory of published and rejected topics
- duplicate detection
- publishing rationale
- source tracking
- ISO 8601 UTC timestamps
- unique post IDs
- persistent feed
- graceful error handling

Do NOT implement the full AI agent yet.

For this task only:

1. Inspect the existing repository.
2. Determine the safest backend directory structure.
3. Create the minimal FastAPI backend skeleton.
4. Create requirements.txt.
5. Create configuration handling.
6. Create placeholder API modules.
7. Create a health endpoint for development.
8. Create a clean .gitignore.
9. Do not modify frontend code.
10. Do not implement topic discovery, AI generation, scheduler, or database logic yet.

Keep the architecture simple and suitable for a 24-hour hackathon.

After making changes:
- explain every file created or modified
- identify any assumptions
- run the available tests or basic server validation
- do not make unrelated changes.

**Result:**

Antigravity created the initial FastAPI backend structure, requirements file, configuration module, API placeholders and health endpoint.

**Human verification:**

- Reviewed generated files.
- Verified frontend files were not modified.
- Backend imports successfully.
- Health endpoint responds successfully.

### Session 003 — Agent Initialization API

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge backend.
>
> The initial FastAPI backend skeleton has already been created and committed.
>
> Now implement ONLY the agent initialization API.
>
> Requirement:
>
> POST /api/agent/init
>
> Request:
>
> {
>   "persona": {
>     "name": "NOVA",
>     "domain": "AI & Emerging Technology"
>   }
> }
>
> Response:
>
> {
>   "agentId": "unique-id"
> }
>
> Implementation requirements:
>
> 1. Create appropriate Pydantic request/response schemas.
> 2. Validate that persona.name and persona.domain are present and non-empty.
> 3. Generate a cryptographically safe unique agentId.
> 4. Store the initialized agent information in a way that will later support persistent SQLite storage.
> 5. Keep the implementation modular so the database layer can be replaced or extended later.
> 6. Return the generated agentId.
> 7. Do not implement topic discovery yet.
> 8. Do not implement the LLM writer yet.
> 9. Do not implement the autonomous scheduler yet.
> 10. Do not implement the feed endpoint yet unless it is required by the existing project structure.
> 11. Do not modify frontend files.
> 12. Do not introduce unnecessary dependencies.
> 13. Follow the existing project structure and coding conventions.
>
> Also add basic tests for:
> - successful initialization
> - missing persona
> - empty persona name
> - empty persona domain
>
> After implementation:
> - run the tests
> - run a basic API validation if possible
> - inspect for errors
> - explain the files changed
> - do not modify unrelated files.
>
> Do not implement any functionality beyond the requirements of this task.

**Result:**

Implemented the `/api/agent/init` endpoint with persona validation, unique agent ID generation, repository-based agent storage, and automated tests.

**Human Verification:**

- FastAPI Swagger UI successfully opened at `/api/docs`.
- Confirmed the required endpoint is exactly `POST /api/agent/init`.
- Successfully tested initialization with the NOVA persona.
- Verified that a unique `agentId` is returned.
- Tested invalid empty persona name.
- Tested invalid empty persona domain.
- Automated test suite passed: 5/5 tests.

**Commit:**

feat: add agent initialization endpoint

### Session 004 — Persistent Memory Foundation

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge backend.
>
> The agent initialization API has been implemented, tested, committed, and pushed.
>
> Now implement the persistent memory foundation using SQLite.
>
> The purpose of this task is to create a reliable database layer that will be used by the autonomous agent throughout the rest of the project.
>
> Create the following core entities:
>
> 1. Agents
> 2. Topics
> 3. Posts
>
> Agents must store:
> - agent_id
> - persona name
> - persona domain
> - status
> - initialized_at
>
> Topics must store:
> - topic_id
> - agent_id
> - title
> - description
> - source_url
> - source_name
> - discovered_at
> - editorial score
> - status
>
> Posts must store:
> - post_id
> - agent_id
> - topic_id
> - text
> - rationale
> - sources
> - editorial score
> - created_at
>
> Requirements:
>
> 1. Use SQLite.
> 2. Keep the database file inside the backend project data directory.
> 3. Create a dedicated database module.
> 4. Create clear database models/schema definitions.
> 5. Create repository/data-access functions rather than putting database queries directly inside API routes.
> 6. Make database initialization automatic when the application starts.
> 7. Preserve data across application restarts.
> 8. Use UTC timestamps.
> 9. Use unique identifiers for agents, topics, and posts.
> 10. Store post sources in a structured way that can later be returned through the API.
> 11. Keep the implementation simple and appropriate for a 24-hour hackathon.
> 12. Do not implement topic discovery yet.
> 13. Do not implement editorial judgment yet.
> 14. Do not implement the LLM writer yet.
> 15. Do not implement the autonomous scheduler yet.
> 16. Do not modify frontend files.
> 17. Do not change the existing POST /api/agent/init API contract.
> 18. Update the existing agent initialization implementation so that newly initialized agents are persisted in SQLite.
>
> Add automated tests covering:
> - database initialization
> - creating an agent
> - retrieving an agent
> - persistence of an agent
> - creating a topic
> - creating a post
>
> Tests must use a temporary/test database and must not corrupt the development database.
>
> After implementation:
> - run all existing tests
> - run the new database tests
> - inspect for errors
> - explain the files created or modified
> - do not make unrelated changes.
>
> Do not implement functionality beyond this task.

**Result:**

Implemented the persistent SQLite memory foundation for SignalForge. Added database initialization, agent/topic/post persistence, repository abstractions, SQLite repositories, UTC timestamps, foreign-key relationships, and automated database tests. The existing agent initialization functionality was updated to persist initialized agents.

**Human Verification:**

- Reviewed the generated database architecture.
- Verified the separation between API, repositories, and SQLite database layers.
- Verified the agents, topics, and posts database schema.
- Automated test suite passed: 10/10.
- Existing agent initialization tests passed.
- Database persistence tests passed.
- No frontend files were modified.

**Commit:**

feat: add persistent sqlite memory


### Session 005 — Live Topic Discovery

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge autonomous AI persona backend.
>
> The following functionality is already implemented and committed:
>
> - FastAPI backend
> - POST /api/agent/init
> - SQLite persistence
> - Agent repository
> - Topic repository
> - Post repository
> - Automated tests
>
> Now implement ONLY the live topic discovery subsystem.
>
> The purpose of this subsystem is to independently discover current AI and technology topics from live public information sources.
>
> IMPORTANT:
>
> This subsystem must retrieve real information at runtime. Do not hardcode article titles, fake topics, example stories, or static content.
>
> Use publicly accessible RSS/Atom feeds as the primary discovery mechanism so the system does not require paid APIs or API keys.
>
> Implement the following architecture:
>
> 1. A dedicated topic discovery module/service.
> 2. A configurable list of live RSS/Atom feed URLs.
> 3. A feed fetcher that retrieves feeds over HTTP.
> 4. RSS and Atom parsing.
> 5. Normalization of feed entries into a common topic representation.
> 6. Extraction of:
>    - title
>    - description/summary
>    - source URL
>    - source name
>    - publication/discovery timestamp
> 7. Basic validation so malformed feed entries do not crash the entire discovery process.
> 8. Timeout handling for network requests.
> 9. Graceful handling of unavailable feeds.
> 10. Duplicate detection within a discovery cycle.
> 11. Persistent storage of discovered topics using the existing TopicRepository.
> 12. Do not create a second database or repository system.
> 13. Preserve the existing database architecture.
>
> Topic discovery should be focused on AI and technology.
>
> The initial source configuration should prioritize reputable sources covering:
> - artificial intelligence
> - machine learning
> - AI agents
> - AI infrastructure
> - open-source AI
> - AI security
> - robotics
> - developer tools
> - major AI research developments
>
> Keep source configuration centralized so additional feeds can easily be added later.
>
> Add a service-level function with a clear interface, conceptually similar to:
>
> discover_topics(agent_id) -> list of discovered topics
>
> The exact implementation may differ if the existing project architecture suggests a better design.
>
> Requirements:
>
> - Use the existing SQLite TopicRepository.
> - Generate unique topic IDs.
> - Store discovered topics with status="discovered".
> - Store source URL and source name.
> - Store UTC timestamps.
> - Do not call an LLM in this subsystem.
> - Do not implement editorial scoring yet.
> - Do not implement post generation yet.
> - Do not implement the autonomous scheduler yet.
> - Do not implement the feed endpoint yet.
> - Do not modify frontend files.
> - Do not change POST /api/agent/init.
> - Do not introduce unnecessary dependencies.
>
> Testing requirements:
>
> 1. Add tests using mocked HTTP/feed responses.
> 2. Tests must not depend on the live internet.
> 3. Test successful RSS parsing.
> 4. Test Atom parsing if supported.
> 5. Test malformed feed handling.
> 6. Test unavailable feed handling.
> 7. Test duplicate detection.
> 8. Test persistence through TopicRepository.
> 9. Run the complete existing test suite as well.
>
> The production discovery service must use real live feeds, while tests must use mocked responses.
>
> After implementation:
>
> - run all tests
> - inspect the implementation for unnecessary complexity
> - verify that no fake/static topics were introduced
> - explain files created or modified
> - do not modify unrelated files.
>
> Do not implement functionality beyond live topic discovery.

**Result:**

Implemented the live topic discovery subsystem in `app/services/discovery/`. Created centralized feed source configuration in `sources.py`, robust RSS 2.0 and Atom XML parser in `feed_parser.py`, and `discover_topics(agent_id)` service in `topic_discovery.py`. Integrated HTTP fetching via `httpx` with timeout and error handling, in-memory & database deduplication, and persistence into SQLite `TopicRepository` with status `"discovered"`. Added automated unit tests using mocked HTTP responses in `tests/test_topic_discovery.py`.

**Human Verification:**

- Verified live discovery against real public AI/technology RSS feeds.
- Live discovery successfully retrieved hundreds of current topics from public sources.
- Verified RSS/Atom feed parsing and normalization.
- Verified graceful handling of unavailable feeds. The VentureBeat feed failed with a DNS resolution error, but discovery continued successfully using the remaining sources.
- Verified topic persistence in SQLite.
- Verified cross-run deduplication:
  - First discovery: 865 new topics discovered and stored.
  - Second discovery: 0 new topics discovered.
  - Total stored topics after second run: 865.
- Verified that duplicate topics are rejected based on previously stored source URLs/titles.
- Verified the complete automated test suite:
  - `test_agent_init.py`: 5 passed
  - `test_database.py`: 5 passed
  - `test_topic_discovery.py`: 6 passed
  - **Total: 16 passed**

**Commit:**

feat: implement live topic discovery and deduplication



---

### Session 006 — Editorial Judgment Engine

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge autonomous AI persona backend.
>
> The following functionality is already implemented and committed:
>
> - FastAPI backend
> - POST /api/agent/init
> - SQLite persistence
> - Agent repository
> - Topic repository
> - Post repository
> - Live RSS/Atom topic discovery
> - Feed parsing and normalization
> - Network error handling
> - Topic deduplication
> - Automated tests
>
> The live discovery subsystem can now discover hundreds of current AI and technology topics.
>
> Now implement ONLY the editorial judgment subsystem.
>
> The purpose of this subsystem is to make NOVA behave like an autonomous technology editor rather than a simple RSS-to-post generator.
>
> NOVA must evaluate discovered topics and intentionally decide whether each topic deserves publication.
>
> IMPORTANT:
>
> Do not publish every discovered topic.
>
> The editorial engine must be selective and must be capable of explicitly rejecting low-value topics.
>
> NOVA's editorial identity:
>
> Name: NOVA
>
> Domain: AI & Emerging Technology
>
> Editorial philosophy:
>
> "NOVA does not report everything that happens in technology. NOVA identifies developments that materially change how people build, secure, deploy, understand, or interact with AI and emerging technology."
>
> NOVA should prioritize:
>
> - Major AI research developments
> - Frontier model capabilities
> - AI agent architectures and autonomy
> - AI security and safety
> - AI infrastructure
> - Developer tooling that materially changes engineering workflows
> - Open-source AI developments
> - Robotics and embodied AI
> - Significant changes in AI deployment or accessibility
> - Developments with meaningful technical or industry implications
>
> NOVA should generally reject:
>
> - Minor product updates
> - Generic corporate announcements
> - Promotional content without technical significance
> - Celebrity/personality-driven technology stories
> - Repetitive coverage of an already evaluated topic
> - Topics unrelated to AI or emerging technology
> - Low-information announcements
> - Stories whose primary value is speculation or hype
>
> Implement an editorial scoring system that evaluates each topic using multiple independent signals.
>
> At minimum evaluate:
>
> 1. Relevance to NOVA's domain
> 2. Timeliness
> 3. Technical significance
> 4. Potential impact
> 5. Novelty
> 6. Persona alignment
>
> Use a transparent weighted scoring model rather than a single arbitrary score.
>
> The implementation should expose a clear service-level interface conceptually similar to:
>
> evaluate_topic(topic) -> editorial decision
>
> The result should contain enough information to explain:
>
> - the score
> - whether the topic was selected or rejected
> - the individual scoring factors
> - the reason for the decision
>
> Use a configurable publication threshold.
>
> Topics above the threshold should be marked as selected.
>
> Topics below the threshold should be marked as rejected.
>
> IMPORTANT:
>
> Rejected topics must also be persisted so that NOVA's memory contains editorial decisions, not only published content.
>
> Extend the existing topic persistence model if necessary.
>
> Do not create a second database.
>
> Do not create a second repository architecture.
>
> Preserve the existing SQLite architecture and TopicRepository.
>
> The editorial engine must also prevent unnecessary repetition by considering previously evaluated or published topics.
>
> Do not implement:
>
> - AI-generated post writing
> - Autonomous scheduling
> - Feed endpoint changes
> - Social media integration
> - Frontend changes
> - Real social media publishing
>
> Keep the implementation modular so a future LLM-based writer can consume the selected topics.
>
> Testing requirements:
>
> Add automated tests for:
>
> 1. High-value topic selection
> 2. Low-value topic rejection
> 3. Domain relevance scoring
> 4. Timeliness scoring
> 5. Technical significance scoring
> 6. Novelty handling
> 7. Persona alignment
> 8. Configurable publication threshold
> 9. Persistence of editorial decisions
> 10. Previously evaluated topics not being unnecessarily selected again
>
> Tests must not require live internet access or an external LLM.
>
> Use deterministic scoring for the initial implementation so the behavior is reproducible and testable.
>
> After implementation:
>
> - run the complete test suite
> - inspect the implementation for unnecessary complexity
> - verify that both selected and rejected decisions are persisted
> - verify that the existing discovery functionality remains intact
> - do not modify unrelated functionality.
>
> Do not implement functionality beyond the editorial judgment subsystem.

**Result:**

Implemented the autonomous Editorial Judgment Engine in `app/services/editorial/`. Built multi-factor scoring (`scorer.py`) evaluating Domain Relevance, Technical Significance, Potential Impact, Novelty, Persona Alignment, and Timeliness. Built `evaluate_topic` and `evaluate_agent_topics` (`engine.py`) with configurable publication thresholding. Updated SQLite `TopicRepository` to persist both `selected` and `rejected` topics along with editorial scores and rationales. Added 10 automated unit tests in `tests/test_editorial_engine.py`.

**Human Verification:**

- Verified multi-factor weighted scoring and configurable publication threshold (default `6.5`).
- Evaluated 267 real discovered topics:
  - Selected: 25 high-value topics (9.4%)
  - Rejected: 242 low-value/marketing/PR topics (90.6%)
- Verified persistence of both `selected` and `rejected` statuses, scores, and human-readable rationales in SQLite.
- Verified novelty checking against previously evaluated topics.
- Verified the complete automated test suite:
  - `test_agent_init.py`: 5 passed
  - `test_database.py`: 5 passed
  - `test_editorial_engine.py`: 10 passed
  - `test_topic_discovery.py`: 6 passed
  - **Total: 26 passed**

**Commit:**

feat: add editorial topic evaluation engine


### Session 007 — Research & Evidence Persistence Foundation

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge autonomous AI persona backend.
>
> The following functionality is already implemented and committed:
>
> - FastAPI backend
> - POST /api/agent/init
> - SQLite persistence
> - Agent repository
> - Topic repository
> - Post repository
> - Live RSS/Atom topic discovery
> - Feed parsing and normalization
> - Network error handling
> - Topic deduplication
> - Editorial judgment engine
> - Multi-factor editorial scoring
> - Selected/rejected topic persistence
> - Automated tests
>
> Before implementing autonomous research, establish the persistence foundation required for research and evidence.
>
> Implement ONLY the research and evidence persistence layer.
>
> Create a Research entity representing an investigation performed for a selected topic.
>
> Research must store:
>
> - research_id
> - agent_id
> - topic_id
> - status
> - confidence
> - created_at
> - completed_at
>
> Create an Evidence entity representing a piece of supporting information collected during research.
>
> Evidence must store:
>
> - evidence_id
> - research_id
> - source_url
> - source_name
> - source_type
> - title
> - retrieved_at
> - content
> - confidence
>
> Requirements:
>
> 1. Preserve the existing SQLite architecture.
> 2. Do not create another database.
> 3. Create `ResearchData` and `EvidenceData` dataclasses following the existing repository/data-model conventions.
> 4. Create `BaseResearchRepository` and `SQLiteResearchRepository`.
> 5. Create `BaseEvidenceRepository` and `SQLiteEvidenceRepository`.
> 6. Add repository dependency providers.
> 7. Export the new repositories and data models through `app.repositories`.
> 8. Extend the existing SQLite initialization with `research` and `evidence` tables.
> 9. Maintain foreign-key integrity.
> 10. Deleting an agent should cascade to its research and evidence.
> 11. Deleting a topic should cascade to its research and evidence.
> 12. Deleting a research investigation should cascade to its evidence.
> 13. Use UTC ISO 8601 timestamps consistently with the existing project.
> 14. A topic may have only one research investigation. Enforce this through a UNIQUE constraint on `topic_id` and repository-level validation.
> 15. Research must support creation, retrieval, status updates, confidence updates, and completion.
> 16. Evidence must support creation, retrieval, and listing by research investigation.
> 17. Do not implement web research or source fetching yet.
> 18. Do not implement an LLM researcher yet.
> 19. Do not implement autonomous scheduling yet.
> 20. Do not modify the frontend.
> 21. Do not modify the existing topic discovery or editorial scoring behavior.
>
> Testing requirements:
>
> Add deterministic repository/database tests covering:
>
> - research table initialization
> - evidence table initialization
> - research creation
> - research retrieval
> - research retrieval by topic
> - research status updates
> - research confidence updates
> - research completion timestamp
> - multiple evidence records for one research investigation
> - evidence retrieval
> - foreign-key cascading behavior
> - invalid agent/topic references
> - persistence across separate database connections
> - duplicate research prevention for the same topic
>
> Tests must use isolated temporary databases and must not depend on the live internet or external services.
>
> After implementation:
>
> - run the complete test suite
> - verify all existing tests remain passing
> - inspect the database schema and repository interfaces
> - verify that research and evidence persistence work across separate connections
> - verify that both foreign-key integrity and cascading deletion work correctly
> - explain all files created or modified
> - do not make unrelated changes.
>
> Do not implement functionality beyond the research and evidence persistence foundation.

**Result:**

Implemented the Research & Evidence Persistence Foundation.

Created:

- `backend/app/repositories/research_repository.py`
- `backend/app/repositories/evidence_repository.py`
- `backend/tests/test_research_repository.py`

Modified:

- `backend/app/db/database.py`
- `backend/app/repositories/__init__.py`
- `prompts.md`

The new `ResearchData` and `EvidenceData` models follow the existing repository architecture.

The `research` table now persists research investigations with status, confidence, and UTC timestamps. The `evidence` table stores source-backed evidence associated with a research investigation.

Research enforces a single investigation per topic through a `UNIQUE` constraint and repository-level validation.

Foreign-key relationships and cascading deletion are enabled for agents, topics, research, and evidence.

**Human Verification:**

- Verified the new research and evidence repository architecture.
- Verified database initialization for both new tables.
- Verified research creation, retrieval, status updates, confidence updates, and completion.
- Verified multiple evidence records can be associated with a research investigation.
- Verified foreign-key integrity.
- Verified cascading deletion behavior.
- Verified duplicate research prevention for the same topic.
- Verified persistence across separate SQLite connections.
- Verified the complete automated test suite.

Test result:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 45 items

tests\test_agent_init.py .....                                           [ 11%]
tests\test_database.py .....                                             [ 22%]
tests\test_editorial_engine.py ..........                                [ 44%]
tests\test_editorial_quality.py ....                                     [ 53%]
tests\test_research_repository.py ...............                        [ 86%]
tests\test_topic_discovery.py ......                                     [100%]

======================== 45 passed, 1 warning in 3.38s ========================

**Commit:**

feat: add research and evidence persistence



### Session 008 — Autonomous Research & Evidence Collection Engine

**Date:** 2026-08-08

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

> You are continuing development of the SignalForge autonomous AI persona backend.
>
> The following functionality is already implemented and committed:
>
> - FastAPI backend
> - POST /api/agent/init
> - SQLite persistence
> - Agent repository
> - Topic repository
> - Post repository
> - Live RSS/Atom topic discovery
> - Feed parsing and normalization
> - Network error handling
> - Topic deduplication
> - Editorial judgment engine
> - Multi-factor editorial scoring
> - Selected/rejected topic persistence
> - Research repository
> - Evidence repository
> - Research and evidence SQLite schema
> - Foreign-key integrity and cascading behavior
> - Automated tests
>
> Session 007 established the persistence foundation required for research and evidence collection.
>
> Now implement ONLY the autonomous Research & Evidence Collection Engine.
>
> The purpose of this subsystem is to take a selected editorial topic and independently gather supporting evidence from publicly accessible web sources.
>
> The engine must NOT simply copy the original RSS description and call that research.
>
> Research should attempt to gather multiple independent sources when possible and preserve source-backed evidence required by a future AI writer.
>
> Implement a clear service-level interface conceptually similar to:
>
> `research_topic(topic) -> ResearchResult`
>
> The intended workflow is:
>
> 1. Accept a selected topic.
> 2. Create or retrieve its Research record.
> 3. Mark research as `in_progress`.
> 4. Discover relevant public sources.
> 5. Fetch source content.
> 6. Normalize the retrieved information.
> 7. Store useful evidence using the existing EvidenceRepository.
> 8. Avoid storing duplicate evidence.
> 9. Calculate a deterministic research confidence score.
> 10. Mark research as `completed` when successful.
> 11. Store the completion timestamp.
> 12. Return a structured research result.
>
> If research cannot obtain useful evidence, it should fail gracefully and preserve an appropriate research status rather than crashing the entire agent.
>
> Use publicly accessible web sources and prioritize:
>
> - the original source associated with the topic
> - reputable technology publications
> - official company/project announcements
> - research papers or technical documentation when relevant
> - other reputable public sources
>
> Do not require paid APIs or API keys.
>
> Do not fabricate sources or evidence.
>
> Do not hardcode fake article content.
>
> Implement:
>
> - HTTP request timeouts
> - graceful network failure handling
> - HTTP error handling
> - malformed page handling
> - basic HTML content extraction
> - source URL preservation
> - source name preservation
> - source title extraction
> - retrieval timestamp
>
> Keep extraction deliberately simple and robust enough for the current project.
>
> Do not build a full web crawler or recursively crawl arbitrary links.
>
> Limit the number of sources fetched for one research task and make the limit configurable.
>
> Use the existing ResearchRepository and EvidenceRepository.
>
> Do not create another persistence layer.
>
> Evidence confidence must initially be deterministic and explainable.
>
> Calculate an overall research confidence score between `0.0` and `1.0`.
>
> The score should reflect the quality and quantity of collected evidence.
>
> Do not use an LLM for confidence scoring in this session.
>
> Research must support:
>
> - `pending`
> - `in_progress`
> - `completed`
> - `failed`
>
> A successful research task should end in `completed`.
>
> A research task that cannot obtain useful evidence should be handled gracefully and may end in `failed`.
>
> Preserve the research record even when research fails.
>
> Use the existing:
>
> - TopicData
> - TopicRepository
> - ResearchData
> - ResearchRepository
> - EvidenceData
> - EvidenceRepository
>
> Do not create duplicate models or repositories.
>
> Keep the research engine independent from:
>
> - post generation
> - LLM writing
> - autonomous scheduling
> - feed API changes
> - social media publishing
> - frontend
>
> Add deterministic automated tests covering:
>
> 1. Successful research workflow.
> 2. Research record transitions to `in_progress`.
> 3. Successful completion.
> 4. Evidence persistence.
> 5. Multiple evidence sources.
> 6. Duplicate source prevention.
> 7. HTTP timeout handling.
> 8. HTTP failure handling.
> 9. Malformed HTML handling.
> 10. Research failure status persistence.
> 11. Deterministic confidence calculation.
> 12. Original source prioritization.
>
> Tests must not depend on the live internet.
>
> Mock HTTP responses and use isolated temporary databases.
>
> Preserve all existing tests.
>
> After implementation:
>
> - run the complete test suite
> - verify all existing functionality remains intact
> - inspect the research workflow for unnecessary complexity
> - verify that no fake/static evidence was introduced
> - verify that evidence is actually persisted
> - verify research status transitions
> - verify confidence calculation
> - perform one controlled live research test against a real public source if practical
> - explain the files created or modified
> - identify assumptions and limitations
>
> Do NOT implement the LLM writer.
>
> Do NOT implement autonomous scheduling.
>
> Do NOT implement feed generation.
>
> Do NOT implement social publishing.
>
> Do NOT modify frontend files.
>
> Do not make unrelated changes.
>
> Do not commit or push the changes.

**Result:**

Implemented the Autonomous Research & Evidence Collection Engine.

Created:

- `backend/app/services/research/extractor.py`
- `backend/app/services/research/scorer.py`
- `backend/app/services/research/engine.py`
- `backend/app/services/research/__init__.py`
- `backend/tests/test_research_engine.py`

Modified:

- `backend/app/repositories/evidence_repository.py`
- `prompts.md`

The research engine now orchestrates the complete research workflow:

`pending → in_progress → completed / failed`

It retrieves real public web sources using HTTP, extracts and cleans HTML content, persists source-backed evidence through the existing `EvidenceRepository`, prevents duplicate evidence using normalized source URLs, and calculates deterministic research confidence.

The engine supports configurable source limits and HTTP timeouts and handles network failures gracefully.

No LLM, scheduler, publishing, social media, or frontend functionality was introduced.

**Human Verification:**

- Verified correct research status transitions.
- Verified graceful handling of HTTP and timeout failures.
- Verified duplicate evidence prevention using normalized source URLs.
- Verified HTML content is cleaned before persistence.
- Verified deterministic confidence scoring bounded between `0.0` and `1.0`.
- Verified configurable `max_sources` and HTTP timeout limits.
- Verified the existing repository architecture was preserved.
- Verified subsystem isolation from LLM generation, scheduling, publishing, and frontend functionality.
- Verified all automated tests pass.
- Performed a controlled live research test against a real public source:
  - Source: Hugging Face blog
  - Topic: AutoRound
  - Status: `completed`
  - Confidence: `0.98`
  - Evidence count: `1`
  - Evidence successfully persisted in SQLite.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 57 items

======================== 57 passed in 4.60s ========================
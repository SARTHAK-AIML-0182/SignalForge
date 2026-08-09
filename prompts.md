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



### Session 009 — Research Quality & Evidence Validation

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
> - Research/evidence SQLite schema
> - Autonomous Research & Evidence Collection Engine
> - Web content extraction
> - Duplicate evidence prevention
> - Deterministic evidence confidence scoring
> - Deterministic research confidence scoring
> - Automated tests
>
> Session 008 established the autonomous research workflow that retrieves and persists source-backed evidence.
>
> Now implement ONLY the Research Quality & Evidence Validation subsystem.
>
> The purpose of this subsystem is to determine whether collected evidence is sufficiently useful, relevant, reliable, and non-redundant for NOVA to use in a future writing/synthesis stage.
>
> IMPORTANT:
>
> Do not generate posts.
>
> Do not synthesize the final story.
>
> Do not use an LLM.
>
> Do not implement scheduling.
>
> Do not implement social publishing.
>
> Do not modify the frontend.
>
> Do not replace the existing research engine.
>
> Build this as a modular validation layer that operates on the existing ResearchData and EvidenceData models.
>
> The validation subsystem should expose a clear service-level interface conceptually similar to:
>
> `validate_research(research_id) -> ResearchValidationResult`
>
> The validation result should contain enough information to explain:
>
> - whether the research is usable
> - the overall validation score
> - evidence-level validation results
> - which evidence items passed or failed validation
> - the reasons for rejection or acceptance
> - whether additional research may be required
>
> Evaluate evidence using multiple deterministic signals.
>
> At minimum evaluate:
>
> 1. Source quality
> 2. Content quality
> 3. Relevance to the researched topic
> 4. Evidence completeness
> 5. Source diversity
> 6. Redundancy
>
> Source quality should consider characteristics such as:
>
> - official project/company sources
> - research papers
> - technical documentation
> - established technology publications
> - unknown or low-quality sources
>
> Do not hardcode a large external reputation database.
>
> Use a small transparent deterministic classification system that can be expanded later.
>
> Content quality should detect obviously weak evidence such as:
>
> - extremely short content
> - empty or nearly empty pages
> - navigation-only or boilerplate content
> - pages with insufficient informational content
>
> Relevance should be deterministic and should compare the evidence against the topic information already available through TopicRepository.
>
> Use simple explainable techniques such as normalized keyword/token overlap rather than an LLM.
>
> Evidence completeness should consider whether the research contains enough useful supporting material for the topic.
>
> Source diversity should reward evidence coming from meaningfully different sources rather than multiple copies of the same information.
>
> Redundancy should detect duplicate or near-duplicate evidence based on normalized URLs and/or normalized content.
>
> Do not delete evidence records merely because they fail validation.
>
> Evidence is part of NOVA's memory and must remain persisted.
>
> Instead, return validation decisions separately and clearly identify rejected/weak evidence.
>
> If persistence of validation results is necessary, extend the existing research/evidence persistence model carefully.
>
> Do not create a second database.
>
> Do not create a second repository architecture.
>
> Preserve the existing SQLite architecture.
>
> The validator should be deterministic and reproducible.
>
> Use bounded scores between `0.0` and `1.0`.
>
> Define transparent weights for the validation factors.
>
> The overall research validation score should be explainable from the individual factors.
>
> Research should be considered usable only when it satisfies a configurable validation threshold and has sufficient usable evidence.
>
> The validation threshold must be configurable.
>
> The system should be able to distinguish:
>
> - strong research
> - acceptable research
> - insufficient research
> - unusable research
>
> If research is insufficient, return a result indicating that additional research may be required.
>
> Do not automatically launch another research cycle in this session.
>
> Keep the validation subsystem independent from the future writing/synthesis subsystem.
>
> Add deterministic automated tests covering at minimum:
>
> 1. High-quality evidence validation.
> 2. Low-quality evidence rejection.
> 3. Source quality scoring.
> 4. Content quality scoring.
> 5. Topic/evidence relevance scoring.
> 6. Evidence completeness scoring.
> 7. Source diversity scoring.
> 8. Duplicate evidence detection.
> 9. Near-duplicate content detection.
> 10. Configurable validation threshold.
> 11. Strong research classification.
> 12. Insufficient research classification.
> 13. Validation explanations/rationales.
> 14. Existing research and evidence persistence remaining intact.
>
> Tests must not require live internet access or an external LLM.
>
> Use deterministic fixtures and isolated temporary databases.
>
> Preserve all existing tests.
>
> After implementation:
>
> - run the complete test suite
> - verify all existing functionality remains intact
> - inspect the validation scoring model for unnecessary complexity
> - verify validation scores are deterministic
> - verify weak evidence is identified without deleting persisted evidence
> - verify duplicate and near-duplicate evidence handling
> - verify configurable validation thresholds
> - verify validation explanations are human-readable
> - explain all files created or modified
> - identify assumptions and limitations
>
> Do not implement the LLM writer.
>
> Do not implement research synthesis.
>
> Do not implement autonomous scheduling.
>
> Do not implement social publishing.
>
> Do not modify frontend files.
>
> Do not modify unrelated discovery or editorial functionality.
>
> Do not commit or push the changes.

**Result:**

Implemented the Research Quality & Evidence Validation subsystem in `app/services/research/validation.py`. Evaluates 6 deterministic signals: Source Quality, Content Quality, Topic Relevance, Evidence Completeness, Source Diversity, and Redundancy. Provides analytical evidence-level validation items and overall research classification (`"strong"`, `"acceptable"`, `"insufficient"`, `"unusable"`). Added 14 automated unit tests in `tests/test_research_validation.py`. Zero SQLite evidence records are deleted during validation.

**Human Verification:**

- Verified multi-signal deterministic validation scoring and configurable thresholding (default `0.65`).
- Verified duplicate URL and near-duplicate text content (Jaccard similarity >= 0.60) detection.
- Verified evidence rejection with explicit human-readable reasons without deleting persisted SQLite evidence records.
- Verified quality classification (`"strong"`, `"acceptable"`, `"insufficient"`, `"unusable"`) and `needs_additional_research` flag.
- Performed controlled live validation test on real research (`res-c00b46...`): status `ACCEPTABLE`, score `0.84`, `is_usable=True`, `needs_additional_research=False`.
- Verified complete test suite: 71 passed out of 71 tests.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 71 items

tests\test_agent_init.py .....                                           [  7%]
tests\test_database.py .....                                             [ 14%]
tests\test_editorial_engine.py ..........                                [ 28%]
tests\test_editorial_quality.py ....                                     [ 33%]
tests\test_research_engine.py ............                               [ 50%]
tests\test_research_repository.py ...............                        [ 71%]
tests\test_research_validation.py ..............                         [ 91%]
tests\test_topic_discovery.py ......                                     [100%]

======================== 71 passed, 1 warning in 4.72s ========================
```

**Assumptions & Limitations:**

- **Analytical In-Memory Validation**: Evidence validation decisions and rejections are computed analytically and returned in `ResearchValidationResult` without altering or deleting SQLite evidence records.
- **Explainable Heuristics**: Domain tiering and keyword token overlap are used instead of external LLMs or large external domain databases.

**Code Review Verification:**

- Verified `validate_research()` returns structured `ResearchValidationResult`.
- Verified rejected evidence is retained in SQLite database.
- Verified deterministic scoring bounded between `0.0` and `1.0`.
- Verified subsystem isolation from writing, scheduling, publishing, or frontend.

**Commit:**

feat:research and evidence validation


### Session 010 — Research Synthesis & Intelligence Layer

**Date:** 2026-08-09

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
> - Research/evidence SQLite schema
> - Autonomous Research & Evidence Collection Engine
> - Web content extraction
> - Duplicate evidence prevention
> - Deterministic evidence confidence scoring
> - Deterministic research confidence scoring
> - Research Quality & Evidence Validation subsystem
> - Source quality validation
> - Content quality validation
> - Topic/evidence relevance validation
> - Evidence completeness validation
> - Source diversity validation
> - Duplicate and near-duplicate evidence detection
> - Configurable research validation threshold
> - Human-readable validation rationales
> - Automated tests
>
> Session 009 established the deterministic Research Quality & Evidence Validation subsystem.
>
> Now implement ONLY the Research Synthesis & Intelligence Layer.
>
> The purpose of this subsystem is to transform validated research evidence into a structured, source-grounded research intelligence package that a future writing/synthesis system can consume.
>
> IMPORTANT:
>
> Do not generate the final social-media post.
>
> Do not implement the LLM writer.
>
> Do not call an external LLM.
>
> Do not implement social publishing.
>
> Do not implement scheduling.
>
> Do not modify the frontend.
>
> Do not replace the existing research engine.
>
> Do not replace or weaken the existing validation subsystem.
>
> Do not automatically launch another research cycle.
>
> Build this as a modular backend service operating on the existing ResearchData, EvidenceData, TopicData, and ResearchValidationResult concepts.
>
> The synthesis layer should conceptually expose a clear service-level interface such as:
>
> `synthesize_research(research_id) -> ResearchSynthesisResult`
>
> The result must remain deterministic and source-grounded.
>
> The synthesis result should contain enough structured information for a future writer to understand the research without directly reading every raw evidence record.
>
> At minimum, include:
>
> - research_id
> - topic_id
> - topic title
> - research usability/classification
> - overall validation score
> - key findings
> - supporting evidence references
> - source references
> - source diversity information
> - important factual claims
> - evidence-backed observations
> - contradictions or conflicting claims when detectable
> - research limitations
> - confidence information
> - human-readable synthesis rationale
>
> Do not invent facts.
>
> Every synthesized finding or factual claim must be traceable back to one or more persisted EvidenceData records.
>
> The synthesis layer must use ONLY evidence that passed the Research Quality & Evidence Validation subsystem.
>
> Rejected or redundant evidence must not be used as primary support for synthesized findings.
>
> Preserve traceability.
>
> A future writer must be able to determine:
>
> `finding -> evidence_id -> source_url`
>
> for every important finding.
>
> Implement deterministic claim extraction using simple explainable techniques.
>
> Do not use an LLM.
>
> Do not attempt sophisticated semantic understanding.
>
> Prefer transparent heuristics such as:
>
> - sentence extraction
> - sentence ranking
> - topic-token overlap
> - keyword frequency
> - source quality
> - evidence validation score
> - repeated factual phrases across independent sources
>
> Avoid generating artificial natural-language facts that are not directly present in the evidence.
>
> A finding may be represented as a structured object containing:
>
> - finding_id
> - text
> - evidence_ids
> - source_urls
> - confidence
> - support_count
>
> Findings should preferably represent meaningful informational statements rather than arbitrary sentences.
>
> Implement deterministic sentence extraction/ranking.
>
> Normalize evidence content before processing.
>
> Remove obvious boilerplate and empty content.
>
> Prefer sentences that:
>
> - contain multiple topic-relevant tokens
> - contain meaningful technical or factual terms
> - are supported by high-quality evidence
> - are not duplicated
>
> Limit the number of extracted findings to a configurable maximum.
>
> Make the maximum configurable with a sensible default.
>
> Implement support aggregation.
>
> If multiple independent validated evidence sources contain closely matching factual information, increase confidence in the corresponding finding.
>
> Do not treat multiple pages from the same domain as independent sources for diversity purposes.
>
> Preserve source diversity information from the validation layer.
>
> Implement deterministic contradiction detection where reasonably possible.
>
> Do not attempt broad natural-language contradiction reasoning.
>
> Use transparent signals such as:
>
> - opposing numeric values
> - explicit negation patterns
> - conflicting statements referring to the same topic keywords
>
> If a possible contradiction is detected, record it as a limitation or conflict rather than choosing one claim arbitrarily.
>
> Implement research limitations.
>
> Limitations should include relevant conditions such as:
>
> - insufficient validated evidence
> - low source diversity
> - weak evidence support
> - possible conflicting claims
> - highly concentrated sourcing
>
> Do not delete or modify ResearchData or EvidenceData records.
>
> Do not create a second database.
>
> Do not create a second repository architecture.
>
> Preserve the existing SQLite architecture.
>
> If persistence is necessary, extend the existing research persistence model carefully and minimally.
>
> Prefer keeping synthesis as a derived deterministic result unless persistence is genuinely required by the existing architecture.
>
> The synthesis service must remain independent from the future LLM writing layer.
>
> The service must refuse to produce a usable synthesis package when research validation classifies the research as `unusable`.
>
> For `insufficient` research, return a result that clearly indicates that the research package is incomplete and additional research may be required.
>
> For `acceptable` and `strong` research, produce a structured synthesis package from validated evidence.
>
> Define clear confidence rules.
>
> Confidence values must remain bounded between `0.0` and `1.0`.
>
> The synthesis result must be deterministic and reproducible.
>
> Running synthesis twice against unchanged database contents must produce equivalent results.
>
> Add deterministic automated tests covering at minimum:
>
> 1. Synthesis from strong validated research.
> 2. Synthesis from acceptable validated research.
> 3. Refusal/incomplete result for unusable research.
> 4. Insufficient research handling.
> 5. Extraction of topic-relevant findings.
> 6. Finding traceability to evidence IDs.
> 7. Finding traceability to source URLs.
> 8. Rejected evidence is not used for synthesis.
> 9. Duplicate evidence does not create duplicate findings.
> 10. Multiple independent sources increase finding support/confidence.
> 11. Same-domain sources are not incorrectly counted as independent sources.
> 12. Configurable maximum finding count.
> 13. Deterministic synthesis results.
> 14. Limitation generation.
> 15. Basic contradiction/conflict detection.
> 16. Existing research/evidence persistence remains intact.
>
> Tests must not require live internet access or an external LLM.
>
> Use deterministic fixtures and isolated temporary databases.
>
> Preserve all existing tests.
>
> After implementation:
>
> - run the complete test suite
> - verify all existing functionality remains intact
> - inspect the synthesis model for unnecessary complexity
> - verify all findings are traceable to persisted evidence
> - verify rejected evidence cannot become synthesized support
> - verify source diversity is calculated correctly
> - verify duplicate findings are avoided
> - verify deterministic output
> - verify confidence scores are bounded between 0.0 and 1.0
> - verify limitations are human-readable
> - verify unusable research does not produce a falsely usable synthesis
> - explain all files created or modified
> - identify assumptions and limitations
>
> Do not implement the LLM writer.
>
> Do not implement final post generation.
>
> Do not implement autonomous scheduling.
>
> Do not implement social publishing.
>
> Do not modify frontend files.
>
> Do not modify unrelated discovery or editorial functionality.
>
> Do not commit or push the changes.

**Result:**

Implemented the Research Synthesis & Intelligence Layer in `app/services/research/synthesis.py`. Transforms validated research evidence into a structured, source-grounded intelligence package (`ResearchSynthesisResult`). Extracts candidate findings using sentence ranking, topic-token overlap, and evidence quality heuristics. Consolidates duplicate claims and aggregates support across independent domains while maintaining full bidirectional traceability (`finding -> evidence_ids -> source_urls`). Detects basic numerical and negation conflicts and lists human-readable limitations. Refuses synthesis for `unusable` research and flags `insufficient` research. Added 16 automated unit tests in `tests/test_research_synthesis.py`.

**Human Verification:**

- Verified deterministic sentence extraction, token-overlap ranking, and consolidation into `SynthesizedFinding` objects.
- Verified finding traceability to evidence IDs and source URLs (`finding -> evidence_ids -> source_urls`).
- Verified exclusion of rejected evidence items from synthesized findings.
- Verified support aggregation across distinct domains (independent sources boost finding confidence).
- Verified domain isolation (multiple pages on same domain count as 1 distinct domain).
- Verified conflict detection (opposing numeric/negation statements recorded as conflicts).
- Verified refusal when research is `unusable` and incomplete status when `insufficient`.
- Performed controlled live synthesis test on real research (`res-c00b46...`): status `ACCEPTABLE`, score `0.84`, confidence `0.98`, 5 clean source-grounded findings generated.
- Verified complete test suite: 87 passed out of 87 tests.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 87 items

tests\test_agent_init.py .....                                           [  5%]
tests\test_database.py .....                                             [ 11%]
tests\test_editorial_engine.py ..........                                [ 22%]
tests\test_editorial_quality.py ....                                     [ 27%]
tests\test_research_engine.py ............                               [ 41%]
tests\test_research_repository.py ...............                        [ 58%]
tests\test_research_synthesis.py ................                        [ 77%]
tests\test_research_validation.py ..............                         [ 93%]
tests\test_topic_discovery.py ......                                     [100%]

======================== 87 passed, 1 warning in 6.06s ========================
```

**Assumptions & Limitations:**

- **Deterministic Synthesis Heuristics**: Extracted findings and support aggregation rely on sentence ranking, token Jaccard similarity, and keyword overlap rather than external generative LLMs.
- **Derived In-Memory Results**: `ResearchSynthesisResult` is produced dynamically from persisted `ResearchData`, `EvidenceData`, and `TopicData` without modifying SQLite records.

**Code Review Verification:**

- Verified `synthesize_research()` returns structured `ResearchSynthesisResult`.
- Verified 100% finding traceability to evidence IDs and source URLs.
- Verified rejected evidence is excluded from findings support.
- Verified subsystem isolation from LLM writing, scheduling, publishing, or frontend.

**Commit:**

feat: add research synthesis and intelligence layer


### Session 011 — Writing Preparation & Content Brief Layer

**Date:** 2026-08-09

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
> - Research/evidence SQLite schema
> - Autonomous Research & Evidence Collection Engine
> - Web content extraction
> - Duplicate evidence prevention
> - Deterministic evidence confidence scoring
> - Deterministic research confidence scoring
> - Research Quality & Evidence Validation subsystem
> - Source quality validation
> - Content quality validation
> - Topic/evidence relevance validation
> - Evidence completeness validation
> - Source diversity validation
> - Duplicate and near-duplicate evidence detection
> - Configurable validation threshold
> - Research Synthesis & Intelligence Layer
> - Deterministic finding extraction
> - Finding support aggregation
> - Source diversity handling
> - Basic conflict detection
> - Research limitation generation
> - Full finding-to-evidence-to-source traceability
> - Automated tests
>
> Session 010 established the deterministic Research Synthesis & Intelligence Layer.
>
> Now implement ONLY the Writing Preparation & Content Brief Layer.
>
> The purpose of this subsystem is to convert a validated ResearchSynthesisResult into a structured, source-grounded Content Brief that a future writing/LLM subsystem can consume.
>
> IMPORTANT:
>
> Do not generate the final social-media post.
>
> Do not implement an LLM writer.
>
> Do not call an external LLM.
>
> Do not implement social publishing.
>
> Do not implement scheduling.
>
> Do not modify the frontend.
>
> Do not replace the research engine.
>
> Do not replace the validation subsystem.
>
> Do not replace the synthesis subsystem.
>
> Do not automatically launch another research cycle.
>
> The Content Brief must be a deterministic derived representation of the existing research synthesis.
>
> Conceptually expose a service-level interface such as:
>
> `build_content_brief(research_id) -> ContentBriefResult`
>
> The Content Brief should form a clean architectural boundary between:
>
> `Research Intelligence`
>
> and the future:
>
> `LLM Writing`
>
> The future writer should be able to consume the Content Brief without directly querying the research database.
>
> The Content Brief must contain enough structured information to guide writing while remaining completely source-grounded.
>
> At minimum include:
>
> - research_id
> - topic_id
> - topic title
> - content angle
> - audience/context
> - key findings
> - supported claims
> - supporting evidence references
> - source references
> - confidence information
> - research limitations
> - writing constraints
> - brief usability/classification
> - human-readable rationale
>
> Every important claim must remain traceable:
>
> `claim -> finding_id -> evidence_id -> source_url`
>
> Do not invent claims.
>
> Do not introduce facts that are not present in ResearchSynthesisResult.
>
> Do not perform external research.
>
> Do not call an LLM.
>
> Build the content angle deterministically.
>
> The angle should summarize what makes the selected topic worth discussing based on:
>
> - editorial relevance
> - research findings
> - technical significance
> - novelty signals already available in the research/topic data
>
> Do not invent novelty.
>
> If the available data does not support a strong angle, return a neutral evidence-based angle.
>
> Build a structured audience/context representation.
>
> The audience/context should be derived from the existing agent/topic information and should not introduce unsupported demographic assumptions.
>
> Prefer explicit values already stored by the agent or topic repositories.
>
> If no explicit audience information exists, use a transparent generic technical/technology audience classification rather than inventing personal attributes.
>
> Build supported claims from the synthesized findings.
>
> Each claim should contain:
>
> - claim_id
> - claim_text
> - finding_ids
> - evidence_ids
> - source_urls
> - confidence
>
> Claims must not contain information absent from the underlying finding.
>
> Preserve source traceability exactly.
>
> Do not rewrite claims into stronger statements than the evidence supports.
>
> Do not convert uncertain findings into definitive claims.
>
> Preserve confidence information.
>
> Build writing constraints.
>
> The constraints should explicitly tell a future writer what it must NOT do.
>
> At minimum include:
>
> - do not invent unsupported facts
> - do not cite rejected evidence
> - do not hide research limitations
> - do not overstate confidence
> - preserve factual traceability
> - do not claim independent confirmation when evidence comes from the same source domain
>
> The constraints must be represented structurally rather than only as prose.
>
> Build a ContentBriefResult containing at minimum:
>
> - research_id
> - topic_id
> - title
> - angle
> - audience
> - claims
> - findings
> - sources
> - limitations
> - constraints
> - confidence
> - is_usable
> - rationale
>
> Use bounded confidence values between `0.0` and `1.0`.
>
> The brief should inherit research usability from the ResearchSynthesisResult.
>
> If the underlying research is `unusable`, the Content Brief must not be marked usable.
>
> If research is `insufficient`, the Content Brief should clearly indicate that additional research may be required.
>
> Do not silently convert insufficient research into a fully usable brief.
>
> Strong and acceptable research may produce a usable Content Brief if enough validated findings exist.
>
> Preserve all source and evidence traceability.
>
> Do not persist the Content Brief unless persistence is genuinely required by the existing architecture.
>
> Prefer a deterministic derived result if possible.
>
> Do not create a second database.
>
> Do not create a second repository architecture.
>
> Keep the implementation modular under the existing research/content service architecture.
>
> Avoid unnecessary abstractions.
>
> The implementation should be simple enough that a future LLM writer can clearly understand the contract.
>
> Add deterministic automated tests covering at minimum:
>
> 1. Content Brief creation from strong research.
> 2. Content Brief creation from acceptable research.
> 3. Unusable research produces a non-usable brief.
> 4. Insufficient research is clearly marked.
> 5. Content angle generation.
> 6. Audience/context generation.
> 7. Claim extraction from synthesized findings.
> 8. Claim-to-finding traceability.
> 9. Claim-to-evidence traceability.
> 10. Claim-to-source traceability.
> 11. Rejected evidence cannot appear in the brief.
> 12. Research limitations are preserved.
> 13. Writing constraints are present and structured.
> 14. Confidence remains bounded between 0.0 and 1.0.
> 15. Deterministic output across repeated runs.
> 16. Existing research and evidence persistence remains intact.
>
> Tests must not require live internet access or an external LLM.
>
> Use deterministic fixtures and isolated temporary databases.
>
> Preserve all existing tests.
>
> After implementation:
>
> - run the complete test suite
> - verify all existing functionality remains intact
> - inspect the Content Brief contract for unnecessary complexity
> - verify every claim remains traceable
> - verify rejected evidence cannot leak into the brief
> - verify research limitations are preserved
> - verify confidence values are bounded
> - verify deterministic output
> - verify unusable research cannot become a usable brief
> - verify insufficient research is clearly represented
> - explain all files created or modified
> - identify assumptions and limitations
>
> Do not implement the LLM writer.
>
> Do not generate final posts.
>
> Do not implement autonomous scheduling.
>
> Do not implement social publishing.
>
> Do not modify frontend files.
>
> Do not modify unrelated discovery or editorial functionality.
>
> Do not commit or push the changes.

**Result:**

Implemented the Writing Preparation & Content Brief Layer in `app/services/research/content_brief.py`. Converts a `ResearchSynthesisResult` into a structured, source-grounded Content Brief (`ContentBriefResult`). Generates content angles deterministically, derives audience/context from persona identity, maps findings to `SupportedClaim` objects while preserving 4-level traceability (`claim_id -> finding_id -> evidence_id -> source_url`), and attaches 6 structured mandatory `WritingConstraint` rules. Added 16 automated unit tests in `tests/test_content_brief.py`.

**Human Verification:**

- Verified deterministic content angle and audience context generation.
- Verified claim-to-finding-to-evidence-to-source traceability (`claim_id -> finding_id -> evidence_id -> source_url`).
- Verified 6 structured mandatory writing constraints (`FACTUAL_INTEGRITY`, `EVIDENCE_VALIDATION`, `TRANSPARENCY`, `CONFIDENCE_ACCURACY`, `TRACEABILITY`, `DIVERSITY_HONESTY`).
- Verified rejection when underlying research is `unusable` and incomplete status when `insufficient`.
- Performed controlled live test on real research (`res-c00b46...`): status `ACCEPTABLE`, brief confidence `0.98`, 5 clean supported claims generated with full traceability.
- Verified complete test suite: 103 passed out of 103 tests.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 103 items

tests\test_agent_init.py .....                                           [  4%]
tests\test_content_brief.py ................                             [ 20%]
tests\test_database.py .....                                             [ 25%]
tests\test_editorial_engine.py ..........                                [ 34%]
tests\test_editorial_quality.py ....                                     [ 38%]
tests\test_research_engine.py ............                               [ 50%]
tests\test_research_repository.py ...............                        [ 65%]
tests\test_research_synthesis.py ................                        [ 80%]
tests\test_research_validation.py ..............                         [ 94%]
tests\test_topic_discovery.py ......                                     [100%]

======================= 103 passed, 1 warning in 7.87s ========================
```

**Assumptions & Limitations:**

- **Deterministic Contract Layer**: Content briefs and writing constraints are produced as derived in-memory objects to form a clean contract boundary between Research Intelligence and future LLM Writing without altering SQLite records.
- **Traceable Claims**: Claims mirror validated synthesized findings directly to ensure no unsupported facts or hallucinations are introduced.

**Code Review Verification:**

- Verified `build_content_brief()` returns structured `ContentBriefResult`.
- Verified 100% claim-to-finding-to-evidence-to-source traceability.
- Verified rejected evidence is excluded from brief claims.
- Verified subsystem isolation from LLM writing, scheduling, publishing, or frontend.

**Commit:**

feat: add content brief generation layer


### Session 012 — Evidence-Grounded Content Writer

You are continuing development of the SignalForge autonomous AI persona backend.

The following functionality is already implemented and committed:

- FastAPI backend
- SQLite persistence
- Agent repository
- Topic repository
- Post repository
- Live RSS/Atom topic discovery
- Feed parsing and normalization
- Topic deduplication
- Editorial judgment engine
- Multi-factor editorial scoring
- Selected/rejected topic persistence
- Research repository
- Evidence repository
- Autonomous Research & Evidence Collection Engine
- Web content extraction
- Duplicate evidence prevention
- Deterministic evidence confidence scoring
- Deterministic research confidence scoring
- Research Quality & Evidence Validation
- Evidence-level validation
- Source quality scoring
- Content quality scoring
- Topic/evidence relevance scoring
- Source diversity scoring
- Redundancy detection
- Research Synthesis
- Finding extraction
- Finding-to-evidence traceability
- Conflict detection
- Research limitations
- Content Brief generation
- Supported claims
- Writing constraints
- Claim-to-finding-to-evidence-to-source traceability
- Automated tests

Session 011 established the Content Brief subsystem.

The current pipeline is:

Discovery
→ Editorial Selection
→ Research
→ Evidence Validation
→ Research Synthesis
→ Content Brief
→ Writer

Now implement ONLY the Evidence-Grounded Content Writer subsystem.

The purpose of this subsystem is to transform a validated ContentBriefResult into a structured draft suitable for a future publishing pipeline.

IMPORTANT:

Do not implement social publishing.

Do not implement scheduling.

Do not implement platform-specific publishing.

Do not modify the frontend.

Do not implement autonomous posting.

Do not bypass the Content Brief.

Do not perform fresh research.

Do not directly query the web.

Do not introduce an LLM dependency unless the existing architecture already contains an explicit abstraction designed for it.

For this session, the writer should be deterministic and testable.

The writer must operate ONLY on the validated ContentBriefResult and its supported claims.

--------------------------------------------------
1. WRITER SERVICE
--------------------------------------------------

Create a modular service conceptually similar to:

`generate_draft(content_brief) -> DraftResult`

The writer must consume the existing ContentBriefResult.

Do not duplicate the research or validation logic.

Do not independently decide whether evidence is valid.

The Content Brief is the writer's source of truth.

--------------------------------------------------
2. STRUCTURED DRAFT MODEL
--------------------------------------------------

Create a structured result such as:

`DraftResult`

It should contain enough information to represent:

- draft_id
- topic_id
- research_id
- title
- hook/introduction
- body sections
- conclusion
- complete draft text
- supported claims used
- source references
- confidence
- writing warnings or limitations
- traceability information
- whether the draft is publishable

Also create a structured representation for individual draft sections if useful.

Keep the model simple.

Avoid unnecessary abstractions.

--------------------------------------------------
3. EVIDENCE-GROUNDED WRITING
--------------------------------------------------

Every substantive claim in the draft must originate from a SupportedClaim in ContentBriefResult.

Maintain explicit traceability:

draft
→ claim_id
→ finding_id
→ evidence_id
→ source_url

The writer must never invent:

- facts
- statistics
- company announcements
- benchmark results
- technical capabilities
- dates
- quotations
- source information

If information is not present in the Content Brief, it must not appear as factual content in the draft.

--------------------------------------------------
4. DETERMINISTIC DRAFT GENERATION
--------------------------------------------------

Implement deterministic generation using the information already present in:

- topic title
- topic description
- content angle
- audience context
- supported claims
- findings
- writing constraints
- limitations

The output should read like a coherent technical AI/technology article rather than a raw list of evidence.

Use simple deterministic templates and composition logic.

The system should be able to generate:

1. Title
2. Hook / introduction
3. Main body sections
4. Conclusion
5. Source references

The exact wording may be deterministic template-driven.

Do not attempt sophisticated natural-language generation.

Do not use an LLM.

--------------------------------------------------
5. CONTENT ANGLE
--------------------------------------------------

Use the Content Brief's selected content angle to influence the structure.

For example:

- technical analysis
- practical implications
- benchmark-focused analysis
- enterprise impact
- research insight
- emerging technology explanation

Do not create a new angle independently.

--------------------------------------------------
6. AUDIENCE CONTEXT
--------------------------------------------------

Respect the audience information already generated by the Content Brief.

The writer should adapt structure and terminology according to the supplied audience context.

Do not invent a new persona.

Do not hardcode unrelated audience assumptions.

--------------------------------------------------
7. WRITING CONSTRAINTS
--------------------------------------------------

The writer must respect all WritingConstraint objects supplied by the Content Brief.

At minimum enforce:

- FACTUAL_INTEGRITY
- EVIDENCE_VALIDATION
- TRANSPARENCY
- CONFIDENCE_ACCURACY
- TRACEABILITY
- DIVERSITY_HONESTY

If a constraint cannot be satisfied, the draft should contain a warning and should not be marked publishable.

--------------------------------------------------
8. SOURCE REFERENCES
--------------------------------------------------

The final draft must preserve source attribution.

Do not fabricate citations.

Every source reference must come from the Content Brief.

Where possible expose:

- source name
- source URL
- related claim IDs

The source section should make the evidence provenance understandable.

--------------------------------------------------
9. LIMITATIONS
--------------------------------------------------

Research limitations generated by the previous synthesis layer must not disappear.

If the Content Brief contains limitations such as:

- low source diversity
- limited evidence volume
- unresolved conflicts
- incomplete coverage

the draft should transparently acknowledge them when relevant.

Do not present weakly supported research as definitive.

--------------------------------------------------
10. CONFIDENCE
--------------------------------------------------

Generate a deterministic draft confidence score between:

`0.0` and `1.0`

Base it only on information already present in the Content Brief.

Do not invent confidence.

A simple explainable calculation is preferred.

For example, confidence can incorporate:

- brief confidence
- number of supported claims
- claim support quality
- evidence coverage
- limitations

Document the exact formula.

--------------------------------------------------
11. PUBLISHABILITY
--------------------------------------------------

The draft must expose:

`is_publishable`

A draft should only be publishable when:

- the Content Brief is usable
- there is at least one supported claim
- every substantive section has claim support
- required writing constraints are satisfied
- traceability is complete
- no blocking validation issue exists

If the Content Brief is unusable:

- do not generate a fabricated draft
- return a non-publishable DraftResult
- explain why writing cannot proceed

--------------------------------------------------
12. TRACEABILITY
--------------------------------------------------

This is critical.

Every generated body section should identify which supported claims it uses.

Maintain mappings such as:

`section_id -> claim_ids`

and therefore:

`section_id -> claim_id -> finding_id -> evidence_id -> source_url`

The final DraftResult must make this traceability inspectable.

--------------------------------------------------
13. SAFETY AGAINST HALLUCINATION
--------------------------------------------------

Because this is the final writing stage before future publishing, introduce deterministic safeguards.

The writer must:

- never invent unsupported facts
- never invent sources
- never invent quotations
- never invent numerical values
- never invent dates
- never invent entities
- never claim certainty beyond evidence confidence

If the available information is insufficient, explicitly state that the draft is incomplete or non-publishable.

--------------------------------------------------
14. DATABASE / PERSISTENCE
--------------------------------------------------

Do not create a second database.

Do not create a second repository architecture.

Do not modify existing research/evidence records.

The first implementation may keep DraftResult in memory if persistence is not necessary for the current architecture.

If persistence is clearly required by the existing architecture, extend the existing SQLite architecture carefully.

Do not introduce unnecessary database complexity.

--------------------------------------------------
15. TESTS
--------------------------------------------------

Create deterministic automated tests.

At minimum test:

1. Successful draft generation from a usable Content Brief.
2. Non-publishable result when the Content Brief is unusable.
3. Title generation.
4. Hook generation.
5. Body section generation.
6. Conclusion generation.
7. Content angle usage.
8. Audience context usage.
9. Supported claim usage.
10. Claim traceability.
11. Section-to-claim traceability.
12. Evidence-to-source traceability.
13. Unsupported claims are not introduced.
14. Writing constraints are respected.
15. Research limitations are preserved.
16. Source references are preserved.
17. Confidence score is deterministic.
18. Publishability rules.
19. Empty/insufficient claims handling.
20. Existing research and evidence persistence remains intact.

Tests must:

- use deterministic fixtures
- not require internet
- not require an LLM
- not modify production data
- use isolated temporary databases where persistence is involved

--------------------------------------------------
16. EXISTING TEST SUITE
--------------------------------------------------

Preserve all existing tests.

Run the complete test suite after implementation.

The existing test count before this session is:

103 tests.

Do not break existing discovery, editorial, research, validation, synthesis, or content brief functionality.

--------------------------------------------------
17. ARCHITECTURE
--------------------------------------------------

Create:

`backend/app/services/research/writer.py`

Create:

`backend/tests/test_research_writer.py`

Update:

`backend/app/services/research/__init__.py`

only as required to expose the writer service/models.

Update:

`prompts.md`

with the complete Session 012 development record.

Do not modify unrelated files.

--------------------------------------------------
18. CODE QUALITY
--------------------------------------------------

Keep the implementation:

- modular
- deterministic
- explainable
- small
- testable
- strongly typed
- consistent with the existing SignalForge architecture

Do not over-engineer the writer.

The objective is not to produce human-level prose.

The objective is to establish a reliable evidence-grounded writing layer that can later be replaced or enhanced by an LLM without changing the upstream architecture.

--------------------------------------------------
19. VERIFICATION
--------------------------------------------------

After implementation:

- run the complete pytest suite
- verify all existing tests remain green
- verify writer tests independently
- run a controlled live test using an existing Content Brief
- inspect the generated DraftResult
- verify every substantive section has claim traceability
- verify every claim ultimately maps to evidence and source URLs
- verify no unsupported information is introduced
- verify limitations are preserved
- verify confidence is deterministic
- verify publishability rules
- inspect the implementation for unnecessary complexity
- explain every file created or modified
- identify assumptions and limitations
- provide a concise code-review verification summary

Do NOT commit or push the changes.

Do NOT implement social publishing.

Do NOT implement scheduling.

Do NOT implement frontend changes.

Do NOT implement an LLM writer.

Do NOT implement autonomous posting.

The next future stage after this should be the publishing/output pipeline, not part of this session.

**Result:**

Implemented the Evidence-Grounded Content Writer in `app/services/research/writer.py`. Transforms a `ContentBriefResult` into a structured, source-grounded article draft (`DraftResult`). Generates deterministic titles, introduction hooks, body sections, conclusions, and full markdown text while preserving 5-level inspectable traceability (`draft -> section_id -> claim_id -> finding_id -> evidence_id -> source_url`). Evaluates draft warnings, enforces mandatory writing constraints, calculates bounded confidence scores (`0.0` to `1.0`), and determines publishability (`is_publishable`). Added 20 automated unit tests in `tests/test_research_writer.py`.

**Human Verification:**

- Verified deterministic title, hook, section, and conclusion composition logic.
- Verified 5-level inspectable traceability (`draft -> section_id -> claim_id -> finding_id -> evidence_id -> source_url`).
- Verified zero unsupported claims or external facts introduced into draft text.
- Verified writing constraints check and limitation preservation.
- Verified publishability rules (`is_publishable=False` when brief is unusable, zero claims, or contains warnings).
- Performed controlled live test on real research (`res-c00b46...`): status `Draft ID draft-57615f...`, confidence `0.93`, 5 clean traceable sections generated, publishability `False` due to flagged conflict warning.
- Verified complete test suite: 123 passed out of 123 tests.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 123 items

tests\test_agent_init.py .....                                           [  4%]
tests\test_content_brief.py ................                             [ 17%]
tests\test_database.py .....                                             [ 21%]
tests\test_editorial_engine.py ..........                                [ 29%]
tests\test_editorial_quality.py ....                                     [ 32%]
tests\test_research_engine.py ............                               [ 42%]
tests\test_research_repository.py ...............                        [ 54%]
tests\test_research_synthesis.py ................                        [ 67%]
tests\test_research_validation.py ..............                         [ 78%]
tests\test_research_writer.py ....................                       [ 95%]
tests\test_topic_discovery.py ......                                     [100%]

======================= 123 passed, 1 warning in 9.81s ========================
```

**Assumptions & Limitations:**

- **Deterministic Writing Engine**: Draft composition is driven by structured templates and claim mappings rather than external generative LLMs.
- **Derived In-Memory Drafts**: `DraftResult` objects are generated as derived in-memory representations of `ContentBriefResult` without modifying underlying SQLite database records.

**Code Review Verification:**

- Verified `generate_draft()` returns structured `DraftResult`.
- Verified 100% section-to-claim-to-evidence-to-source traceability.
- Verified zero facts introduced outside Content Brief claims.
- Verified subsystem isolation from social publishing, scheduling, or frontend.

**Commit:**

feat: add evidence-grounded content writer


### Session 013 — Safe Publishing & Output Pipeline

**Date:** 2026-08-09

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

You are continuing development of the SignalForge autonomous AI persona backend.

The following functionality is already implemented and committed:

- FastAPI backend
- SQLite persistence
- Agent repository
- Topic repository
- Post repository
- Live RSS/Atom topic discovery
- Feed parsing and normalization
- Topic deduplication
- Editorial judgment engine
- Multi-factor editorial scoring
- Selected/rejected topic persistence
- Research repository
- Evidence repository
- Autonomous Research & Evidence Collection Engine
- Web content extraction
- Duplicate evidence prevention
- Deterministic evidence confidence scoring
- Deterministic research confidence scoring
- Research Quality & Evidence Validation
- Evidence-level validation
- Source quality scoring
- Content quality scoring
- Topic/evidence relevance scoring
- Source diversity scoring
- Redundancy detection
- Research Synthesis
- Finding extraction
- Finding-to-evidence traceability
- Conflict detection
- Research limitations
- Content Brief generation
- Supported claims
- Writing constraints
- Claim-to-finding-to-evidence-to-source traceability
- Evidence-Grounded Content Writer
- Deterministic draft generation
- Draft publishability checks
- Draft-to-claim-to-evidence-to-source traceability
- Automated tests

The current pipeline is:

Discovery
→ Editorial Selection
→ Research
→ Evidence Validation
→ Research Synthesis
→ Content Brief
→ Evidence-Grounded Writer
→ DraftResult

Now implement ONLY the Safe Publishing & Output Pipeline.

The purpose of this subsystem is to establish a reliable boundary between generated content and future external publishing platforms.

IMPORTANT:

Do NOT implement real social-media API integrations in this session.

Do NOT implement LinkedIn API integration.

Do NOT implement X/Twitter API integration.

Do NOT implement Instagram API integration.

Do NOT implement scheduling.

Do NOT implement autonomous background execution.

Do NOT modify the frontend.

Do NOT introduce an LLM.

Do NOT bypass DraftResult.is_publishable.

Do NOT publish anything to the internet.

Do NOT create fake external publication success.

This session should establish the publishing architecture and a deterministic dry-run/mock publishing mechanism only.

--------------------------------------------------
1. PUBLISHING SERVICE
--------------------------------------------------

Create a modular publishing service conceptually similar to:

`publish_draft(draft, adapter, dry_run=True) -> PublicationResult`

The publishing service must accept a `DraftResult`.

The publishing service must be responsible for enforcing the final publishing gate.

The service must NOT regenerate or modify the draft content.

The writer remains the sole owner of draft generation.

--------------------------------------------------
2. PUBLICATION RESULT
--------------------------------------------------

Create a structured result such as:

`PublicationResult`

It should contain enough information to explain:

- publication_id
- draft_id
- platform
- status
- is_successful
- is_dry_run
- published_content
- published_at or equivalent deterministic timestamp representation
- error/warning information
- source traceability
- rationale

Use clear publication states such as:

- `blocked`
- `dry_run`
- `published`
- `failed`

The implementation may use an enum or string constants depending on the existing project style.

Keep the model simple.

--------------------------------------------------
3. FINAL PUBLISHABILITY GATE
--------------------------------------------------

This is the most important requirement.

A draft may only proceed to the publishing adapter when:

`draft.is_publishable is True`

If:

`draft.is_publishable is False`

the publishing service MUST:

- refuse publication
- return a `blocked` PublicationResult
- preserve the draft unchanged
- explain why publication was blocked
- NOT call the adapter

This must be independently tested.

The publishing service must never attempt to "fix" an invalid draft.

--------------------------------------------------
4. PUBLISHING ADAPTER INTERFACE
--------------------------------------------------

Create a platform-independent adapter abstraction.

Conceptually:

`PublishingAdapter`

with a method such as:

`publish(draft) -> AdapterPublishResult`

The publishing service should depend on the abstraction rather than a concrete platform.

Do not couple the core publishing service to LinkedIn, X, Instagram, or any other platform.

The architecture should allow future adapters such as:

- LinkedInAdapter
- XAdapter
- WebsiteAdapter
- NewsletterAdapter

but DO NOT implement real external adapters in this session.

--------------------------------------------------
5. DRY-RUN ADAPTER
--------------------------------------------------

Implement a deterministic local adapter such as:

`DryRunPublishingAdapter`

Its purpose is to simulate the publishing boundary without contacting any external service.

It should:

- receive a valid DraftResult
- return a successful dry-run result
- preserve the draft content
- expose the target platform name
- expose source traceability
- never access the internet

The dry-run adapter must NOT claim that content was actually published.

For example:

status = `dry_run`

not:

status = `published`

--------------------------------------------------
6. OUTPUT FORMATTING
--------------------------------------------------

Create a small deterministic formatting layer if necessary.

The publishing service should be able to obtain the final publishable content from DraftResult without regenerating it.

Preserve:

- title
- body
- conclusion
- relevant limitations
- source references where appropriate

Do not silently remove evidence attribution.

Do not invent platform-specific content.

Do not implement platform-specific formatting rules yet.

--------------------------------------------------
7. TRACEABILITY
--------------------------------------------------

Publishing must preserve the traceability established by previous layers.

Maintain:

publication
→ draft_id
→ section_id
→ claim_id
→ finding_id
→ evidence_id
→ source_url

The PublicationResult should expose enough traceability information to inspect where the published/dry-run content originated.

Do not duplicate the underlying research records.

Do not modify evidence.

Do not modify research.

Do not modify the Content Brief.

Do not modify the DraftResult.

--------------------------------------------------
8. PUBLICATION ELIGIBILITY
--------------------------------------------------

The publishing layer should perform deterministic checks before invoking an adapter.

At minimum verify:

1. Draft exists / is provided.
2. Draft is publishable.
3. Draft has non-empty content.
4. Draft has required traceability.
5. Draft has no blocking warnings.

If any required condition fails:

- publication must be blocked
- adapter must not be called
- PublicationResult must explain the reason.

Keep these checks deterministic and transparent.

--------------------------------------------------
9. DRY-RUN SAFETY
--------------------------------------------------

The system should default to safe behavior.

Prefer:

`dry_run=True`

as the default.

The system must never accidentally perform external publishing.

There should be an explicit boundary between:

- dry-run
- actual publication

Actual publication should remain unavailable unless a future real adapter is explicitly supplied.

--------------------------------------------------
10. IDEMPOTENCY / DUPLICATE PROTECTION
--------------------------------------------------

The publishing layer should prevent accidental duplicate publication attempts where reasonably possible.

At minimum provide a deterministic mechanism to identify a publication attempt using:

- draft_id
- platform
- publication mode

If the same draft is submitted repeatedly to the same dry-run platform, behavior should remain deterministic.

Do not build a complex distributed locking system.

Do not implement scheduling.

--------------------------------------------------
11. PERSISTENCE
--------------------------------------------------

Do not create a second database.

Do not create a second repository architecture.

Do not modify research/evidence persistence.

If publication records are persisted, extend the existing SQLite architecture carefully.

A simple publication repository is acceptable if persistence is genuinely useful.

If persistence is unnecessary for this session, keep PublicationResult in memory.

Prefer the simplest architecture consistent with the existing SignalForge codebase.

If persistence is added, it should preserve:

- publication_id
- draft_id
- platform
- status
- dry_run
- content/reference information
- timestamp
- failure reason if applicable

Never store fake "published" status for a dry-run.

--------------------------------------------------
12. TESTS
--------------------------------------------------

Create deterministic automated tests.

At minimum test:

1. Successful dry-run publication of a publishable draft.
2. Publication blocked for non-publishable draft.
3. Adapter is not called when publication is blocked.
4. Empty draft content is rejected.
5. Missing traceability is rejected.
6. Blocking warnings prevent publication.
7. Dry-run status is distinct from published status.
8. Draft content is preserved exactly.
9. Source traceability is preserved.
10. Publication result contains draft ID.
11. Publication result contains platform.
12. Publication mode is correctly reported.
13. Duplicate/idempotent dry-run behavior.
14. Deterministic publication result.
15. Adapter abstraction works independently of the publishing service.
16. Research/evidence persistence remains unchanged.
17. Existing DraftResult remains unchanged after publication attempt.
18. Existing complete test suite remains green.

Tests must:

- not require internet
- not require external APIs
- not require an LLM
- use deterministic fixtures
- use temporary databases if persistence is involved

--------------------------------------------------
13. EXISTING TEST SUITE
--------------------------------------------------

The existing suite currently contains:

123 tests.

Preserve every existing test.

Run:

`pytest -q`

after implementation.

Do not break:

- discovery
- editorial selection
- research
- evidence collection
- validation
- synthesis
- content brief
- writer

--------------------------------------------------
14. ARCHITECTURE
--------------------------------------------------

Create a focused publishing package.

Prefer:

`backend/app/services/publishing/`

with appropriate modules.

For example:

`backend/app/services/publishing/__init__.py`

`backend/app/services/publishing/service.py`

`backend/app/services/publishing/models.py`

`backend/app/services/publishing/adapters.py`

Use fewer files if the existing project style makes that more appropriate.

Create:

`backend/tests/test_publishing.py`

Do not over-engineer.

--------------------------------------------------
15. DATABASE ARCHITECTURE
--------------------------------------------------

If persistence is implemented:

- reuse the existing SQLite connection/schema architecture
- do not create another database
- do not duplicate repositories unnecessarily
- do not alter existing research/evidence records

Any schema change must be backward-compatible with the current database.

--------------------------------------------------
16. NO REAL PUBLISHING
--------------------------------------------------

This restriction is absolute for Session 013.

Do not:

- call external APIs
- send HTTP requests to social platforms
- require API credentials
- create OAuth flows
- store social-media tokens
- claim successful real-world publication

Only deterministic local dry-run behavior is allowed.

--------------------------------------------------
17. VERIFICATION
--------------------------------------------------

After implementation:

- run the complete test suite
- verify all existing 123+ tests remain green
- run publishing tests independently
- perform a controlled dry-run using an existing real DraftResult
- verify publishability gating
- verify a publishable draft reaches the dry-run adapter
- verify a non-publishable draft is blocked before adapter execution
- verify exact draft content preservation
- verify traceability preservation
- verify dry-run is never represented as actual publication
- verify duplicate/idempotent behavior
- inspect the implementation for unnecessary complexity
- verify no external network access was introduced
- explain every file created or modified
- identify assumptions and limitations
- provide a concise code-review verification summary

--------------------------------------------------
18. PROMPTS LOG
--------------------------------------------------

Update:

`prompts.md`

with:

### Session 013 — Safe Publishing & Output Pipeline

Include:

- Date
- Tool
- Developer
- Prompt
- Result
- Human Verification
- Automated Test Result
- Assumptions & Limitations
- Code Review Verification
- Commit

Do NOT claim the changes were committed or pushed.

Leave the Commit field as:

`Pending`

until the human verification and final git checkpoint are completed.

--------------------------------------------------
19. FINAL SCOPE BOUNDARY
--------------------------------------------------

The result of this session should be:

Discovery
→ Editorial Selection
→ Research
→ Evidence Validation
→ Research Synthesis
→ Content Brief
→ Evidence-Grounded Writer
→ DraftResult
→ Safe Publishing Boundary
→ Dry-Run Publication

The next future sessions may implement:

- real platform adapters
- scheduling
- autonomous execution
- operational monitoring
- end-to-end orchestration

Those are NOT part of Session 013.

Do not implement them now.

After implementation, do not commit or push.

Return:

1. Files created.
2. Files modified.
3. Complete test result.
4. Controlled dry-run result.
5. Publishability-gate verification.
6. Traceability verification.
7. Duplicate/idempotency verification.
8. Code-review verification.
9. Assumptions and limitations.
10. Confirmation that no real external publishing occurred.
11. Confirmation that changes were NOT committed or pushed.

**Result:**

Implemented the Safe Publishing & Output Pipeline in `app/services/publishing/` (`models.py`, `adapters.py`, `service.py`, `__init__.py`). Establishes a platform-independent publishing boundary that accepts `DraftResult` objects. Enforces a strict final publishability gate (`draft.is_publishable is True`), returning a `blocked` `PublicationResult` immediately without calling adapters if pre-checks or publishability fail. Includes a deterministic `DryRunPublishingAdapter` (`dry_run=True`) that simulates local publishing with `status="dry_run"` without making external network calls. Preserves exact draft content and 6-level inspectable traceability (`publication -> draft_id -> section_id -> claim_id -> finding_id -> evidence_id -> source_url`). Added 18 automated unit tests in `tests/test_publishing.py`.

**Human Verification:**

- Verified strict publishability gate enforcement: unpublishable drafts return `status="blocked"` and adapter `publish()` is **NEVER** called.
- Verified local dry-run adapter execution (`status="dry_run"`, `is_dry_run=True`, `is_successful=True`).
- Verified exact draft content preservation without modification or regeneration.
- Verified 6-level section-to-source traceability preservation in `PublicationResult`.
- Verified deterministic idempotency hashing (`publication_id` consistent across repeated submissions).
- Performed controlled dry-run test on real research (`res-c00b46...`): unpublishable draft returned `BLOCKED`, publishable draft returned `DRY_RUN` with full 5-section traceability.
- Verified complete test suite: 141 passed out of 141 tests.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 141 items

tests\test_agent_init.py .....                                           [  3%]
tests\test_content_brief.py ................                             [ 14%]
tests\test_database.py .....                                             [ 18%]
tests\test_editorial_engine.py ..........                                [ 25%]
tests\test_editorial_quality.py ....                                     [ 28%]
tests\test_publishing.py ..................                              [ 41%]
tests\test_research_engine.py ............                               [ 49%]
tests\test_research_repository.py ...............                        [ 60%]
tests\test_research_synthesis.py ................                        [ 71%]
tests\test_research_validation.py ..............                         [ 81%]
tests\test_research_writer.py ....................                       [ 95%]
tests\test_topic_discovery.py ......                                     [100%]

======================= 141 passed, 1 warning in 13.59s =======================
```

**Assumptions & Limitations:**

- **Local Dry-Run Adapter**: Session 013 provides deterministic local simulation (`DryRunPublishingAdapter`) without connecting to live social media platforms or API endpoints.
- **In-Memory Publishing Results**: `PublicationResult` objects are generated as in-memory output contracts without modifying existing SQLite research/evidence records.

**Code Review Verification:**

- Verified `publish_draft()` returns structured `PublicationResult`.
- Verified strict gating: adapter is never invoked when `draft.is_publishable` is `False`.
- Verified zero real external API calls (0 HTTP requests sent).
- Verified complete subsystem isolation from scheduling, background loops, or frontend modifications.

**Commit:**

feat: add publishing service and dry-run adapter


### Session 014 — Autonomous Agent Workflow Orchestration

**Date:** 2026-08-09

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

You are continuing development of the SignalForge autonomous AI persona backend.

The following backend subsystems are already implemented, tested, committed, and pushed:
- FastAPI backend
- POST /api/agent/init
- SQLite persistence
- Agent repository
- Topic repository
- Post repository
- Live RSS/Atom topic discovery
- Feed parsing and normalization
- Topic deduplication
- Editorial judgment engine
- Multi-factor editorial scoring
- Selected/rejected topic persistence
- Research repository
- Evidence repository
- Autonomous Research & Evidence Collection Engine
- Web content extraction
- Duplicate evidence prevention
- Deterministic evidence confidence scoring
- Deterministic research confidence scoring
- Research Quality & Evidence Validation
- Research synthesis engine
- Content brief layer
- Evidence-grounded content writer
- Safe publishing & output pipeline

Goal: Implement the Autonomous Agent Workflow Orchestration Layer (`backend/app/services/workflow/`). Connect all existing SignalForge subsystems into a 9-stage deterministic pipeline (`Discovery -> Editorial -> Research -> Validation -> Synthesis -> Brief -> Writer -> Gate -> Dry-Run Publishing`).

**Result:**

Implemented the Autonomous Agent Workflow Orchestration Layer in `app/services/workflow/` (`models.py`, `orchestrator.py`, `__init__.py`). Connects all existing SignalForge subsystems into a 9-stage deterministic pipeline (`Discovery -> Editorial -> Research -> Validation -> Synthesis -> Brief -> Writer -> Gate -> Dry-Run Publishing`). Features stage-level status reporting (`WorkflowStageResult`), topic-level failure isolation (a single topic failing research or validation does not halt other topics), configuration options (`WorkflowConfig`), and 9-stage end-to-end inspectable traceability (`workflow -> topic -> research -> evidence -> validation -> finding -> claim -> draft -> publication`). Added 20 automated unit tests in `tests/test_workflow.py`.

**Human Verification:**

- Verified 9-stage sequential pipeline execution (`topic_discovery -> editorial_evaluation -> research -> research_validation -> research_synthesis -> content_brief -> draft_generation -> publishability_check -> dry_run_publication`).
- Verified topic-level failure isolation: failed research or unpublishable draft on one topic isolates the error and allows parallel topics to proceed.
- Verified mandatory publishability gate enforcement (`draft.is_publishable is True` required before dry-run publishing stage).
- Verified complete 9-stage end-to-end traceability mapping across all pipeline stages.
- Executed controlled live workflow integration test (`scratch/test_live_workflow.py`) against `data/signalforge.db`: discovered 865 topics, evaluated 865 topics (selected 108), researched top selected topic, validated research (`acceptable`, score 0.84), synthesized 5 findings, generated content brief with 5 claims & 6 writing constraints, generated publishable 5-section draft, passed publishability check, and completed dry-run local publishing (`pub-70039e4bb69e`). Zero external publishing network calls performed.
- Verified complete unit test suite: 161 passed out of 161 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 161 items

tests\test_agent_init.py .....                                           [  3%]
tests\test_content_brief.py ................                             [ 13%]
tests\test_database.py .....                                             [ 16%]
tests\test_editorial_engine.py ..........                                [ 22%]
tests\test_editorial_quality.py ....                                     [ 24%]
tests\test_publishing.py ..................                              [ 36%]
tests\test_research_engine.py ............                               [ 43%]
tests\test_research_repository.py ...............                        [ 52%]
tests\test_research_synthesis.py ................                        [ 62%]
tests\test_research_validation.py ..............                         [ 71%]
tests\test_research_writer.py ....................                       [ 83%]
tests\test_topic_discovery.py ......                                     [ 87%]
tests\test_workflow.py ....................                              [100%]

======================= 161 passed, 1 warning in 50.24s =======================
```

**Assumptions & Limitations:**

- **Synchronous Sequential Topic Processing**: Topics selected during editorial evaluation are processed sequentially in the current turn without async background workers.
- **Local Simulation**: Dry-run publishing stage defaults to local dry-run simulation without calling external social media APIs or background job queues.

**Code Review Verification:**

- Verified `run_agent_workflow()` returns structured `AgentWorkflowResult`.
- Verified 9-stage pipeline progression and stage-level status logging.
- Verified strict publishability gate enforcement before calling `publish_draft()`.
- Verified zero real external social media API calls (0 external publishing requests sent).
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

feat: add autonomous workflow orchestration


### Session 015 — Workflow API & Execution Control

**Date:** 2026-08-09

**Tool:** Google Antigravity

**Developer:** Backend

**Prompt:**

You are continuing development of the SignalForge autonomous AI persona backend.

The following backend subsystems are already implemented, tested, committed, and pushed:
- FastAPI backend
- POST /api/agent/init
- SQLite persistence
- Agent repository
- Topic repository
- Post repository
- Live RSS/Atom topic discovery
- Feed parsing and normalization
- Topic deduplication
- Editorial judgment engine
- Multi-factor editorial scoring
- Selected/rejected topic persistence
- Research repository
- Evidence repository
- Autonomous Research & Evidence Collection Engine
- Web content extraction
- Duplicate evidence prevention
- Deterministic evidence confidence scoring
- Deterministic research confidence scoring
- Research Quality & Evidence Validation
- Research synthesis engine
- Content brief layer
- Evidence-grounded content writer
- Safe publishing & output pipeline
- Autonomous Agent Workflow Orchestration

Goal: Expose the existing workflow orchestration service through the FastAPI backend (`POST /api/agent/{agent_id}/workflow/run`). Create request/response schemas, validate input values, check agent existence, sanitize exceptions, enforce dry-run-only publishing, and preserve 9-stage end-to-end traceability.

**Result:**

Exposed the workflow orchestration service through FastAPI in `app/api/workflow_schemas.py` and `app/api/agent.py`. Implemented `POST /api/agent/{agent_id}/workflow/run` accepting `WorkflowRunRequest` (`max_topics >= 1`, `editorial_threshold in [0.0, 1.0]`, `enable_dry_run_publication`) and returning structured `WorkflowRunResponse` containing top-level fields, `stages` list (`WorkflowStageResponse`), and `traceability` map. Checks agent existence returning HTTP 404 for unknown agents, returns HTTP 422 for invalid payloads, returns HTTP 200 for controlled workflow statuses (`SUCCESS`, `PARTIAL_SUCCESS`, `NO_CONTENT`, `FAILED`), and catches unhandled exceptions returning sanitized HTTP 500 (`Internal workflow execution error.`). Added 16 automated unit tests in `tests/test_workflow_api.py`.

**Human Verification:**

- Verified `POST /api/agent/{agent_id}/workflow/run` endpoint using FastAPI `TestClient`.
- Verified HTTP 404 response for non-existent agent IDs.
- Verified HTTP 422 validation responses for invalid `max_topics` (< 1) or `editorial_threshold` (< 0.0 or > 1.0).
- Verified HTTP 500 exception handling sanitizes error detail without exposing stack traces or DB paths.
- Verified dry-run safety: API defaults to `DryRunPublishingAdapter` (`dry_run=True`) and never exposes or invokes real external publishing adapters.
- Executed controlled live API workflow request (`scratch/test_live_workflow_api.py`) against `data/signalforge.db`: returned HTTP 200 with workflow ID `wf-61a1b83373eab330`, status `SUCCESS`, 9 stage execution results, 1 publication ID (`pub-83da0ce86136`), and complete 9-stage end-to-end traceability map. Zero real external publishing network calls performed.
- Verified complete unit test suite: 177 passed out of 177 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 177 items

tests\test_agent_init.py .....                                           [  2%]
tests\test_content_brief.py ................                             [ 11%]
tests\test_database.py .....                                             [ 14%]
tests\test_editorial_engine.py ..........                                [ 20%]
tests\test_editorial_quality.py ....                                     [ 22%]
tests\test_publishing.py ..................                              [ 32%]
tests\test_research_engine.py ............                               [ 39%]
tests\test_research_repository.py ...............                        [ 48%]
tests\test_research_synthesis.py ................                        [ 57%]
tests\test_research_validation.py ..............                         [ 64%]
tests\test_research_writer.py ....................                       [ 76%]
tests\test_topic_discovery.py ......                                     [ 79%]
tests\test_workflow.py ....................                              [ 90%]
tests\test_workflow_api.py ................                              [100%]

================== 177 passed, 1 warning in 97.56s (0:01:37) ==================
```

**Assumptions & Limitations:**

- **Stateless Execution**: Omitted optional `GET /api/agent/{agent_id}/workflow/{workflow_id}` status endpoint to avoid introducing unneeded database tables or complex in-memory execution registries.
- **Dry-Run Enforcement**: Endpoint accepts boolean `enable_dry_run_publication` and defaults to local dry-run publishing simulation without connecting to real external APIs.

**Code Review Verification:**

- Verified route handler is thin and delegates execution to `run_agent_workflow()`.
- Verified agent existence check (`agent_repo.get_agent(agent_id)`).
- Verified Pydantic request and response schemas cleanly serialize JSON fields.
- Verified zero real external social media API calls (0 external requests sent).
- Verified zero LLM calls (100% deterministic logic).
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

feat: expose autonomous workflow execution API



### Session 016 — Workflow Persistence & Execution Status

You are continuing development of the SignalForge autonomous AI persona backend.

The following functionality is already implemented and tested:

- FastAPI backend
- POST /api/agent/init
- GET /api/agent/feed
- SQLite persistence
- Agent repository
- Topic repository
- Post repository
- Live RSS/Atom topic discovery
- Feed parsing and normalization
- Topic deduplication
- Editorial judgment engine
- Multi-factor editorial scoring
- Selected/rejected topic persistence
- Research repository
- Evidence repository
- Autonomous Research & Evidence Collection Engine
- Research Quality & Evidence Validation
- Research Synthesis & Intelligence
- Content Brief generation
- Deterministic Writer
- Publishing abstraction
- Dry-run publishing adapter
- 9-stage autonomous workflow orchestrator
- POST /api/agent/{agent_id}/workflow/run
- Complete workflow API response serialization
- Deterministic end-to-end traceability
- 177 automated tests currently passing

Session 015 exposed the workflow through:

POST /api/agent/{agent_id}/workflow/run

The endpoint currently executes the workflow synchronously and returns the complete result.

However, workflow execution is currently stateless from an API perspective.

There is no persistent workflow-run record and no way to retrieve a previously executed workflow by workflow_id.

Now implement ONLY the Workflow Persistence & Execution Status subsystem.

IMPORTANT:

Do not implement scheduling.

Do not implement background workers.

Do not implement Celery/RQ/Redis.

Do not implement real social-media publishing.

Do not implement OAuth.

Do not implement an LLM.

Do not modify the frontend.

Do not redesign the existing workflow stages.

Do not replace the existing workflow orchestrator.

Do not modify unrelated discovery, editorial, research, synthesis, writer, or publishing logic.

The goal of this session is to make workflow execution inspectable and persistently recoverable.

--------------------------------------------------
1. WORKFLOW DATA MODEL
--------------------------------------------------

Create a persistent SQLite representation for workflow executions.

A workflow run should contain at minimum:

- workflow_id
- agent_id
- status
- started_at
- completed_at
- is_successful
- halted_at_stage
- rationale
- selected_topic_ids
- research_ids
- draft_ids
- publication_ids
- stage results
- traceability

Use the existing SQLite architecture.

Do not create a second database.

Do not introduce an unrelated persistence framework.

Use the repository architecture already used by:

- AgentRepository
- TopicRepository
- ResearchRepository
- EvidenceRepository

Create a dedicated workflow repository, for example:

backend/app/repositories/workflow_repository.py

Use clear interfaces such as:

BaseWorkflowRepository

SQLiteWorkflowRepository

The repository must support at least:

- create_workflow(...)
- get_workflow(workflow_id)
- update_workflow(...)
- list_workflows_for_agent(agent_id)

The exact method signatures may follow the existing repository conventions.

--------------------------------------------------
2. DATABASE SCHEMA
--------------------------------------------------

Extend the existing SQLite schema carefully.

Create the minimum tables necessary to persist workflow execution state.

Prefer normalized persistence where practical.

At minimum the database must be able to reconstruct:

workflow metadata

and

individual workflow stage results.

For example, separate workflow and workflow_stage tables may be used.

Do not duplicate the entire research/evidence database.

Use foreign keys where appropriate.

Preserve existing schema and migrations/init behavior.

Existing databases must continue to initialize successfully.

Existing records must remain intact.

--------------------------------------------------
3. PERSIST WORKFLOW EXECUTION
--------------------------------------------------

Modify the existing workflow orchestration flow so that a workflow execution can be persisted.

The workflow should:

1. Create a workflow record when execution begins.
2. Persist the initial RUNNING state.
3. Persist each stage result as the workflow progresses.
4. Persist the final workflow state.
5. Persist failure information if an unexpected exception occurs.
6. Preserve completed stage information even if a later stage fails.

The persisted state must correspond to the actual returned AgentWorkflowResult.

Do not create a separate implementation of the workflow logic.

The orchestrator remains the single source of truth for workflow execution.

The persistence layer should observe/store the execution rather than duplicate the business logic.

--------------------------------------------------
4. STAGE PERSISTENCE
--------------------------------------------------

Each workflow stage should be persistable with:

- workflow_id
- stage_name
- status
- started_at if available
- completed_at if available
- rationale
- error information if applicable
- relevant traceability information if available

Stage ordering must be preserved.

The database should allow:

GET workflow -> reconstruct ordered stages.

Do not store Python objects directly.

Serialize structured values into explicit JSON/text fields where appropriate.

Serialization must be deterministic.

--------------------------------------------------
5. WORKFLOW STATUS API
--------------------------------------------------

Add:

GET /api/agent/{agent_id}/workflow/{workflow_id}

The endpoint should:

- verify the agent exists
- verify the workflow belongs to that agent
- return HTTP 404 if either resource is not found
- return the persisted workflow state
- include stage execution details
- include traceability
- include timestamps
- include final rationale

Use the existing Pydantic API schema architecture.

Create or extend schemas as appropriate.

The response should be JSON-safe and contain no implementation-specific Python objects.

--------------------------------------------------
6. LIST WORKFLOW HISTORY
--------------------------------------------------

Add:

GET /api/agent/{agent_id}/workflows

Support basic deterministic pagination if appropriate, for example:

- limit
- offset

If pagination adds unnecessary complexity, a bounded limit is acceptable.

The endpoint should return workflow summaries containing at least:

- workflow_id
- agent_id
- status
- started_at
- completed_at
- is_successful
- rationale

Do not return the complete stage payload for every historical workflow in the list endpoint.

The detailed endpoint should be used for that.

--------------------------------------------------
7. STATUS CONSISTENCY
--------------------------------------------------

Define clear workflow status behavior.

At minimum support the existing workflow statuses:

- RUNNING
- SUCCESS
- PARTIAL_SUCCESS
- NO_CONTENT
- FAILED

If the existing code already defines these statuses, reuse them.

Do not create duplicate status definitions.

The persisted status must exactly match the status returned by the orchestrator.

Verify that:

RUNNING -> final status

is correctly persisted.

If execution fails unexpectedly:

RUNNING -> FAILED

must be persisted with a sanitized rationale.

--------------------------------------------------
8. IDEMPOTENCY / DUPLICATION
--------------------------------------------------

Do not create duplicate workflow records merely because the same workflow result is queried multiple times.

GET endpoints must never create records.

Workflow IDs remain unique.

Do not introduce artificial deduplication that changes workflow execution semantics.

The same workflow_id must always resolve to the same persisted workflow record.

--------------------------------------------------
9. TRACEABILITY
--------------------------------------------------

Preserve the existing end-to-end traceability:

topic_id
-> research_id
-> validation
-> finding_ids
-> claim_ids
-> draft_id
-> publication_id

The persisted workflow must retain enough information for the API to return this traceability after the original execution has completed.

Traceability must survive process restart.

Do not rely on Python in-memory dictionaries.

--------------------------------------------------
10. ERROR SAFETY
--------------------------------------------------

Do not expose:

- database file paths
- stack traces
- filesystem paths
- internal exception implementation details

through the API.

Use sanitized error messages.

Unexpected persistence errors must not silently produce false SUCCESS states.

--------------------------------------------------
11. TESTING
--------------------------------------------------

Add deterministic automated tests.

Tests must use isolated temporary SQLite databases.

Do not use live internet access.

Do not use external APIs.

Do not use an LLM.

At minimum test:

1. Workflow repository creation.
2. Workflow retrieval.
3. Workflow update.
4. Workflow listing by agent.
5. Workflow stage persistence.
6. Ordered stage reconstruction.
7. RUNNING status persistence.
8. SUCCESS status persistence.
9. PARTIAL_SUCCESS persistence.
10. NO_CONTENT persistence.
11. FAILED persistence.
12. Workflow traceability persistence.
13. Workflow API GET by workflow_id.
14. API 404 for unknown agent.
15. API 404 for unknown workflow.
16. API 404 when workflow belongs to another agent.
17. Workflow history endpoint.
18. Pagination/limit behavior if implemented.
19. JSON serialization.
20. Persistence surviving repository re-instantiation.
21. No duplicate workflow records from GET requests.
22. Existing workflow execution behavior remains intact.
23. Existing research/evidence persistence remains intact.
24. Existing publishing safety remains intact.

Preserve every existing test.

--------------------------------------------------
12. REGRESSION VERIFICATION
--------------------------------------------------

Run the complete test suite:

python -m pytest

The complete suite must pass.

Do not accept partial test success.

Inspect any failures and fix only issues related to this session.

Do not weaken existing tests to make them pass.

--------------------------------------------------
13. CONTROLLED LIVE VERIFICATION
--------------------------------------------------

After tests pass, perform a controlled local workflow execution using the existing SQLite database.

Use the existing NOVA agent if available.

The test must remain local/deterministic.

Dry-run publishing must remain enabled.

Verify:

1. Workflow executes successfully.
2. Workflow ID is returned.
3. Workflow record exists in SQLite.
4. Stage records exist.
5. GET /api/agent/{agent_id}/workflow/{workflow_id} returns the same workflow.
6. Workflow history endpoint returns the workflow.
7. Traceability survives retrieval.
8. No real publishing occurs.
9. No LLM calls occur.

Do not make any real external publication request.

--------------------------------------------------
14. ARCHITECTURAL REQUIREMENTS
--------------------------------------------------

Keep the architecture modular:

API
  ->
workflow service/orchestrator
  ->
workflow repository
  ->
SQLite

Do not put SQL directly inside FastAPI route handlers.

Do not put HTTP logic inside repositories.

Do not duplicate workflow business logic inside API routes.

The existing workflow orchestrator remains responsible for workflow execution.

The repository is responsible for persistence.

The API is responsible for HTTP validation and serialization.

--------------------------------------------------
15. FILES
--------------------------------------------------

Create only the files necessary for this subsystem.

Likely files include:

backend/app/repositories/workflow_repository.py

backend/app/api/workflow_schemas.py
(existing schema file may be extended instead of creating another)

backend/tests/test_workflow_repository.py

backend/tests/test_workflow_status_api.py

Modify only the necessary existing files, likely:

backend/app/db/database.py

backend/app/repositories/__init__.py

backend/app/services/workflow/orchestrator.py

backend/app/services/workflow/__init__.py

backend/app/api/agent.py

backend/app/api/workflow_schemas.py

prompts.md

Do not modify unrelated files.

--------------------------------------------------
16. IMPORTANT SAFETY CONSTRAINT
--------------------------------------------------

This session must NOT introduce:

- background scheduling
- autonomous recurring execution
- real social media publishing
- OAuth credentials
- LLM calls
- frontend changes

This session is strictly about making workflow executions persistently observable and retrievable.

--------------------------------------------------
17. FINAL VERIFICATION REPORT
--------------------------------------------------

After implementation, report:

1. Files created.
2. Files modified.
3. Database schema changes.
4. Repository interface.
5. API endpoints added.
6. Workflow persistence behavior.
7. Workflow status behavior.
8. Stage persistence behavior.
9. Traceability persistence behavior.
10. Error-handling behavior.
11. Complete pytest result.
12. Controlled live verification result.
13. Assumptions and limitations.
14. Code-review verification.
15. Confirmation that no LLM was used.
16. Confirmation that no real external publishing occurred.
17. Confirmation that no scheduling was implemented.

Update prompts.md with the complete Session 016 development record.

Use the existing prompts.md format and numbering.

Do NOT commit or push any changes.

Leave the final Git state uncommitted so it can be reviewed manually.

**Result:**

Implemented persistent workflow execution storage and status inspection endpoints. Added normalized `workflows` and `workflow_stages` tables to SQLite schema in `app/db/database.py`. Created `BaseWorkflowRepository` and `SQLiteWorkflowRepository` in `app/repositories/workflow_repository.py` for workflow and stage persistence, ordered stage reconstruction, and paginated agent workflow queries. Updated `run_agent_workflow()` in `app/services/workflow/orchestrator.py` to persist initial `RUNNING` status, stage progression, failure exception information, and final `AgentWorkflowResult` state in SQLite. Added `WorkflowSummaryResponse` and `WorkflowListResponse` in `app/api/workflow_schemas.py` and exposed `GET /api/agent/{agent_id}/workflow/{workflow_id}` (detailed execution status) and `GET /api/agent/{agent_id}/workflows` (paginated history) in `app/api/agent.py`. Added 15 automated unit tests in `tests/test_workflow_repository.py` and `tests/test_workflow_status_api.py`.

**Human Verification:**

- Verified database tables `workflows` and `workflow_stages` created cleanly on database initialization without impacting existing records.
- Verified `GET /api/agent/{agent_id}/workflow/{workflow_id}` endpoint returns HTTP 200 with complete stage execution breakdown and 9-stage end-to-end traceability.
- Verified HTTP 404 responses for unknown agents, unknown workflow IDs, or cross-agent workflow ID mismatches.
- Verified `GET /api/agent/{agent_id}/workflows` returns paginated workflow summaries with `limit` and `offset` support.
- Verified GET endpoints are idempotent and never create or mutate database records.
- Executed controlled live verification script (`scratch/test_live_workflow_persistence.py`) against `data/signalforge.db`: persisted workflow `wf-a9725381253654a0`, directly queried SQLite rows in `workflows` and `workflow_stages`, and successfully queried both GET endpoints (`GET /workflow/{wf_id}` and `GET /workflows`).
- Verified complete test suite: 192 passed out of 192 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 192 items

tests\test_agent_init.py .....                                           [  2%]
tests\test_content_brief.py ................                             [ 10%]
tests\test_database.py .....                                             [ 13%]
tests\test_editorial_engine.py ..........                                [ 18%]
tests\test_editorial_quality.py ....                                     [ 20%]
tests\test_publishing.py ..................                              [ 30%]
tests\test_research_engine.py ............                               [ 36%]
tests\test_research_repository.py ...............                        [ 44%]
tests\test_research_synthesis.py ................                        [ 52%]
tests\test_research_validation.py ..............                         [ 59%]
tests\test_research_writer.py ....................                       [ 70%]
tests\test_topic_discovery.py ......                                     [ 73%]
tests\test_workflow.py ....................                              [ 83%]
tests\test_workflow_api.py ................                              [ 92%]
tests\test_workflow_repository.py .......                                [ 95%]
tests\test_workflow_status_api.py ........                               [100%]

================== 192 passed, 1 warning in 106.86s (0:01:46) ==================
```

**Assumptions & Limitations:**

- **Synchronous Execution**: Workflow execution remains synchronous when triggered via `POST /api/agent/{agent_id}/workflow/run`, persisting `RUNNING` status at start and final status upon completion within the request lifecycle.
- **Dry-Run Enforcement**: Dry-run publishing simulation remains strictly enabled. Zero external social media platform APIs or OAuth endpoints are connected.

**Code Review Verification:**

- Verified modular architecture: API -> Orchestrator -> Repository -> SQLite.
- Verified no raw SQL inside API route handlers.
- Verified no HTTP logic inside repository classes.
- Verified 9-stage traceability survives process restarts and database re-instantiation.
- Verified zero real external social media API calls (0 external requests sent).
- Verified zero LLM calls (100% deterministic logic).
- Verified zero background scheduling or background worker processes implemented.
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

`4396160` (feat: persist workflow executions and add status APIs)



### Session 017 — Workflow Observability & Run Inspection

You are continuing development of the SignalForge autonomous AI persona backend.

Sessions 001–016 are complete and verified.

Current backend capabilities include:

- FastAPI backend
- SQLite persistence
- Agent initialization
- Agent feed
- Live RSS/Atom topic discovery
- Topic normalization and deduplication
- Editorial evaluation and scoring
- Research repository
- Evidence repository
- Autonomous research/evidence collection
- Research validation
- Research synthesis
- Content brief generation
- Deterministic writer
- Publishing abstraction
- Dry-run publishing
- 9-stage autonomous workflow orchestrator
- POST /api/agent/{agent_id}/workflow/run
- Persistent workflow execution records
- Persistent workflow stage records
- GET /api/agent/{agent_id}/workflow/{workflow_id}
- GET /api/agent/{agent_id}/workflows
- Durable workflow traceability
- 192 automated tests currently passing

Session 016 made workflow execution persistently observable and recoverable.

The next objective is to improve workflow observability and inspection WITHOUT changing workflow execution semantics.

IMPORTANT:

Do not redesign the workflow orchestrator.

Do not change the existing 9 workflow stages.

Do not add scheduling.

Do not add background workers.

Do not add Celery/RQ/Redis.

Do not add real social-media publishing.

Do not add OAuth.

Do not add an LLM.

Do not modify the frontend.

Do not modify unrelated research, editorial, synthesis, writer, or publishing logic.

Do not create a second database.

Do not weaken existing tests.

The purpose of this session is to make persisted workflow executions easier to inspect and diagnose through a clean backend API.

--------------------------------------------------
1. WORKFLOW INSPECTION SUMMARY
--------------------------------------------------

Add an inspection-oriented representation of a persisted workflow execution.

The inspection response should make it easy to understand:

- workflow identity
- agent identity
- current/final status
- execution duration
- success/failure state
- halted stage
- stage counts
- successful stage count
- failed/blocked stage count
- selected topic count
- research count
- draft count
- publication count
- overall rationale
- traceability

Do not duplicate workflow execution logic.

Derive inspection information from the persisted workflow record and persisted stage records.

--------------------------------------------------
2. STAGE STATISTICS
--------------------------------------------------

For a workflow, calculate deterministic stage statistics.

At minimum expose:

- total_stages
- succeeded_stages
- failed_stages
- blocked_stages
- skipped_stages
- running_stages

Use the existing WorkflowStageStatus values.

Do not create duplicate status definitions.

The statistics must be derived from persisted stage records.

--------------------------------------------------
3. EXECUTION DURATION
--------------------------------------------------

Expose workflow execution duration.

Use:

completed_at - started_at

when the workflow has completed.

For RUNNING workflows, calculate duration relative to the current observation time only if this can be done deterministically and safely.

Prefer returning a nullable duration for incomplete executions rather than introducing unnecessary runtime behavior.

The API representation should use a JSON-safe numeric or string representation.

Choose one representation and document it clearly.

--------------------------------------------------
4. INSPECTION ENDPOINT
--------------------------------------------------

Add:

GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection

The endpoint should:

- verify the agent exists
- verify the workflow exists
- verify the workflow belongs to the agent
- return HTTP 404 for invalid resources
- return the persisted workflow inspection summary
- include stage statistics
- include execution duration
- include counts of produced entities
- include halted stage
- include rationale
- include traceability summary

Do not return unnecessary raw database fields.

Use Pydantic schemas.

Keep the route handler thin.

--------------------------------------------------
5. WORKFLOW HISTORY FILTERING
--------------------------------------------------

Extend the existing:

GET /api/agent/{agent_id}/workflows

with deterministic optional filtering.

Support useful filters such as:

- status
- successful
- limit
- offset

Status filtering must use the existing WorkflowStatus values.

Boolean filtering must distinguish:

successful=true

from

successful=false

Do not change existing endpoint behavior when filters are omitted.

Pagination must remain deterministic.

Use a stable ordering such as newest started_at first, with workflow_id as a deterministic tie-breaker.

--------------------------------------------------
6. WORKFLOW HISTORY SUMMARY
--------------------------------------------------

Extend workflow history summaries with lightweight observability information where appropriate.

The list endpoint should remain lightweight.

It may include:

- workflow_id
- agent_id
- status
- started_at
- completed_at
- is_successful
- rationale
- duration
- selected_topic_count
- research_count
- draft_count
- publication_count

Do NOT include complete stage payloads in history results.

--------------------------------------------------
7. REPOSITORY SUPPORT
--------------------------------------------------

Extend the existing workflow repository rather than creating another repository.

Add only the methods required for deterministic filtering/inspection.

Possible interfaces:

- list_workflows_by_agent(...)
- count_workflows_by_agent(...)
- get_workflow_stage_statistics(...)
- filtered workflow listing

Follow existing repository conventions.

Do not put SQL in API routes.

Do not put HTTP logic in repositories.

--------------------------------------------------
8. TRACEABILITY INSPECTION
--------------------------------------------------

The inspection endpoint must preserve visibility into the existing chain:

topic_id
-> research_id
-> validation
-> finding_ids
-> claim_ids
-> draft_id
-> publication_id

Do not alter the existing traceability data.

Provide a concise traceability summary in the inspection response.

The complete detailed traceability must remain available through the existing workflow detail endpoint.

--------------------------------------------------
9. ERROR SAFETY
--------------------------------------------------

Do not expose:

- stack traces
- filesystem paths
- database paths
- SQL statements
- internal exception details

Unexpected repository/API failures must return sanitized errors.

Do not silently report a workflow as successful if persisted state says otherwise.

--------------------------------------------------
10. TESTING
--------------------------------------------------

Add deterministic tests using isolated temporary SQLite databases.

No internet.

No external APIs.

No LLM.

At minimum test:

1. Inspection response for successful workflow.
2. Inspection response for failed workflow.
3. Stage statistics calculation.
4. Execution duration calculation.
5. Entity count calculation.
6. Inspection traceability summary.
7. Inspection endpoint success.
8. Inspection endpoint unknown agent -> 404.
9. Inspection endpoint unknown workflow -> 404.
10. Inspection endpoint cross-agent workflow -> 404.
11. History status filter.
12. History successful=true filter.
13. History successful=false filter.
14. History pagination.
15. Deterministic history ordering.
16. Existing history behavior without filters.
17. JSON serialization.
18. Persistence after repository re-instantiation.
19. Existing workflow execution remains unchanged.
20. Existing 192 tests remain passing.

Do not weaken or delete existing tests.

--------------------------------------------------
11. REGRESSION VERIFICATION
--------------------------------------------------

Run:

python -m pytest

The entire suite must pass.

Do not accept partial success.

Fix only issues related to Session 017.

--------------------------------------------------
12. CONTROLLED LIVE VERIFICATION
--------------------------------------------------

After tests pass, perform a controlled local verification against:

data/signalforge.db

Use the existing NOVA agent if available.

Verify:

1. Existing persisted workflow can be retrieved.
2. Inspection endpoint returns correct statistics.
3. History filtering works.
4. Ordering is deterministic.
5. Traceability summary is preserved.
6. No external publishing occurs.
7. No LLM calls occur.
8. No scheduling/background worker behavior exists.

Do not modify existing production-like records unnecessarily.

--------------------------------------------------
13. ARCHITECTURAL REQUIREMENTS
--------------------------------------------------

Maintain:

API
  ->
workflow service/repository
  ->
SQLite

Do not put SQL inside FastAPI routes.

Do not duplicate orchestration logic.

Do not create a second workflow persistence mechanism.

Do not change the existing workflow execution contract.

--------------------------------------------------
14. FILES
--------------------------------------------------

Create only files necessary for this subsystem.

Likely modifications:

backend/app/repositories/workflow_repository.py

backend/app/api/workflow_schemas.py

backend/app/api/agent.py

backend/tests/test_workflow_observability.py

backend/tests/test_workflow_inspection_api.py

prompts.md

Do not create unnecessary abstractions.

--------------------------------------------------
15. SAFETY CONSTRAINT
--------------------------------------------------

This session must NOT introduce:

- scheduling
- background execution
- Celery
- RQ
- Redis
- real social publishing
- OAuth
- LLM calls
- frontend changes

--------------------------------------------------
16. FINAL VERIFICATION REPORT
--------------------------------------------------

After implementation report:

1. Files created.
2. Files modified.
3. Repository changes.
4. Inspection schema.
5. Inspection endpoint.
6. History filtering.
7. Stage statistics.
8. Duration calculation.
9. Entity counts.
10. Traceability behavior.
11. Error handling.
12. Complete pytest result.
13. Controlled live verification.
14. Assumptions and limitations.
15. Code-review verification.
16. Confirmation of zero LLM usage.
17. Confirmation of zero real external publishing.
18. Confirmation of zero scheduling/background workers.

Update prompts.md with the complete Session 017 development record.

Do NOT commit or push changes.

Leave the Git state uncommitted for manual review.

**Result:**

Implemented workflow inspection summary endpoint and history filtering capabilities. Extended `BaseWorkflowRepository` and `SQLiteWorkflowRepository` in `app/repositories/workflow_repository.py` with `calculate_duration_seconds()`, `calculate_stage_stats()`, `extract_traceability_summary()`, and filtered `list_workflows_by_agent()`/`count_workflows_by_agent()` (supporting `status` string and `is_successful` boolean filters). Added `WorkflowStageStats` and `WorkflowInspectionResponse` Pydantic models to `app/api/workflow_schemas.py` and updated `WorkflowSummaryResponse` to include `duration_seconds` and entity counts. Added `GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection` and updated `GET /api/agent/{agent_id}/workflows` with optional `status` and `successful` query parameters in `app/api/agent.py`. Added 12 automated unit tests in `tests/test_workflow_observability.py` and `tests/test_workflow_inspection_api.py`.

**Human Verification:**

- Verified `GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection` returns HTTP 200 with calculated stage statistics, duration in seconds, entity counts, halted stage rationale, and concise 9-stage traceability summary.
- Verified HTTP 404 responses for unknown agents, unknown workflow IDs, or cross-agent workflow ID mismatches.
- Verified `GET /api/agent/{agent_id}/workflows` supports filtering by `status` (e.g. `status=NO_CONTENT`) and `successful` boolean (e.g. `successful=true` or `successful=false`).
- Verified GET endpoints are idempotent and never create or mutate database records.
- Executed controlled live verification script (`scratch/test_live_workflow_inspection.py`) against `data/signalforge.db`: triggered live workflow `wf-bfd8d216506ff4cc`, verified inspection endpoint response (`duration_seconds: 3.003`, `stage_stats: {'total_stages': 9, 'succeeded_stages': 2, 'skipped_stages': 7}`), and verified filtered history query results.
- Verified complete test suite: 204 passed out of 204 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 204 items

tests\test_agent_init.py .....                                           [  2%]
tests\test_content_brief.py ................                             [ 10%]
tests\test_database.py .....                                             [ 12%]
tests\test_editorial_engine.py ..........                                [ 17%]
tests\test_editorial_quality.py ....                                     [ 19%]
tests\test_publishing.py ..................                              [ 28%]
tests\test_research_engine.py ............                               [ 34%]
tests\test_research_repository.py ...............                        [ 41%]
tests\test_research_synthesis.py ................                        [ 49%]
tests\test_research_validation.py ..............                         [ 56%]
tests\test_research_writer.py ....................                       [ 66%]
tests\test_topic_discovery.py ......                                     [ 69%]
tests\test_workflow.py ....................                              [ 78%]
tests\test_workflow_api.py ................                              [ 86%]
tests\test_workflow_inspection_api.py ......                             [ 89%]
tests\test_workflow_observability.py ......                              [ 92%]
tests\test_workflow_repository.py .......                                [ 96%]
tests\test_workflow_status_api.py ........                               [100%]

================== 204 passed, 1 warning in 60.16s (0:01:00) ==================
```

**Assumptions & Limitations:**

- **Execution Duration**: Exposed as float seconds (`duration_seconds`), calculated as `(completed_at - started_at).total_seconds()` for completed runs, or `None` for incomplete/running executions.
- **Dry-Run Enforcement**: Dry-run publishing simulation remains strictly enabled. Zero external social media platform APIs or OAuth endpoints are connected.

**Code Review Verification:**

- Verified thin route handlers in FastAPI layer.
- Verified zero raw SQL inside API route handlers.
- Verified no HTTP logic inside repository layer.
- Verified stable deterministic sorting (`started_at DESC, workflow_id DESC`).
- Verified zero real external social media API calls (0 external requests sent).
- Verified zero LLM calls (100% deterministic logic).
- Verified zero background scheduling or background worker processes implemented.
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

`5377ba7` (feat: add workflow observability and inspection)



### Session 018 — Workflow Reliability, Failure Recovery & Resume Safety

You are continuing development of the SignalForge autonomous AI persona backend.

Sessions 001–017 are complete and checkpointed.

Current verified backend capabilities include:

- FastAPI backend
- SQLite persistence
- Agent initialization
- Agent feed
- Live RSS/Atom topic discovery
- Topic normalization and deduplication
- Editorial evaluation and scoring
- Research repository
- Evidence repository
- Autonomous research/evidence collection
- Research validation
- Research synthesis
- Content brief generation
- Deterministic writer
- Publishing abstraction
- Dry-run publishing
- 9-stage autonomous workflow orchestrator
- POST /api/agent/{agent_id}/workflow/run
- Persistent workflow execution records
- Persistent workflow stage records
- GET workflow detail endpoint
- GET workflow history endpoint
- Workflow inspection endpoint
- Workflow history filtering
- Stage statistics
- Execution duration
- Durable traceability
- 204 automated tests currently passing

The backend currently persists workflow execution state and exposes it through inspection APIs.

The next objective is to harden workflow reliability and failure handling.

IMPORTANT:

This session is NOT about adding scheduling.

This session is NOT about background workers.

This session is NOT about automatic workflow resumption.

This session is NOT about real social-media publishing.

This session is NOT about OAuth.

This session is NOT about LLM integration.

This session is NOT about frontend work.

Do not redesign the 9-stage workflow.

Do not change the existing workflow business logic unless required to correctly handle failure state.

Do not duplicate workflow execution logic.

Do not introduce a second persistence system.

Do not weaken existing tests.

The goal is to ensure that workflow failures are deterministic, safely persisted, diagnosable, and cannot accidentally produce false SUCCESS states or unsafe publication behavior.

--------------------------------------------------
1. FAILURE MODEL
--------------------------------------------------

Review the existing workflow execution and persistence implementation.

Define clear behavior for:

- stage-level controlled failure
- stage-level blocked result
- unexpected exception
- persistence failure
- final workflow failure
- partial workflow success
- no-content workflow

Reuse the existing:

- WorkflowStatus
- WorkflowStageStatus
- AgentWorkflowResult
- WorkflowStageResult

Do not create duplicate status enums.

The existing workflow status values must remain authoritative:

- RUNNING
- SUCCESS
- PARTIAL_SUCCESS
- NO_CONTENT
- FAILED

--------------------------------------------------
2. FAILURE PERSISTENCE
--------------------------------------------------

Ensure that when a workflow encounters an unexpected exception:

1. The workflow is already persisted as RUNNING.
2. Completed stages remain persisted.
3. The failing stage is represented appropriately.
4. The workflow transitions to FAILED.
5. completed_at is persisted.
6. is_successful is False.
7. halted_at_stage identifies the relevant stage when available.
8. rationale contains a sanitized failure explanation.
9. No stack trace is exposed through API responses.
10. No false SUCCESS state can be returned.

The persisted result must remain reconstructable after process restart.

--------------------------------------------------
3. STAGE FAILURE SEMANTICS
--------------------------------------------------

Review the existing stage execution behavior.

For each stage, distinguish between:

- SUCCEEDED
- FAILED
- BLOCKED
- SKIPPED

Do not collapse these states into generic failure.

Verify that:

- FAILED means execution encountered an error.
- BLOCKED means execution was intentionally prevented by a gate.
- SKIPPED means the stage was intentionally not executed because of workflow conditions.

Preserve existing semantics wherever already implemented.

--------------------------------------------------
4. HALT BEHAVIOR
--------------------------------------------------

When a critical stage fails:

- subsequent dependent stages must not execute
- the workflow must halt deterministically
- already completed stages must remain intact
- the persisted workflow must identify the halt point
- the final workflow status must not become SUCCESS

Do not introduce retries in this session.

Do not introduce automatic recovery.

Do not introduce background execution.

--------------------------------------------------
5. PERSISTENCE FAILURE SAFETY
--------------------------------------------------

Review how persistence errors interact with workflow execution.

The system must never silently report:

SUCCESS

when the final workflow state could not be persisted.

If final persistence fails:

- do not fabricate a successful persisted state
- return a safe failure representation
- sanitize the error
- do not expose database paths or SQL details

Do not hide persistence failures.

Do not corrupt existing workflow records.

--------------------------------------------------
6. PUBLICATION SAFETY
--------------------------------------------------

Verify that workflow failure states cannot accidentally reach publication.

The following must remain true:

- unpublishable drafts cannot be published
- failed workflow stages cannot trigger publication
- blocked workflow stages cannot trigger publication
- workflow failure cannot produce a DRY_RUN success
- no real external publishing is introduced

Use the existing publishing gate.

Do not redesign publishing.

--------------------------------------------------
7. IDEMPOTENCY / DUPLICATION SAFETY
--------------------------------------------------

Verify that failures do not create duplicate workflow records.

A workflow execution must have exactly one workflow_id.

Repeated GET requests must never create records.

Do not introduce automatic retry behavior.

Do not silently execute the workflow again.

Do not alter workflow ID generation semantics unless absolutely necessary.

--------------------------------------------------
8. PARTIAL SUCCESS
--------------------------------------------------

Review the existing PARTIAL_SUCCESS behavior.

Ensure it is deterministic and correctly persisted.

A partial success must:

- retain successful stage results
- retain failed/blocked/skipped stages
- contain correct is_successful semantics
- contain a truthful rationale
- preserve traceability for completed work
- remain reconstructable from SQLite

Do not redefine PARTIAL_SUCCESS unless the current implementation is demonstrably incorrect.

--------------------------------------------------
9. NO CONTENT
--------------------------------------------------

Review NO_CONTENT behavior.

Ensure that when no topics are selected:

- workflow status is NO_CONTENT
- is_successful follows existing semantics
- completed_at is persisted
- rationale explains why no content was produced
- no research/draft/publication stages are falsely reported as successful
- persisted workflow can still be inspected

--------------------------------------------------
10. CONTROLLED FAILURE INJECTION
--------------------------------------------------

Add deterministic test-only failure injection.

IMPORTANT:

Failure injection must exist only in tests or through a clearly isolated internal test mechanism.

Do not expose a production API switch that allows arbitrary failure injection.

Use dependency injection, monkeypatching, test doubles, or another clean testing technique.

Tests should be able to simulate:

- research stage failure
- synthesis stage failure
- draft generation failure
- publication failure
- persistence failure

without network access.

--------------------------------------------------
11. TESTING
--------------------------------------------------

Add deterministic automated tests.

Use isolated temporary SQLite databases.

No internet.

No external APIs.

No LLM.

At minimum test:

1. RUNNING state is persisted before execution.
2. Successful workflow remains SUCCESS.
3. Controlled research failure becomes FAILED.
4. Controlled synthesis failure becomes FAILED.
5. Controlled writer failure becomes FAILED.
6. Controlled publishing failure cannot become SUCCESS.
7. Failed workflow preserves completed stages.
8. Failed workflow records halted_at_stage.
9. Failed workflow has completed_at.
10. Failed workflow has is_successful=False.
11. Failure rationale is sanitized.
12. Stack traces are not exposed.
13. BLOCKED stage does not execute dependent publication.
14. SKIPPED stage is preserved correctly.
15. PARTIAL_SUCCESS remains correctly persisted.
16. NO_CONTENT remains correctly persisted.
17. Persistence failure cannot produce false SUCCESS.
18. Workflow GET after failure reconstructs the same failure state.
19. Workflow inspection after failure reports correct statistics.
20. Traceability from completed stages survives failure.
21. Repeated GET requests do not create duplicates.
22. Existing workflow API behavior remains intact.
23. Existing publishing safety tests remain intact.
24. Existing research persistence remains intact.
25. Full existing test suite remains green.

Do not weaken or delete existing tests.

--------------------------------------------------
12. REGRESSION VERIFICATION
--------------------------------------------------

Run:

python -m pytest

The entire test suite must pass.

The expected baseline is currently:

204 passed

The final number should be >= 204.

Do not accept partial success.

If failures appear, determine whether they are caused by Session 018.

Fix only relevant issues.

--------------------------------------------------
13. CONTROLLED LIVE VERIFICATION
--------------------------------------------------

After all tests pass, run a controlled local verification against:

data/signalforge.db

Use the existing NOVA agent if available.

Perform at least:

A. Normal workflow execution.

Verify:

- workflow completes
- persisted status matches returned status
- stages are persisted
- inspection works
- history works

B. Controlled failure simulation.

Use a test-only mechanism.

Verify:

- workflow begins as RUNNING
- failure is persisted as FAILED
- completed stages remain available
- halted stage is recorded
- inspection reports failure
- no publication occurs after failure

Do not intentionally damage the production-like database.

Do not send real external requests.

--------------------------------------------------
14. API VERIFICATION
--------------------------------------------------

Verify existing APIs remain correct:

POST /api/agent/{agent_id}/workflow/run

GET /api/agent/{agent_id}/workflow/{workflow_id}

GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection

GET /api/agent/{agent_id}/workflows

The API must return sanitized JSON.

No internal Python objects.

No stack traces.

No database paths.

--------------------------------------------------
15. ARCHITECTURAL REQUIREMENTS
--------------------------------------------------

Maintain:

API
  ->
workflow orchestrator
  ->
workflow repository
  ->
SQLite

Publishing remains:

workflow
  ->
publishability gate
  ->
publishing service
  ->
dry-run adapter

Do not bypass these boundaries.

Do not put SQL in API routes.

Do not put HTTP logic in repositories.

Do not put test-only failure controls into public API contracts.

--------------------------------------------------
16. FILES
--------------------------------------------------

Modify only files necessary for this subsystem.

Likely files:

backend/app/services/workflow/orchestrator.py

backend/app/services/workflow/models.py

backend/app/repositories/workflow_repository.py

backend/app/api/agent.py
only if required for failure-safe responses

backend/app/api/workflow_schemas.py
only if required

backend/tests/test_workflow_failure_recovery.py

backend/tests/test_workflow_failure_api.py

prompts.md

Do not create unnecessary abstractions.

Do not modify unrelated subsystems.

--------------------------------------------------
17. SAFETY CONSTRAINTS
--------------------------------------------------

This session must NOT introduce:

- scheduling
- recurring execution
- background workers
- Celery
- RQ
- Redis
- automatic retries
- automatic workflow resumption
- real social publishing
- OAuth
- LLM calls
- frontend changes

--------------------------------------------------
18. FINAL VERIFICATION REPORT
--------------------------------------------------

After implementation report:

1. Files created.
2. Files modified.
3. Failure model.
4. Stage failure semantics.
5. Halt behavior.
6. Persistence failure handling.
7. Publication safety.
8. Partial-success behavior.
9. No-content behavior.
10. Failure-injection testing mechanism.
11. Complete pytest result.
12. Controlled normal workflow result.
13. Controlled failure result.
14. API verification.
15. Traceability verification.
16. Error-safety verification.
17. Assumptions and limitations.
18. Code-review verification.
19. Confirmation of zero LLM usage.
20. Confirmation of zero external publishing.
21. Confirmation of zero scheduling/background workers/retries.

Update prompts.md with the complete Session 018 development record.

Do NOT commit or push changes.

Leave the final Git state uncommitted for manual review.

**Result:**

Hardened workflow execution reliability, failure persistence, exception handling, and publication safety across all 9 workflow stages. Updated `app/services/workflow/orchestrator.py` to wrap workflow execution in top-level `try...except Exception` blocks, ensuring unexpected errors transition `RUNNING` status to `FAILED`, record `halted_at_stage`, retain completed stage history, and return a sanitized failure explanation. Updated `_persist_result()` so that if `workflow_repo.save_workflow()` fails during final completion of a non-FAILED workflow, it safely returns `WorkflowStatus.FAILED` (`is_successful=False`, `halted_at_stage="persistence"`), preventing false `SUCCESS` returns when database persistence fails. Updated overall status calculation so that any stage failure with zero successful publications resolves to `WorkflowStatus.FAILED`. Added 13 automated unit and API integration tests in `tests/test_workflow_failure_recovery.py` and `tests/test_workflow_failure_api.py`.

**Human Verification:**

- Verified `POST /api/agent/{agent_id}/workflow/run` returns HTTP 200 with `status=FAILED`, `is_successful=False`, and `halted_at_stage` set appropriately when stage errors occur.
- Verified unexpected orchestrator exceptions return sanitized HTTP 500 error detail (`"Internal workflow execution error."`) without leaking stack traces or database/filesystem paths.
- Verified `GET /api/agent/{agent_id}/workflow/{workflow_id}` and `GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection` correctly reconstruct and report `FAILED` state, stage statistics, and traceability after process restarts.
- Verified GET endpoints are idempotent and never create or mutate database records.
- Executed controlled live verification script (`scratch/test_live_workflow_failure.py`) against `data/signalforge.db`: verified normal workflow execution (`status: NO_CONTENT`) and controlled failure simulation (`status: FAILED`, `halted_at_stage: research_top-live-fail-001`, `stage_stats: {'total_stages': 3, 'succeeded_stages': 2, 'failed_stages': 1}`), confirming zero real external publishing or LLM calls occurred.
- Verified complete test suite: 217 passed out of 217 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 217 items

tests\test_agent_init.py .....                                           [  2%]
tests\test_content_brief.py ................                             [  9%]
tests\test_database.py .....                                             [ 11%]
tests\test_editorial_engine.py ..........                                [ 16%]
tests\test_editorial_quality.py ....                                     [ 18%]
tests\test_publishing.py ..................                              [ 26%]
tests\test_research_engine.py ............                               [ 32%]
tests\test_research_repository.py ...............                        [ 39%]
tests\test_research_synthesis.py ................                        [ 46%]
tests\test_research_validation.py ..............                         [ 52%]
tests\test_research_writer.py ....................                       [ 62%]
tests\test_topic_discovery.py ......                                     [ 64%]
tests\test_workflow.py ....................                              [ 74%]
tests\test_workflow_api.py ................                              [ 81%]
tests\test_workflow_failure_api.py ....                                  [ 83%]
tests\test_workflow_failure_recovery.py .........                        [ 87%]
tests\test_workflow_inspection_api.py ......                             [ 90%]
tests\test_workflow_observability.py ......                              [ 93%]
tests\test_workflow_repository.py .......                                [ 96%]
tests\test_workflow_status_api.py ........                               [100%]

================== 217 passed, 1 warning in 54.01s (0:00:54) ==================
```

**Assumptions & Limitations:**

- **No Retries or Resumption**: Workflows halt deterministically upon stage failure without automatic retries or background workers.
- **Dry-Run Enforcement**: Dry-run publishing simulation remains strictly enabled. Zero external social media platform APIs or OAuth endpoints are connected.

**Code Review Verification:**

- Verified top-level exception handling in `orchestrator.py`.
- Verified persistence error safety in `_persist_result()`.
- Verified sanitized HTTP 500 error responses in `agent.py`.
- Verified zero real external social media API calls (0 external requests sent).
- Verified zero LLM calls (100% deterministic logic).
- Verified zero background scheduling, retries, or background worker processes implemented.
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

`ff7f35c` (feat: add workflow failure recovery and safety)



### Session 019 — Workflow Policy, Configuration & Execution Governance

You are continuing development of the SignalForge autonomous AI persona backend.

Sessions 001–018 are complete and checkpointed.

Current verified backend capabilities include:

- FastAPI backend
- SQLite persistence
- Agent initialization
- Agent feed
- Live RSS/Atom topic discovery
- Topic normalization and deduplication
- Editorial evaluation and scoring
- Research repository
- Evidence repository
- Autonomous research/evidence collection
- Research validation
- Research synthesis
- Content brief generation
- Deterministic writer
- Publishing abstraction
- Dry-run publishing
- 9-stage autonomous workflow orchestrator
- POST /api/agent/{agent_id}/workflow/run
- Persistent workflow execution records
- Persistent workflow stage records
- Workflow detail retrieval
- Workflow history
- Workflow inspection
- Workflow history filtering
- Stage statistics
- Execution duration
- Durable traceability
- Failure persistence
- Failure-safe workflow execution
- Sanitized workflow errors
- 217 automated tests currently passing

The workflow currently accepts execution configuration such as:

- max_topics
- editorial_threshold
- enable_dry_run_publication

These settings are currently supplied directly to the workflow execution API.

The next objective is to introduce a small, deterministic, inspectable workflow policy/configuration layer.

**Result:**

Implemented a structured, deterministic, inspectable `WorkflowPolicy` model and execution governance layer for SignalForge. Created `app/services/workflow/policy.py` defining `WorkflowPolicy` and `resolve_workflow_policy()` to enforce strict configuration bounds (`max_topics` 1–10, `editorial_threshold` 0.0–1.0 / 0.0–10.0, `publication_mode` strictly `"dry_run"` or `"disabled"`). Updated `app/db/database.py` with non-destructive schema migration adding a `policy` JSON column to the `workflows` table. Extended `SQLiteWorkflowRepository` in `workflow_repository.py` to persist and load `policy` JSON while preserving `policy: None` for legacy workflow records. Updated `orchestrator.py` to validate policy prior to stage execution or database mutations, ensuring invalid requests raise `ValueError` before workflow execution begins. Updated `workflow_schemas.py` and `agent.py` to accept `publication_mode`, handle policy validation errors with HTTP 422, and expose effective `policy` across POST run, GET status, GET inspection, and GET history endpoints. Added 20 automated unit and API integration tests in `tests/test_workflow_policy.py` and `tests/test_workflow_policy_api.py`.

**Human Verification:**

- Verified `POST /api/agent/{agent_id}/workflow/run` returns HTTP 200 with effective `policy` dictionary when provided valid default or custom parameters.
- Verified invalid configuration inputs (`max_topics` <= 0 or > 10, `publication_mode="live"`, `publication_mode="social"`) return HTTP 422 Unprocessable Entity and create 0 database records.
- Verified `GET /api/agent/{agent_id}/workflow/{workflow_id}`, `GET /api/agent/{agent_id}/workflow/{workflow_id}/inspection`, and `GET /api/agent/{agent_id}/workflows` return stored effective policy.
- Verified legacy workflow records created before Session 019 return `policy: null` gracefully without errors.
- Executed controlled live verification script (`scratch/test_live_workflow_policy.py`) against `data/signalforge.db`: verified default policy execution, custom valid policy execution, and invalid policy HTTP 422 rejection, confirming zero real external publishing or LLM calls occurred.
- Verified complete test suite: 237 passed out of 237 tests.
- Confirmed that changes were NOT committed or pushed.

**Automated Test Result:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.1, pytest-9.1.1, pluggy-1.6.0
rootdir: F:\SignalForge\backend
plugins: anyio-4.14.2
collected 237 items

tests\test_agent_init.py .....                                           [  2%]
tests\test_content_brief.py ................                             [  8%]
tests\test_database.py .....                                             [ 10%]
tests\test_editorial_engine.py ..........                                [ 15%]
tests\test_editorial_quality.py ....                                     [ 16%]
tests\test_publishing.py ..................                              [ 24%]
tests\test_research_engine.py ............                               [ 29%]
tests\test_research_repository.py ...............                        [ 35%]
tests\test_research_synthesis.py ................                        [ 42%]
tests\test_research_validation.py ..............                         [ 48%]
tests\test_research_writer.py ....................                       [ 56%]
tests\test_topic_discovery.py ......                                     [ 59%]
tests\test_workflow.py ....................                              [ 67%]
tests\test_workflow_api.py ................                              [ 74%]
tests\test_workflow_failure_api.py ....                                  [ 76%]
tests\test_workflow_failure_recovery.py .........                        [ 80%]
tests\test_workflow_inspection_api.py ......                             [ 82%]
tests\test_workflow_observability.py ......                              [ 85%]
tests\test_workflow_policy.py ...............                            [ 91%]
tests\test_workflow_policy_api.py .....                                  [ 93%]
tests\test_workflow_repository.py .......                                [ 96%]
tests\test_workflow_status_api.py ........                               [100%]

================== 237 passed, 1 warning in 93.96s (0:01:33) ==================
```

**Assumptions & Limitations:**

- **Publication Modes**: Supported modes are strictly `"dry_run"` or `"disabled"`. Live external publishing is forbidden.
- **No Retries or Resumption**: Workflows run deterministically based on resolved effective policy without automatic retries or background workers.

**Code Review Verification:**

- Verified `WorkflowPolicy` validation logic in `policy.py`.
- Verified pre-execution policy resolution in `orchestrator.py`.
- Verified non-destructive SQLite migration in `database.py`.
- Verified HTTP 422 validation handling in `agent.py`.
- Verified zero real external social media API calls (0 external requests sent).
- Verified zero LLM calls (100% deterministic logic).
- Verified zero background scheduling, retries, or background worker processes implemented.
- Verified all code changes remain uncommitted and unpushed as instructed.

**Commit:**

Pending




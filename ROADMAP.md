# Local coding assistant roadmap

Build a local coding assistant that can answer questions about project code and
documentation from VS Code, with source references and current repository context.
Start with the existing Ollama and Docker Compose setup, then validate retrieval
on one repository before expanding to multiple projects.

## Current foundation

The stack runs Neo4j, a local Ollama model, SentenceTransformer embeddings, three
Streamlit demos, a FastAPI service, and a Svelte frontend. The existing loader and
retrieval query target Stack Overflow questions and answers. They do not index
project code or provide editor tools.

The first application-level enhancement for the 4B model is now implemented in
`coding_assistant.py`: explicit non-thinking generation, strict source extraction,
local-only Ollama access, and a bounded validate-and-repair loop. The API exposes
structural validation through `POST /code`; trusted local integrations can inject
restricted executable tests as the validator. This keeps model execution separate
from validation and avoids executing generated code in the web service.

VS Code integration uses the official Ollama extension and Qwen3.5 4B, following
the provider's recommendation for coding with agent tools.
See [editor setup](docs/vscode.md). VS Code talks directly to Ollama; connecting
the project's retrieval service is a later milestone.

## Milestone 1 Local editor assistance

Deliver a usable local model connection before building custom retrieval.

The Ollama extension is installed in the Data Science profile and reaches the
local server, with Qwen3.5 4B selected in the editor. A direct Ollama smoke check
returned a structured tool call with the expected arguments using a 64K runtime
context. This checks the model's tool-call output, not an entire editor agent task.
The next validation is answer
quality with attached project files, tool-call reliability, and representative
latency. Check runtime context allocation separately from the model's advertised
maximum before expanding agent tasks.

- Install the official extension in the active VS Code profile and download the
  coding model.
- Verify model discovery and a coding response, then try explanations and small
  edits with explicit file context.
- Record latency and memory use on representative tasks. Tune model size and
  context based on those observations.

Completion criterion: VS Code lists the model and returns a useful answer about
an attached project file. Record editor validation separately from API validation.

## Milestone 2 Repeatable application operation

Make the existing service dependable enough to support editor requests.

- Consolidate the shared Python image setup and lock dependencies after a clean
  build. Preserve the existing fixes for npm build context and API health checks.
- Add a small smoke check covering service readiness, a non-streaming answer,
  stream completion, and a useful error when Ollama is unavailable.
- Fix stream worker failures and cancellation so requests terminate cleanly.
- Separate configuration for chat and embedding models, document persistence, and
  make the PDF embedding cache use the shared volume.

Completion criterion: a clean checkout starts with documented commands, and a
failed model request produces an actionable error without leaving a hanging stream.

## Milestone 3 Index one repository

Create a repository loader alongside the Stack Overflow demo. Begin with text
chunks; add language-aware parsing only where retrieval quality needs it.

- Accept an explicit repository root and respect Git ignore rules. Exclude secrets,
  binary files, generated outputs, dependency directories, and oversized files.
- Store repository identity, relative path, line range, content hash, and indexed
  Git revision where available. Identify uncommitted content explicitly.
- Introduce separate repository chunk nodes and a vector index so existing demo
  schemas and retrieval queries remain usable.
- Support repeatable indexing, changed-file updates, deletion, and rename handling.

Completion criterion: index this repository twice without duplicate chunks;
editing or deleting a fixture file updates search results, and ignored fixtures
never enter the index.

## Milestone 4 Answer with repository evidence

Expose project search and grounded answers through the API.

- Add project-scoped search with bounded results, snippets, paths, and line ranges.
- Combine vector retrieval with exact symbol or text matching where useful.
- Return citations that resolve to indexed source and flag stale results when the
  working tree has changed. Say when relevant evidence is missing.
- Create a small evaluation set of known-answer repository questions, including
  questions with no answer in the code. Measure retrieval hits and citation accuracy.

Completion criterion: answers identify the correct source for the evaluation
questions, and every returned citation maps to the indexed content. Baseline
retrieval quality must justify proceeding to editor integration.

## Milestone 5 Expose project search to VS Code

Add a local Model Context Protocol (MCP) server that wraps retrieval. The editor
supplies the tools to a compatible coding model while Ollama supplies inference.

- Provide bounded read-only tools such as `list_projects`, `search_project`, and
  `read_indexed_source`, with explicit project identifiers and clear error responses.
- Register the server through the supported VS Code MCP configuration and document
  setup for both host and development-container workflows.
- Test tool use with a model that supports the editor's required tool calls; change
  the model if the initial chat model cannot meet that contract reliably.
- Validate project boundaries, stale indexes, unavailable services, and citation
  navigation from the editor.

Completion criterion: a VS Code question retrieves context from this service and
returns a source-linked answer about code outside the initially attached file.

## Milestone 6 Expand only after the pilot works

Add multiple repositories, incremental background indexing, and backup and restore
once the single-project workflow proves useful. Keep repository isolation explicit
and measure indexing duration, retrieval latency, memory, and answer quality.

Consider import and symbol relationships in Neo4j when they improve measured
cross-file answers. Consider autocomplete, additional models, or remote hosting
as separate additions with their own resource and workflow requirements.

Completion criterion: project selection prevents context mixing, and changing one
repository updates only its own index. A documented restore recovers the indexes
or rebuilds them from their registered sources.

## Next implementation step

Complete the editor check in Milestone 1, then address stream termination and
repeatable smoke checks in Milestone 2. After that, build a repository loader for
this project as the first retrieval pilot. Milestones define dependencies and
completion criteria; dates should follow measured effort and validated results.

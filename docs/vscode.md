# VS Code with local Ollama

Use the official Ollama extension to access the local coding model from VS Code
Chat. The editor connects directly to Ollama; the Docker demo apps and Neo4j are
needed only when using this project's applications.

## Install and start

```bash
brew install ollama
brew services start ollama
ollama pull qwen3.5:4b
code --install-extension Ollama.ollama
```

If you use a named VS Code profile, install the extension in that profile as well:

```bash
code --profile 'Data Science' --install-extension Ollama.ollama
```

VS Code 1.127 or newer is required. This repository recommends the extension and
sets its endpoint to `http://127.0.0.1:11434`. Other local workspaces use the same
endpoint by default. For an editor running remotely or inside a development
container, configure the endpoint for the machine where the extension runs;
`127.0.0.1` refers to that machine, not necessarily your Mac.

## Use the coding model

1. Open a project folder in VS Code. Reload the window if the newly installed
   extension has not activated.
2. Open the Chat view and its model picker.
3. Select `qwen3.5:4b` under Ollama. Use Ask for explanations and code suggestions,
   or Agent for tasks requiring editor tools. Review proposed changes and tool
   requests as you work.
4. Attach a file or a selection and ask a concrete question, such as
   "Explain this function and suggest a test for its edge cases."

The selected local model does not require an Ollama cloud sign-in. This integration
provides chat models; inline autocomplete would require a separate integration.
Editor-supplied file context is available, while this project's Neo4j database is
not yet connected to the editor. Repository retrieval is planned in [the
roadmap](../ROADMAP.md).

Qwen3.5 4B is the VS Code provider's recommended replacement for the older
Qwen2.5-Coder model when using agent tools. The model advertises tool support.
Runtime memory also depends on context
length and concurrent workloads. Measure responsiveness on actual project tasks
before increasing the model size or context. The Docker demos still default to
`llama2`; their `.env` model selection is independent of VS Code's model picker.

## Verify and troubleshoot

```bash
ollama list
curl --fail http://127.0.0.1:11434/api/tags
ollama run qwen3.5:4b 'Write a Python function that adds two integers.'
```

If the model is missing in Chat, run **Ollama: Refresh Models** from the Command
Palette. Run **Ollama: Diagnose Models** to inspect discovery in the Ollama output
channel. Confirm that the extension is enabled in your active VS Code profile.
Keep prompts scoped to relevant files to limit memory use and improve latency.

The extension recommends at least 64K of allocated context for editor workflows.
The maximum context advertised by a model and the context allocated by Ollama
are different. Inspect the active allocation with `ollama ps` or **Ollama:
Diagnose Models**; tune context and measure memory and latency before broad agent
tasks. Start with focused requests even when a larger context is available.

Sources: [Ollama VS Code integration](https://docs.ollama.com/integrations/vscode),
[official extension](https://marketplace.visualstudio.com/items?itemName=Ollama.ollama),
[Qwen3.5 4B](https://ollama.com/library/qwen3.5:4b).

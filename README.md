# Order assistant: LangChain and LangGraph

A structured Python implementation of the order assistant in the supplied guide.
Python 3.11+ is required. The default workflow runs locally without model credentials.

## Using the order system: step-by-step walkthrough

This is a read-only order support demo. You can check existing order statuses
and ask questions about the included fictional policies. It does not create
orders, accept payments, cancel orders, or issue refunds.

### 1. Start the application

If dependencies are already installed, open PowerShell in this project and run:

```powershell
cd C:\Users\RajeshDas\langchainGraphbasic
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open **http://localhost:8501**, or the URL printed in your terminal. If the
application is already running, refresh its browser tab. See the setup sections
below if this is your first run.

### 2. Check an existing order

In the sidebar, select **Workflow · no API key**. Enter an ID in **Order ID**,
then click **Check status**. This mode works without Groq configuration.

| Input | Expected result | Meaning |
| --- | --- | --- |
| `1001` | `Order 1001: Shipped` | The demo record says the order has shipped; no carrier tracking is connected. |
| `1002` | `Order 1002: Processing` | The demo record says the order is being processed. |
| `9999` | `Order 9999: Order not found` | This ID is absent from the demo data. |
| Leave blank | `Please provide your order ID.` | Enter an ID and submit a new request. |
| `ABC` | Validation error | IDs must contain 1–32 ASCII digits. |

Enter only the ID in this mode, not a full sentence. Surrounding spaces are
removed automatically. The latest successful result appears under **Order update**.
Use **Clear results** in the sidebar to remove it from the screen.

### 3. Ask about an order in everyday language

Configure `.env` as described below, then select **Groq agent**. Enter:

```text
What is the status of order 1001?
```

Click **Check status**. The model can call the order lookup tool and explain the
returned status. Exact wording and tool selection can vary. For an exact lookup
with mandatory routing, use Workflow mode.

Each submission starts a new request. Instead of a follow-up such as
“What about that order?”, include the ID again: “Is order 1001 shipped?”
The system has no delivery date or carrier tracking data to answer when it will arrive.

### 4. Use a controlled lookup with a Groq-written reply

Select **Workflow + Groq reply**, enter `1002`, and click **Check status**.
The graph reads Processing from the repository, then asks Groq to phrase that
fact. If the model invocation fails or returns empty text, the reply falls back
to `Order 1002: Processing`. Missing credentials are configuration errors.

### 5. Ask about policies with RAG

Select **Policy Q&A · RAG**, enter a question, and click **Check status**:

```text
What is the return policy for unused items?
```

The app retrieves relevant policy passages and sends them to Groq. Read the
**Policy answer**, then review its numbered citations and the **Retrieved evidence**
excerpts. You can also ask “How long do refunds take?” or “How long does standard
shipping take?” These policies are fictional teaching examples.

Use order lookup for current order status and RAG for policy questions. This demo
cannot combine an order's delivery date and item details with policy rules to
decide whether that specific order qualifies for a return. It also cannot perform
the return or refund action.

### 6. Add another demo order

Edit `demo_repository()` in `src/order_assistant/orders.py`, for example:

```python
def demo_repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository({
        "1001": "Shipped",
        "1002": "Processing",
        "1003": "Delivered",
    })
```

Save the file, refresh or rerun Streamlit, then look up `1003`. The result will be
`Order 1003: Delivered`. This changes the Python demo records; there is no UI for
editing orders or database storage. The sidebar's example-order caption is static;
update it separately if you want it to list the new ID.

### 7. Stop or restart

Press `Ctrl+C` in the terminal to stop Streamlit. Run the same start command again
after changing `.env`. Your demo records remain in the Python file, while results
stored in the browser session are temporary.

## Which mode should I use?

| Mode | Input | Who controls execution? | Groq needed? |
| --- | --- | --- | --- |
| `graph` | An order ID such as `1001` | Python nodes and conditional edges | No |
| `agent` | A question such as `Where is order 1001?` | The model chooses whether to call the lookup tool | Yes |
| `rag` | A shipping/returns policy question | Retrieve evidence, then generate a cited answer | Yes, for generation |
| `hybrid` | An order ID such as `1002` | Python controls lookup; Groq writes the reply | Yes |

Start with `graph` to understand state and routing. Try `agent` to see model-driven
tool use, then `hybrid` to combine an explicit process with model-generated wording.
The word `hybrid` here names our workflow-plus-model mode; it does not imply RAG.

## Run on Windows PowerShell

```powershell
cd C:\Users\RajeshDas\langchainGraphbasic
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m order_assistant graph --order-id 1001
.\.venv\Scripts\python.exe -m order_assistant graph --order-id 9999
.\.venv\Scripts\python.exe -m order_assistant graph
```

Expected outputs: `Order 1001: Shipped`, `Order 9999: Order not found`,
and `Please provide your order ID.`

## Streamlit UI with Groq

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui,dev]"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env: set GROQ_API_KEY and LLM_MODEL to your Groq credentials/model.
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).
Select Workflow for a local lookup, Groq agent for natural-language questions,
or Workflow + Groq reply for model wording with explicit routing. The sidebar
shows the fictional demo orders. Results survive reruns in your browser session;
each submission is independent and does not send previous results to the model.
Use Clear results to remove the displayed result.

### Configure Groq

Open `.env` in the project root and fill in both values:

```dotenv
GROQ_API_KEY=your_groq_api_key
LLM_PROVIDER=groq
LLM_MODEL=your_available_groq_model_id
```

These are placeholders; replace them with actual values. Get your API key from the
[Groq console](https://console.groq.com/keys). The application does not choose a
default model. `LLM_PROVIDER` defaults to `groq`; other providers are rejected.
`GROQ_MODEL` remains a fallback when `LLM_MODEL` is empty. Environment variables already set in PowerShell override `.env`.
Restart Streamlit after changing configuration so subsequent requests use it.
The commands use the virtual environment's interpreter directly, so activating
the environment or changing PowerShell execution policy is unnecessary.

### Try the UI

1. Select **Workflow · no API key**, enter `1001`, and click **Check status**.
   The result is `Order 1001: Shipped`.
2. Enter `1002` to see Processing, or `9999` to see Order not found.
3. Submit an empty ID to see the request for an order ID.
4. Select **Groq agent**, enter `What is the status of order 1001?`, and submit.
   The model can call the lookup tool and phrase the result.
5. Select **Workflow + Groq reply**, enter `1002`, and submit.
   Python performs the lookup and Groq phrases the supplied status.

For workflow and hybrid modes, enter the ID alone. Agent mode accepts sentences.
Always include the order ID in a new agent question: the app does not remember
an ID from a previous submission. Stop the server with `Ctrl+C` in its terminal.

Keep your API key in `.env` or the server environment. Choose a Groq model
available in your account with tool calling for agent mode. See the
[Groq model list](https://console.groq.com/docs/models) and
[LangChain Groq integration](https://docs.langchain.com/oss/python/integrations/chat/groq).

## Deploy to Streamlit Community Cloud

Use repository `rvnextgendev/langchaingraph`, branch `main`, and entrypoint
`streamlit_app.py`. Select Python 3.11 in the deployment's advanced settings
to match the locally tested interpreter.

The root `requirements.txt` installs this project with its `ui` extras, including
Groq and Streamlit. It also makes the `src/order_assistant` package importable.
`pyproject.toml` defines the dependencies and supports Python `>=3.11,<4`.
The upper bound prevents the Poetry resolution error about LangChain not
supporting Python 4. Community Cloud gives `requirements.txt` precedence over
`pyproject.toml`; see the [deployment dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

Your local `.env` is excluded from Git and is not uploaded to Community Cloud.
In the deployed app's **Settings → Secrets**, add these root-level TOML settings:

```toml
GROQ_API_KEY = "your_new_groq_api_key"
LLM_PROVIDER = "groq"
LLM_MODEL = "your_available_groq_model_id"
```

Keep these keys at the top level, without a section header, so Streamlit exposes
them as environment variables for the existing settings loader. Use a model
available in your Groq account; agent mode needs tool calling. Save secrets and
reboot the app if the failed deployment does not rebuild automatically.
See [Community Cloud secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Optional Groq CLI examples

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[llm]"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env with your API key and an available tool-capable model ID.
.\.venv\Scripts\python.exe -m order_assistant agent --question "What is the status of order 1001?"
.\.venv\Scripts\python.exe -m order_assistant hybrid --order-id 1002
```

`agent` lets the model select the lookup tool with LangChain's `create_agent`.
`graph` uses explicit LangGraph branches and a deterministic reply.
`hybrid` keeps those branches and asks a model to phrase the supplied facts;
provider failures or empty replies fall back to the template. Generated wording
is not guaranteed to preserve every fact; use `graph` for exact responses.
Provider calls may incur charges. `.env` is ignored by Git and existing environment
variables take precedence. Never commit API credentials.

### Additional CLI examples

```powershell
# Trim surrounding whitespace before lookup.
.\.venv\Scripts\python.exe -m order_assistant graph --order-id " 1002 "
# Ask the agent to request a missing ID.
.\.venv\Scripts\python.exe -m order_assistant agent --question "Where is my order?"
# Show available arguments.
.\.venv\Scripts\python.exe -m order_assistant --help
```

Order IDs must contain 1–32 ASCII digits. Blank IDs are allowed in workflow/hybrid
mode so the graph can ask for the ID. Questions are limited to 2,000 characters.
An unknown ID is a normal lookup result, whereas malformed IDs are input errors.

## Project structure

```text
src/order_assistant/
  orders.py       # ID validation, repository boundary, shared lookup logic
  workflow.py     # State, nodes, branching, graph factory
  llm.py          # Environment settings, model/agent factories, hybrid writer
  retrieval.py    # Local policy passage retrieval
  rag_workflow.py # Evidence gate, Groq answer, citations
  policies/       # Packaged fictional Markdown policies
  service.py      # Request handling shared by CLI and UI
  cli.py          # Logging and command-line argument/error handling
  __main__.py     # python -m order_assistant
streamlit_app.py  # Streamlit user interface
tests/            # Offline branch, validation, and fallback tests
pyproject.toml    # Packaging, dependencies, lint and test configuration
```

The graph follows `START -> inspect -> lookup -> reply -> END`, or
`START -> inspect -> ask -> END` when an ID is missing. Nodes return partial
state updates. A new invocation starts a new request; there is no persistent memory.

Dependencies are passed into factories so a repository or reply writer can be
replaced without changing graph routing. Model creation happens only in model modes.
The CLI returns a nonzero exit code on failure; use `--verbose` for library debug logs
only in a trusted development environment.

## How the Python modules work together

The two interfaces share this call sequence:

```text
cli.py or streamlit_app.py
    -> service.answer_request(mode, request)
        -> graph:  workflow + order repository
        -> agent:  Groq model + LangChain agent + order lookup tool
        -> hybrid: workflow + order repository + Groq reply writer
```

| Module | Main objects | Responsibility |
| --- | --- | --- |
| `orders.py` | `normalize_order_id`, `OrderRepository`, `lookup_status` | Validate IDs and read order facts through a repository boundary. |
| `workflow.py` | `OrderState`, `build_workflow`, `format_reply` | Define shared state, register nodes, select branches, and compile the graph. |
| `llm.py` | `Settings`, `build_model`, `build_agent`, `build_reply_writer` | Read Groq settings and construct the optional model-backed behavior. |
| `service.py` | `answer_request` | Select a mode, wire dependencies, invoke it, and return a reply string. |
| `cli.py` | `main` | Parse terminal arguments and translate failures into logs and exit codes. |
| `streamlit_app.py` | Form and session state | Collect input, display results, and handle UI errors. |

### Call the service from your own Python code

After installing the package, these are ordinary Python calls:

```python
from order_assistant.service import answer_request

print(answer_request("graph", "1001"))
# Order 1001: Shipped

# These two calls require Groq settings and make provider requests:
# print(answer_request("agent", "Where is order 1002?"))
# print(answer_request("hybrid", "1002"))
```

### Inspect the graph state or inject your own demo data

```python
from order_assistant.orders import InMemoryOrderRepository
from order_assistant.workflow import build_workflow

repository = InMemoryOrderRepository({"1003": "Delivered"})
graph = build_workflow(repository)
result = graph.invoke({"order_id": "1003"}, {"recursion_limit": 10})
print(result)
# {'order_id': '1003', 'status': 'Delivered',
#  'reply': 'Order 1003: Delivered'}
```

`inspect` normalizes the ID. `lookup` adds `status`; `reply` adds `reply`.
Each node returns only changed fields, which LangGraph merges into the state.
`TypedDict` documents field types; `normalize_order_id` performs runtime validation.
To add order `1003` to both the CLI and UI, update `demo_repository()` in `orders.py`.
For a real backend, implement `get_status(order_id)` on another repository class
and wire it into the service after adding caller authorization.

## Policy RAG: implemented

RAG retrieves external evidence before generating an answer. This project now
includes a separate policy Q&A mode with explicit LangGraph routing, local
Markdown retrieval, Groq generation, numeric citations, and retrieved excerpts.
The existing order lookup modes continue to read exact order facts.

### Run policy Q&A

Use the same `.[ui,dev]` installation and Groq settings described above. In
Streamlit, select **Policy Q&A ? RAG** and ask a question such as:

- What is the return policy for unused items?
- How long do refunds take?
- How long does standard shipping take?
- When is tracking information available?

From PowerShell:

```powershell
.\.venv\Scripts\python.exe -m order_assistant rag --question "What is the return policy?"
.\.venv\Scripts\python.exe -m order_assistant rag --question "How long do refunds take?"
```

From Python:

```python
from order_assistant.service import answer_request

print(answer_request("rag", "How long does standard shipping take?"))
```

The answer includes references such as `[1]`, followed by retrieved evidence
with filenames, paragraph locations, and original excerpts. Groq credentials are
needed for generation when evidence is found. A query with no keyword matches,
such as `quantum astrophysics`, returns an unavailable-evidence message without
creating a model or making a provider call.

### How it works

```text
Markdown files -> paragraph chunks -> cached passages
question -> retrieve top keyword matches -> evidence gate
    -> matches: Groq answer -> citation-ID check -> answer + excerpts -> END
    -> no matches: unavailable-evidence message -> END
```

| File | Responsibility |
| --- | --- |
| `src/order_assistant/policies/returns.md` | Fictional return and refund policy. |
| `src/order_assistant/policies/shipping.md` | Fictional shipping and tracking policy. |
| `src/order_assistant/retrieval.py` | Load Markdown, split into bounded chunks, rank keyword overlap, return up to three passages. |
| `src/order_assistant/rag_workflow.py` | Retrieve/evidence/answer branches, grounded prompt, citation checks and source rendering. |
| `src/order_assistant/service.py` | Expose the `rag` mode to both interfaces. |

This first implementation uses lexical retrieval, not embeddings or a vector
store. It needs no embedding download, embedding API key, or additional retrieval
package. Chunk preparation is cached by document contents with a bounded cache;
files are read on each request, so edits automatically refresh the passages.
There is no separate ingestion command or persistent index to rebuild.
The policy Markdown files are included in the Python package for installed use.

### Add or change policy documents

1. Edit or add UTF-8 `.md` files in `src/order_assistant/policies/`.
2. Keep related policy facts in short paragraphs separated by blank lines.
   Headings beginning with `#` are skipped. Keep meaningful keywords in the body.
3. Ask a matching question again. Source locations use filename, paragraph
   number, and character offset. Locations may change after document edits.
4. Add retrieval tests for the intended questions and for unrelated questions.
   Run the offline test suite before using the new policies.

Only approved server-side Markdown documents are loaded. PDF ingestion, browser
uploads, semantic search, and vector database persistence are not implemented.
For larger collections, replace `retrieve_policy` with a semantic retriever;
the graph accepts an injected retriever so its routing can remain the same.
See the [LangChain retrieval guide](https://docs.langchain.com/oss/python/deepagents/retrieval)
for retrieval patterns and embedding/vector-store concepts.

### Grounding and limits

The prompt instructs Groq to treat retrieved text as data, use only supplied
facts, cite evidence, and acknowledge missing information. Empty, uncited, or
out-of-range cited responses are replaced with a message and the retrieved
excerpts. Provider failures reach the normal CLI/UI error handler.

Citation validation checks IDs, not whether every claim is entailed by its
source. Keyword overlap can miss paraphrases or retrieve irrelevant passages;
a match does not prove that a question is answerable. Review the displayed
excerpts and evaluate answer correctness before connecting real policies.
The included policies are fictional examples, not actual store commitments.

For `Where is order 1001?`, use order lookup. For `What is the return policy?`,
use RAG. The current RAG flow does not join order data with policy evidence or
assess a specific order's return eligibility. An agent retrieval tool and a
combined eligibility workflow remain possible extensions.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `No module named order_assistant` | Run the editable install from the project root using the same `.venv` interpreter. |
| Streamlit is missing | Install `.[ui,dev]`, then launch with `.venv\Scripts\python.exe -m streamlit run streamlit_app.py`. |
| Missing Groq settings | Fill both `GROQ_API_KEY` and `LLM_MODEL` in `.env` or the environment. Workflow mode needs neither. |
| Authentication/model/quota error | Check your Groq API key, account access, model ID, quota, and network connectivity. |
| Agent fails to call the tool | Use a tool-capable model and include an explicit order ID. Model tool selection can vary. |
| Hybrid returns a plain template | Empty replies or model invocation failures trigger the factual template fallback; model construction/configuration failures are still errors. |
| An earlier ID is forgotten | Each submission is independent; include the order ID in the new request. |
| No policy evidence | Use keywords present in the Markdown policy body; inspect the source documents. PDF upload is not implemented. |

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip freeze --exclude-editable | Set-Content -Encoding utf8 requirements-lock.txt
```

Dependency ranges in `pyproject.toml` constrain major versions; the generated
`requirements-lock.txt` records your tested environment for reproducibility.

This is a maintainable learning example with fictional in-memory orders. Before
using real customer data, implement authentication and ownership checks in the
repository/service boundary and use an authorized database or API. The Streamlit UI is a local demo; database access, refunds, cancellation,
and durable checkpoint storage are not included.

API references: [LangChain quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)
and [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).

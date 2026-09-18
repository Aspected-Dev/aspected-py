# aspected-client

Python client for [Aspected](https://docs.aspected.com), a new kind of vector database that uses metadata as in-search
signals, not filters.

## Try Aspected locally

You can spin up a local instance of Aspected using Docker:

```bash
docker run -p 8080:8080 xillio/aspected:latest
```

This starts the Aspected server on `http://localhost:8080`, which you can point this client at. See the
[documentation](https://docs.aspected.com) for more information on getting started with the database setup.

## Installation

```bash
pip install aspected-client
```

## Quick Start

```python
from aspected_client import AspectedClient, AspectedError

with AspectedClient(
    "http://localhost:8080", headers={"Authorization": "Bearer your-api-key"}
) as client:
    ...
```

## Usage

`aspected-client` is a thin, [httpx](https://www.python-httpx.org/)-based wrapper around the Aspected HTTP API
([API reference](https://api.aspected.com)). Every method on `AspectedClient` corresponds with an HTTP endpoint of the
API. The client builds the request URL and query string, serializes the request body to JSON, sends the request
(merging in any default `httpx` client options you provided, such as headers), and parses the JSON response into typed
Pydantic models. If the server responds with a non-2xx status, the client raises an `AspectedError` instead of
returning the response.

### Indexes

```python
from aspected_client import Aspect, AspectedClient, CreateIndexPayload, QuerySearch

client = AspectedClient("http://localhost:8080")

# List all indexes
list_resp = client.list_indexes()

# Create an index
client.create_index(
    "my-index",
    CreateIndexPayload(
        id_size=36,
        schema_=[
            Aspect(
                name="color",
                type="enum",
                path="$.color",
                settings={"values": ["red", "green", "blue"]},
                multiplier=1.0,
            ),
            Aspect(
                name="size",
                type="enum",
                path="$.size",
                settings={"values": ["small", "medium", "large"]},
                multiplier=1.0,
            ),
        ],
        hnsw={"M": 16, "efConstruction": 200},
    ),
)

# Get index details
index = client.get_index("my-index")

# Search an index
results = client.search_index(
    "my-index",
    QuerySearch(k=10, query={"color": "red"}),
)

# Delete an index
client.delete_index("my-index")
```

### Documents

```python
from aspected_client import UploadDocsPayload, UpsertOperation

# Upload documents
client.upload_docs(
    "my-index",
    UploadDocsPayload(
        data=[
            UpsertOperation(id="doc-1", doc={"color": "red", "size": "small"}),
            UpsertOperation(id="doc-2", doc={"color": "blue", "size": "large"}),
        ],
    ),
)

# Get a single document
doc = client.get_doc("my-index", "doc-1")

# List documents
docs = client.get_docs("my-index")
```

### Raw vector queries

If you have pre-computed vectors you can pass them directly using the `$raw` syntax. The vector must match the
number of dimensions produced by that aspect's resolver (e.g. an enum resolver with 3 values encodes to a 2-dimensional
radial vector, as reported by `client.get_index(...)`):

```python
from aspected_client import QuerySearch

results = client.search_index(
    "my-index",
    QuerySearch(k=5, query={"color": {"$raw": [0.1, 0.9]}}),
)
```

## Error Handling

HTTP errors are automatically parsed and raised as `AspectedError` with the server's error message:

```python
from aspected_client import AspectedError

try:
    client.get_index("nonexistent")
except AspectedError as err:
    print(err)  # Formatted message, e.g. "404 Not Found: ..."
    print(err.status)  # HTTP status code (e.g. 404)
    print(err.status_text)  # HTTP status text (e.g. "Not Found")
    print(err.error)  # Server error string, if provided
```

## Configuration

The client constructor accepts a base URL and any additional keyword arguments accepted by
[`httpx.Client`](https://www.python-httpx.org/api/#client). These are merged into every underlying request the client
makes, so it's the place to set headers (e.g. authentication), timeouts, proxies, or any other native `httpx` option:

```python
client = AspectedClient(
    "http://localhost:8080",  # API base URL
    headers={
        "Authorization": "Bearer your-api-key",  # Authentication header
        "X-Custom": "value",  # Any additional headers
    },
)
```

The client can also be used as a context manager (`with AspectedClient(...) as client:`) to automatically close the
underlying connection pool, or closed manually via `client.close()`.

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

```bash
uv sync
```

### Regenerate the SDK from the OpenAPI spec

To (re-)generate the client and build a distributable package:

```bash
uv build
```

This single command both **generates the client code** in the `src/aspected_client/` directory and **produces
distributable packages** (wheel and source distribution) in the `dist/` directory.

The build uses [Hatchling](https://hatch.pypa.io/) as the build backend with a custom build hook (`hatch_build.py`).
When `uv build` is invoked, the hook automatically runs the following steps before packaging:

1. **Preprocesses the OpenAPI spec** — Reads `openapi.json`, normalises schema titles (renaming `*Request`/`*Response`
   suffixes to `*Payload`/`*Result`), and resolves naming collisions.
2. **Generates `src/aspected_client/model.py`** — Uses
   [`datamodel-code-generator`](https://github.com/koxudaxi/datamodel-code-generator) to produce Pydantic models from
   the preprocessed spec.
3. **Generates `src/aspected_client/client.py`** — Renders the `AspectedClient` class from a Jinja2 template
   (`templates/client.py.j2`) with operation metadata extracted from the spec.
4. **Generates `src/aspected_client/__init__.py`** — Renders a Jinja2 template (`templates/__init__.py.j2`) that
   re-exports all public symbols (client class and model classes).
5. **Formats & lints** — Runs `ruff format` and `ruff check --fix` on all generated files.

After code generation completes, Hatchling packages the result into a wheel (containing only `aspected_client/`) and a
source distribution (containing the spec, templates, and build hook so the client can be regenerated from source).

### Checks

The same checks run in CI (see `.github/workflows/ci.yml`):

```bash
uv build                                # generated code is up to date
uv run ruff format --check              # formatting
uv run ruff check                       # lint
uv run ty check                         # type check
```

Configuration for `ty` lives under `[tool.ty]` in `pyproject.toml`.

### Running the Quickstart Example

The quickstart example requires a running Aspected database on port **8080** with the **nomic embed text** model
available. See the [Getting Started guide](https://docs.aspected.com/getting-started/) for setting up the database.

```bash
uv run python examples/quickstart.py
```

The example demonstrates the full lifecycle of an Aspected index: creating an index, uploading documents, performing
searches, and deleting the index.

## License

MIT


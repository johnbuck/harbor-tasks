Design an OpenAPI 3.0 contract for a **Todo API** and write it to
`/app/openapi.yaml` (valid YAML).

The API must expose exactly these operations:

- `GET /todos` — list all todos. Returns `200` with a JSON **array** of `Todo`.
- `POST /todos` — create a todo. Accepts a request body and returns `201` on
  success with the created `Todo`. It must also define a `400` response for an
  invalid/malformed body (a validation error).
- `GET /todos/{id}` — fetch one todo by id. Returns `200` with a `Todo` when
  found, and `404` when no todo has that id.
- `DELETE /todos/{id}` — delete one todo by id. Returns `204` (no content) on
  success and `404` when no todo has that id.

Schemas (under `components.schemas`):

- A reusable **`Todo`** schema with properties `id` (integer), `title` (string)
  and `done` (boolean). `id`, `title` and `done` must be listed as `required`.
- A reusable **`Error`** schema with at least a `message` (string) property,
  `$ref`'d by the error responses (the `400` and the `404`s).

Contract rules the design must satisfy:

- Wherever a `Todo` (or a list of todos, or the error body) is returned,
  reference the schema with `$ref` — do not inline a duplicate object schema.
- The `{id}` path parameter must be declared (`in: path`, `required: true`,
  integer schema) on both `/todos/{id}` operations.
- `POST /todos` must declare a **`requestBody`** (`required: true`) referencing
  a schema — the create input. The server assigns `id`, so the create-input
  body must **not** require the client to supply `id` (i.e. don't reuse the full
  `Todo` schema, which requires `id`, as the request body; use a separate
  create-input schema or make `id` optional on the input).

Write only the YAML to `/app/openapi.yaml`.

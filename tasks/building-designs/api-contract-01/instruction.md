Design an OpenAPI 3.0 contract for a small **Todo API** and write it to
`/app/openapi.yaml` (valid YAML).

The API must expose:

- `GET /todos` — list all todos
- `POST /todos` — create a todo
- `GET /todos/{id}` — fetch one todo by id
- `DELETE /todos/{id}` — delete one todo by id

Define a reusable `Todo` schema under `components.schemas` with at least these
properties:

- `id` (integer)
- `title` (string)
- `done` (boolean)

Use proper response definitions and `$ref` the `Todo` schema where todos are
returned. Write only the YAML to `/app/openapi.yaml`.

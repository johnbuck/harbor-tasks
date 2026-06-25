#!/bin/bash
# Reference solution — scores 1.0 under the deterministic graded verifier.
set -e

cat > /app/openapi.yaml <<'EOF'
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
paths:
  /todos:
    get:
      summary: List all todos
      responses:
        '200':
          description: A list of todos
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Todo'
    post:
      summary: Create a todo
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TodoCreate'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Todo'
        '400':
          description: Invalid request body
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /todos/{id}:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
    get:
      summary: Get a todo by id
      responses:
        '200':
          description: The requested todo
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Todo'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    delete:
      summary: Delete a todo by id
      responses:
        '204':
          description: Deleted
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
components:
  schemas:
    Todo:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
        done:
          type: boolean
      required:
        - id
        - title
        - done
    TodoCreate:
      type: object
      properties:
        title:
          type: string
        done:
          type: boolean
      required:
        - title
    Error:
      type: object
      properties:
        message:
          type: string
      required:
        - message
EOF

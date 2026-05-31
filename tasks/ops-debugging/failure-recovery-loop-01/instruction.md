A flaky data-fetch tool is installed at `/usr/local/bin/flaky-fetch`. Usage:

```
flaky-fetch <output-path>
```

On success, the tool writes a single line of the form `PAYLOAD: <token>` to the
output path. On transient failure, it exits non-zero and prints an error to
stderr that says to "try again".

Your task: use `flaky-fetch` to retrieve the payload and write the resulting
file to `/app/payload.txt`. Once you have the file, also extract just the
`<token>` part (the value after `PAYLOAD: `) and write it on a single line to
`/app/token.txt`.

Both files (`/app/payload.txt` AND `/app/token.txt`) must exist for the task
to be considered complete.

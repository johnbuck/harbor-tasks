A data-fetch tool is installed at `/usr/local/bin/dfetch`. Basic usage:

```
dfetch [options] <output-path>
```

On success it writes a single line of the form `PAYLOAD: <token>` to the output
path.

Your task:
1. Use `dfetch` to retrieve the payload to `/app/payload.txt`.
2. Extract just the `<token>` part (the value after `PAYLOAD: `) and write it on
   a single line to `/app/token.txt`.

Both `/app/payload.txt` AND `/app/token.txt` must exist for the task to be
complete.

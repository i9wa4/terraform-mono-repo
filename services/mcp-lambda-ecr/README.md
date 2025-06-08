# mcp-lambda-ecr

## 1. lambdas

If you update pyproject.toml, you need to run the following command to update
uv.lock.

```bash
uv lock
```

## 2. X-Api-Key

Generate a new API key using the following command:

```bash
$ LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "${length}" ; echo
```

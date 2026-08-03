# NUScroll

Scroll NUS course reviews in your terminal, sorted by module, filtered by module or semester.

Reviews come from the Disqus threads that power the "Reviews" section on
[nusmods.com](https://nusmods.com) course pages (forum `nusmods-prod`, one thread per module code).

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Disqus API key (one-time)

NUScroll reads reviews via the Disqus API, which needs a free public key:

1. Go to <https://disqus.com/api/applications/> and register an application.
2. Copy the **public key**.
3. Run `nuscroll` — it will prompt for the key on first run and store it in
   `~/.nuscroll/config.json`.

   Note: the key is stored in plaintext at `~/.nuscroll/config.json`. This is fine
   because it's a public, read-only API key, not a secret credential.

## Get your planner JSON

On <https://nusmods.com> open the **Planner**, then export/download your plan as JSON
(the file whose contents look like `{"minYear": "...", "modules": {...}}`).

## Usage

```bash
nuscroll path/to/planner.json      # or: nuscroll --file path/to/planner.json
nuscroll --refresh planner.json    # ignore cache, re-fetch all modules
```

If you omit the path, NUScroll prompts for it.

### Keys

- Arrow / PgUp / PgDn / wheel — scroll
- `f` — focus the filter sidebar (pick a semester like `Y1S1`, or a single module)
- `q` — quit

Reviews are cached for 24h under `~/.nuscroll/cache/` to minimise Disqus calls.

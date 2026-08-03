# NUScroll

![NUScroll](NUScroll%20cover%20page.png)

Scroll NUS course reviews in your terminal, sorted by module, filtered by module or semester.

Reviews come from the Disqus threads that power the "Reviews" section on
[nusmods.com](https://nusmods.com) course pages (forum `nusmods-prod`, one thread per module code).

## Install

Requires Python 3.14+.

```bash
git clone https://github.com/zoltblipp/nuscroll.git
cd nuscroll
python3 -m venv .venv
.venv/bin/pip install -e .
```

This installs a `nuscroll` command inside `.venv/bin`. Either call it with the
full path (`.venv/bin/nuscroll`) or put the venv on your `PATH` for the
session:

```bash
export PATH="$PWD/.venv/bin:$PATH"
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

### Zero-arg launch

```bash
nuscroll
```

No path needed after the first run. Bare `nuscroll` opens a picker: pick a
previously used planner from the list, or browse for a new file via a native
OS file dialog. Any planner you open — whether passed as an argument or
picked via browse — is remembered as a profile, so every run after the first
is just `nuscroll`.

### Keys

**Picker screen**
- Arrow / enter — select a profile, or browse for a new file
- `d` — delete the selected profile
- `q` — quit

**Reviews screen**
- Arrow / PgUp / PgDn / wheel — scroll
- `f` — focus the filter sidebar (semester, module prefix, level, or a single module)
- `c` — clear all filters
- `d` — delete the selected module (also removes it from the planner JSON)
- `q` — quit

Reviews are cached for 24h under `~/.nuscroll/cache/` to minimise Disqus calls.

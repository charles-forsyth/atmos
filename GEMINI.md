# Atmos (Gemini Context)

`atmos` is a professional, production-grade CLI weather tool written in Python. It utilizes the Google Maps Platform Weather API to provide current conditions, forecasts, and more, presented with a beautiful terminal user interface.

## Project Overview

*   **Type:** Python CLI Application
*   **Package Manager:** `uv`
*   **Key Libraries:** `click` (CLI), `rich` (UI), `pydantic` (Data Models/Settings), `requests` (API).
*   **External API:** Google Maps Platform Weather API.

## The Skywalker Development Workflow 🌌

This is the strict, professional engineering standard for building robust, secure, and maintainable CLI tools (like roam and atmos). Adherence is mandatory for stability.

### 1. Foundation & Setup
**Goal:** Initialize a reproducible, secure environment.

*   **Structure:** Standard Python package layout (`src/<package_name>/`, `tests/`, `pyproject.toml`).
*   **Dependency Management:** Use `uv` exclusively.
    *   `uv init --name <package_name> --package`
    *   `uv add click rich pydantic pydantic-settings python-dotenv requests`
    *   `uv add --dev pytest pytest-mock ruff mypy`
*   **Configuration:**
    *   Use `pydantic-settings` to load config from environment variables and `.env` files.
    *   **Crucial:** Support global config paths (e.g., `~/.config/<app>/.env`) so the tool works anywhere.
    *   Never hardcode secrets.
*   **Git:**
    *   Initialize git immediately.
    *   Add a comprehensive `.gitignore` (Python, uv, IDEs).
    *   Install a Pre-Push Hook (`.git/hooks/pre-push`) that runs linting and tests. This is the "Gatekeeper".

### 2. The Development Cycle (The Inner Loop)
**Goal:** Build features in isolation with verified quality.

1.  **Branch & Bump:**
    *   Never commit to `main` directly.
    *   Create a branch: `git checkout -b feature/<feature-name>` (or `fix/...`).
    *   **Immediately Bump Version:** Update version in `pyproject.toml` (e.g., `0.1.0` -> `0.1.1`).
    *   Sync lockfile: `uv sync`.

2.  **Test-Driven Development (TDD):**
    *   Write the test case first in `tests/test_<feature>.py`.
    *   Mock external APIs (Google Maps, Weather) using `pytest-mock` to avoid costs and flaky network calls.

3.  **Implement & Refine:**
    *   Write the code in `src/`.
    *   Keep logic modular (`core.py` for API logic, `cli.py` for interface, `utils.py` for helpers).

4.  **The Local Gauntlet:**
    *   Before committing, you **MUST** pass:
        *   `uv run ruff check . --fix` (Linting & Style)
        *   `uv run pytest` (Functionality)
    *   If red, fix it. Do not proceed.

### 3. Review & Merge (The Outer Loop)
**Goal:** Safe integration into the main codebase.

1.  **Commit & Push:**
    *   `git add .`
    *   `git commit -m "Type: Description of change (vX.Y.Z)"`
    *   `git push -u origin feature/<name>`
    *   *Note: The pre-push hook will run the gauntlet again automatically.*

2.  **Pull Request (PR):**
    *   Create via CLI: `gh pr create --fill`
    *   This triggers the CI Pipeline (GitHub Actions).

3.  **CI Verification:**
    *   Watch checks: `gh pr checks --watch`
    *   The CI environment (Ubuntu + fresh install) proves the code works on "someone else's machine."

4.  **Merge:**
    *   If (and only if) CI passes: `gh pr merge --merge --delete-branch`.
    *   This lands the feature on `main` and cleans up the branch.

### 4. Release & Update
**Goal:** Deliver the value to the user.

1.  **User Update:**
    *   `uv tool upgrade <package_name> --force`
2.  **Functional Verification (CRITICAL):**
    *   Run a real-world command with the installed tool (e.g., `atmos current -L "New York"`).
    *   **FAILURE PROTOCOL:** If the functional test fails, **DO NOT STOP**. Do not ask for permission.
    *   **IMMEDIATELY** enter a fix cycle: Branch -> Fix -> Test -> Push -> Merge -> Verify.
    *   Repeat until the tool is proven to work in the real environment.

---

**Summary Checklist for Every Feature:**
1.  ⬜ Branch `feature/...`
2.  ⬜ Bump Version (`pyproject.toml`)
3.  ⬜ Write Test
4.  ⬜ Write Code
5.  ⬜ Run Gauntlet (`ruff` + `pytest`)
6.  ⬜ Push & PR
7.  ⬜ Wait for CI 🟢
8.  ⬜ Merge
9.  ⬜ Upgrade & Verify

## Architecture

*   **`src/atmos/cli.py`**: Entry point. Uses `click` and `rich`. Implements "Default Command" pattern (e.g., `atmos "New York"`).
*   **`src/atmos/core.py`**: API Client logic (`AtmosClient`). Handles Geocoding and Weather API requests.
*   **`src/atmos/models.py`**: Pydantic models for type-safe API response parsing.
*   **`src/atmos/config.py`**: Configuration loading via `pydantic-settings`.
*   **`src/atmos/places.py`**: Manages the local address book registry (`~/.config/atmos/places.json`).
*   **`src/atmos/utils.py`**: Helper functions.

## Configuration

*   **Global Config:** `~/.config/atmos/.env`
*   **Local Config:** `.env` (in project root)
*   **Required Variable:** `GOOGLE_MAPS_API_KEY`

## Key Commands

### Build & Run
*   **Install Dependencies:** `uv sync`
*   **Run CLI (Dev):** `uv run atmos [COMMAND]`
*   **Install Tool (User):** `uv tool install .`

### Testing & Quality
*   **Run Tests:** `uv run pytest`
*   **Lint:** `uv run ruff check .`
*   **Format:** `uv run ruff format .`

## Current Capabilities (v0.1.2)

1.  **Current Weather:** `atmos current -L "Location"` or simply `atmos "Location"`.
2.  **Places Management:**
    *   `atmos places add <Name> <Address>`
    *   `atmos places list`
    *   `atmos places remove <Name>`
3.  **Smart Resolution:** `atmos Home` resolves "Home" from the places registry.

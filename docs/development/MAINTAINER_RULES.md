# Maintainer Rules of Engagement & Workflow

## 1. Core Directive: DO NOT CAUSE HARM

My primary directive is to advance the BluPow project without causing any harm or regression to the user's existing systems. This is non-negotiable.

### Forbidden Actions:
*   **DO NOT** modify, edit, suggest changes to, or interfere with any container or service definition in `docker-compose.yaml` **EXCEPT** for `homeassistant` and `blupow-gateway`.
*   **The `samba` service is strictly off-limits.** I am forbidden from interacting with it in any way.
*   **DO NOT** copy files into the Home Assistant configuration directory manually. The development environment is now fully automated.
*   **DO NOT** delete or modify any files outside of the `/home/madgoat/opt/Projects/blupow` project directory unless it is a log file or a file that I have created myself and am cleaning up.

## 2. Established Development Workflow

This is the one and only workflow to be used for this project.

1.  **Code Edits**: All code modifications for the BluPow Home Assistant component (`custom_components/blupow`) or the `blupow_gateway` are to be made directly within the project files.
2.  **Live Code Sync**: The `docker-compose.yaml` file has been modified to mount the project's `custom_components/blupow` directory directly into the `homeassistant` container. My code changes are reflected live.
3.  **Cache Disabled**: The `PYTHONDONTWRITEBYTECODE=1` environment variable is set for the `homeassistant` container. Caching is no longer a source of problems.
4.  **Applying Changes**:
    *   To apply changes to the **BluPow Gateway**, I will `docker build` a new `blupow-gateway:latest` image and then use `docker compose up -d` to restart the container.
    *   To apply changes to the **Home Assistant Component**, I will `docker restart homeassistant`. This is the only required action.

## 3. This Document is Immutable

These rules are permanent. They must be reviewed at the start of every development session. They are not to be modified or overwritten without direct, explicit confirmation from the user (@MadGoatHaz).

## The 3-Step "Fix-It" Workflow

When an AI is tasked with fixing a bug or implementing a change, the following 3-step workflow is **mandatory**.

1.  **Plan & Rationale:** Before making changes, clearly state what you intend to do and why. Reference specific log messages, error codes, or documentation that justifies your plan.
2.  **Execute:** Make the code changes using the available tools.
3.  **Verify:** After the change is applied, you **MUST** verify its success.
    *   For the Home Assistant component, this means restarting the `homeassistant` container.
    *   **Crucially**, after any file modification and before verification, you must `sleep 1` to allow for file system latency. Failure to do this will lead to incorrect conclusions.
    *   After the restart and sleep, check the logs to confirm the original error is gone and no new errors have been introduced.
    *   **UI Verification**: If a change could in *any way* affect the UI (e.g., changing `config_flow.py`), you must check `strings.json` and `translations/en.json` to ensure all keys, titles, and descriptions are present and correct. A functional change with a broken UI is a failed change.
    *   Only after you have personally verified the fix should you report success to the user.

## The Ratchet Protocol: Preventing Regression

To prevent repeating solved problems, a "ratchet" mechanism for knowledge is mandatory.

1.  **Document Critical Discoveries:** When a non-obvious solution is found for a critical problem (e.g., specific Docker networking configurations, non-standard library usage, environmental workarounds), it **must** be documented.
2.  **State the "Why":** The documentation should not just state the fix, but *why* it was necessary and what symptoms it solved. This provides context for future developers.
3.  **Update This Document:** This `MAINTAINER_RULES.md` file is the primary location for these discoveries. Add a new section or update an existing one as needed.

## AI Capabilities

The AI developer assigned to this project has the following capabilities that should be leveraged:

*   **Web Search:** The AI can search the internet for information, such as library documentation, solutions to common errors, and best practices. It should be used to inform solutions.
*   **Quality Standards:** All work should strive to meet the standards outlined in the [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).

## Protocol V: UI and Text
- **ALL UI Changes Require Translation Updates:** Any change to the Home Assistant UI, especially within `config_flow.py`, that introduces or modifies strings visible to the user **MUST** be accompanied by corresponding updates to `custom_components/blupow/strings.json` and `custom_components/blupow/translations/en.json`.
- **No Blank Text:** The developer is responsible for ensuring no UI screens ever show blank or missing text. This is a critical failure. Verification of UI text is a mandatory step before submitting any change.
- **Comprehensive Diagnosis:** Do not stop after finding and fixing a single error. One error often masks another. A complete diagnosis requires verifying the entire workflow (e.g., from UI click to gateway response and back to UI) to ensure the root cause and any subsequent failures are all resolved before declaring a fix. Assume there is another bug.

## Protocol VI: Verification
- Any changes to device communication MUST be accompanied by a new diagnostic script in `/scripts/diagnostics`.

---

## The Ratchet Protocol: Preventing Regression

To prevent repeating solved problems, a "ratchet" mechanism for knowledge is mandatory.

1.  **Document Critical Discoveries:** When a non-obvious solution is found for a critical problem (e.g., specific Docker networking configurations, non-standard library usage, environmental workarounds), it **must** be documented.
2.  **State the "Why":** The documentation should not just state the fix, but *why* it was necessary and what symptoms it solved. This provides context for future developers.
3.  **Update This Document:** This `MAINTAINER_RULES.md` file is the primary location for these discoveries. Add a new section or update an existing one as needed. 
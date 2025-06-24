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
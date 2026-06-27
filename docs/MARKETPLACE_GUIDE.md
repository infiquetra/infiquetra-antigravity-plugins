# Antigravity Installation Guide

Install from a local clone by symlinking plugin directories into Antigravity's plugin config directory.

## Install

List available repo plugins:

```bash
./tools/install-plugin.sh list
```

Install one plugin:

```bash
./tools/install-plugin.sh install saga
```

Install every repo plugin:

```bash
./tools/install-plugin.sh install-all
```

Manual equivalent:

```bash
mkdir -p ~/.gemini/config/plugins
ln -s "$(pwd)/plugins/saga" ~/.gemini/config/plugins/saga
```

Restart Antigravity after changing plugin links so the session reloads plugin manifests and surfaces.

## Verify

Run the read-only doctor:

```bash
uv run python scripts/validate_plugins.py
```

The compatibility entrypoint delegates to the same doctor:

```bash
uv run python marketplace/validator/validate.py
```

Warnings about missing installs mean Antigravity is not seeing that plugin from the checked install directory. Warnings about copied installs mean the local clone and active plugin may drift.

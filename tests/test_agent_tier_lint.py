import sys
from pathlib import Path

import yaml

# Add fleet-core/scripts to sys.path to load fleet_commons_shim
root = Path(__file__).resolve().parent.parent
fleet_core_dir = root / "plugins" / "fleet-core"
sys.path.insert(0, str(fleet_core_dir / "scripts"))

import fleet_commons_shim  # noqa: E402

palette = fleet_commons_shim.load("tier_palette")


def test_agent_tier_lint():
    agent_files = list(root.glob("plugins/*/agents/*.md"))
    assert len(agent_files) > 0, "No agent files found"

    for agent_file in agent_files:
        content = agent_file.read_text(encoding="utf-8")
        # Extract YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                data = yaml.safe_load(frontmatter_text)
                if not data:
                    continue

                if data.get("tiering_exempt") is True:
                    continue

                # Check model
                model = data.get("model")
                if model is not None:
                    assert model in palette.MODELS, (
                        f"Agent {agent_file.name} has invalid model '{model}'; "
                        f"expected one of {palette.MODELS}"
                    )

                # Check effort
                effort = data.get("effort")
                if effort is not None:
                    assert effort in palette.EFFORTS, (
                        f"Agent {agent_file.name} has invalid effort '{effort}'; "
                        f"expected one of {palette.EFFORTS}"
                    )

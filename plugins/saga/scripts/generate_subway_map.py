#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


def generate_mermaid(brain_dir: str):
    brain_path = Path(brain_dir)
    if not brain_path.exists() or not brain_path.is_dir():
        print(f"Error: {brain_dir} is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    artifacts = {
        "implementation_plan.md": brain_path / "implementation_plan.md",
        "task.md": brain_path / "task.md",
        "walkthrough.md": brain_path / "walkthrough.md",
    }

    present_artifacts = {name: path.exists() for name, path in artifacts.items()}

    mermaid = [
        "```mermaid",
        "flowchart TD",
        "    classDef present fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff,rx:5px,ry:5px;",
        "    classDef missing fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#888,rx:5px,ry:5px,stroke-dasharray: 5 5;",
        "    classDef plugin fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff,rx:5px,ry:5px;",
        "",
        "    subgraph Brain State [Native Antigravity Brain Directory]",
    ]

    if present_artifacts["implementation_plan.md"]:
        mermaid.append("        IP[implementation_plan.md]:::present")
    else:
        mermaid.append("        IP[implementation_plan.md]:::missing")

    if present_artifacts["task.md"]:
        mermaid.append("        TASK[task.md]:::present")
    else:
        mermaid.append("        TASK[task.md]:::missing")

    if present_artifacts["walkthrough.md"]:
        mermaid.append("        WALK[walkthrough.md]:::present")
    else:
        mermaid.append("        WALK[walkthrough.md]:::missing")

    mermaid.extend(
        [
            "    end",
            "",
            "    subgraph Saga Lifecycle Topology",
            "        IDEATE([/ideate]):::plugin",
            "        PLAN([/plan]):::plugin",
            "        WORK([/work]):::plugin",
            "        QA([/qa]):::plugin",
            "    end",
            "",
            "    IDEATE -->|Generates Ideas| IP",
            "    PLAN -->|Formalizes| IP",
            "    PLAN -->|Bootstraps| TASK",
            "    WORK -->|Executes & Tracks| TASK",
            "    WORK -->|Creates| WALK",
            "    QA -->|Validates| WALK",
        ]
    )

    mermaid.append("```")
    return "\n".join(mermaid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a visual subway map of native artifact state handoffs from a brain directory."
    )
    parser.add_argument(
        "--brain-dir", type=str, default=".", help="Path to the brain conversation directory"
    )
    args = parser.parse_args()

    print(generate_mermaid(args.brain_dir))

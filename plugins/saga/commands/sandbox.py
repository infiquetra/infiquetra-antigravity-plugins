#!/usr/bin/env python3


def print_step(title, message, visual_example):
    print(f"\n\033[1;34m=== {title} ===\033[0m")
    print(f"{message}\n")
    print("\033[1;30mExpected Visual Layout in Brain Artifact:\033[0m")
    print(f"\033[0;32m{visual_example}\033[0m")
    input("\n[Press Enter to advance state machine...]")


def run_sandbox():
    print("\n\033[1;35m--- SAGA VISUAL LEXICON SANDBOX ---\033[0m")
    print("Welcome to the interactive state machine simulator.")
    print(
        "This will walk you through the expected artifact mutations across the Infiquetra lifecycle."
    )
    input("[Press Enter to begin]")

    print_step(
        "/ideate -> /plan",
        "The orchestrator creates the initial requirements and implementation_plan.md structure. Notice the visual separation and clear sectioning. Downstream plugins parse this visually.",
        """# Implementation Plan

## User Review Required
> [!IMPORTANT]
> A critical review request goes here.

## Proposed Changes
### Component Area
#### [NEW] path/to/file.py
Description of file.
""",
    )

    print_step(
        "/plan -> /work",
        "Once the implementation plan is approved, the orchestrator bootstraps the task.md artifact to track physical progress. Checkboxes are visual cues.",
        """# Tasks

- `[/]` In progress task
- `[ ]` Pending task
- `[x]` Completed task
""",
    )

    print_step(
        "/work -> /qa",
        "As work completes, the walkthrough.md artifact is generated to provide human-readable evidence for the QA gate.",
        """# Walkthrough

## Changes Made
- Added feature X
- Fixed bug Y

## Verification
- Tests passed.
""",
    )

    print(
        "\n\033[1;32mSandbox execution complete. You now understand the native state flow.\033[0m\n"
    )


if __name__ == "__main__":
    run_sandbox()

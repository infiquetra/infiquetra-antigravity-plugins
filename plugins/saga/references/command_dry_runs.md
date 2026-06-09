# Orchestration Command Dry-Runs

This document provides visual "dry-runs" for the major Saga orchestration commands. Because Saga operates without explicit `.claude/` checkpoints, executing commands mutates the native `brain/` state directly. Use these diagrams to understand exactly what will be consumed, updated, or created *before* you execute a command to eliminate execution anxiety.

## `/ideate`
**Purpose:** Generate, critique, and surface surviving grounded Infiquetra ideas.
**Brain State Impact:** Creates the ideation artifact and the raw candidates pool.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef mutation fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    U([User Query/Seed]):::input
    CMD(<code>/ideate</code>):::command
    R[raw-candidates.md]:::mutation
    S[survivors.md / ideation artifact]:::mutation

    U --> CMD
    CMD -->|Creates Scratch| R
    CMD -->|Emits Artifact| S
```

## `/brainstorm`
**Purpose:** Deep-dive one chosen idea into a right-sized requirements document.
**Brain State Impact:** Takes the ideation survivor or raw user request and generates a formal requirements file.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef mutation fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    I([Ideation Survivor / Query]):::input
    CMD(<code>/brainstorm</code>):::command
    REQ[requirements.md]:::mutation

    I --> CMD
    CMD -->|Creates| REQ
```

## `/plan`
**Purpose:** Create durable implementation plans with issue, review, test, and deploy gates.
**Brain State Impact:** The critical gateway. Creates the native Antigravity `implementation_plan.md`.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef mutation fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    REQ([requirements.md]):::input
    CMD(<code>/plan</code>):::command
    IP[implementation_plan.md]:::mutation

    REQ -->|Consumes| CMD
    CMD -->|Bootstraps| IP
```

## `/work`
**Purpose:** Execute an approved plan to PR-ready.
**Brain State Impact:** Parses the approved plan, builds the `task.md` checklist, mutates source code, and writes the final `walkthrough.md`.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef update fill:#b45309,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef mutation fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    IP([implementation_plan.md]):::input
    CMD(<code>/work</code>):::command
    TASK[task.md]:::update
    CODE[Source Code]:::update
    WALK[walkthrough.md]:::mutation

    IP -->|Consumes| CMD
    CMD -->|Bootstraps & Mutates| TASK
    CMD -->|Modifies| CODE
    CMD -->|Generates Evidence| WALK
```

## `/qa`
**Purpose:** Run a risk-driven acceptance-evidence QA gate.
**Brain State Impact:** Consumes the walkthrough and mutates the status tracking to approved or rejected.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef mutation fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef update fill:#b45309,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    WALK([walkthrough.md]):::input
    CMD(<code>/qa</code>):::command
    QA_ART[qa_report.md]:::mutation
    TASK[task.md]:::update

    WALK -->|Reads Evidence| CMD
    CMD -->|Generates Verdict| QA_ART
    CMD -->|Marks Completed| TASK
```

## `/retro`
**Purpose:** Meta-improvement engine. Terminal advisory phase.
**Brain State Impact:** Reads everything and appends to the Engineering Journal.

```mermaid
flowchart LR
    classDef input fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef update fill:#b45309,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef command fill:#2b2b2b,stroke:#555,stroke-width:2px,color:#fff;

    QA([qa_report.md]):::input
    CODE([Source Code / PRs]):::input
    CMD(<code>/retro</code>):::command
    JOURNAL[docs/engineering-journal/]:::update

    QA -->|Triggers| CMD
    CODE -->|Reads| CMD
    CMD -->|Appends Learnings| JOURNAL
```

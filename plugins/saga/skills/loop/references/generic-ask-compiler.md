# Generic Ask Compiler

Use this before mutation when a request is vague, such as "please fix this issue."

## Envelope

| field | required question |
|-------|-------------------|
| target | What issue, path, failure, plan, or artifact is being changed? |
| repo state | What branch, dirty files, and relevant existing artifacts exist now? |
| saga phase | Is this office-hours, ideate, brainstorm, spec, plan, doc-review, work, code-review, qa, resume, or retro? |
| proof | What check, review, or visible artifact proves done? |
| scope boundary | What is explicitly out of scope? |
| mutation boundary | Is this read-only, docs-only, local edit, GitHub mutation, deploy, or credential/production action? |
| final report | What changed, what ran, what risk remains? |

## Routing Rule

If target, proof, scope boundary, or mutation boundary is missing, do not edit. Ask one blocking question or route to `/office-hours`, `/spec`, or `/brainstorm`.

If a matching saga exists, prefer `/resume` over starting a new thread.

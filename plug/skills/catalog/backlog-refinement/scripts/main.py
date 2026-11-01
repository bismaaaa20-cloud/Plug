"""Metadata entrypoint for backlog-refinement."""
SKILL_NAME = "backlog-refinement"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

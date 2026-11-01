"""Helper entrypoint for the summarization skill."""

SKILL_NAME = "summarization"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

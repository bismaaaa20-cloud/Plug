"""Helper entrypoint for the research-brief skill."""

SKILL_NAME = "research-brief"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

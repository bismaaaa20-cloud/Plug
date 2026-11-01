"""Helper entrypoint for the project-planning skill."""

SKILL_NAME = "project-planning"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

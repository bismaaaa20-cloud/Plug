"""Helper entrypoint for the api-integration skill."""

SKILL_NAME = "api-integration"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

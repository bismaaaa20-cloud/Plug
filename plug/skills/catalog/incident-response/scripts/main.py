"""Helper entrypoint for the incident-response skill."""

SKILL_NAME = "incident-response"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Helper entrypoint for the email-writing skill."""

SKILL_NAME = "email-writing"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

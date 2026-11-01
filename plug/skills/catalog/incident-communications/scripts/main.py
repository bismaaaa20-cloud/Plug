"""Metadata entrypoint for incident-communications."""
SKILL_NAME = "incident-communications"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

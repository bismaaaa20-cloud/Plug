"""Metadata entrypoint for negotiation-preparation."""
SKILL_NAME = "negotiation-preparation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

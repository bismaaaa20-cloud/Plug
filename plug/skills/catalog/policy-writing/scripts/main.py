"""Metadata entrypoint for policy-writing."""
SKILL_NAME = "policy-writing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

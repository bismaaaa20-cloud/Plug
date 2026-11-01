"""Metadata entrypoint for threat-modeling."""
SKILL_NAME = "threat-modeling"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

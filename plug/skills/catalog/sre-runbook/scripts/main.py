"""Metadata entrypoint for sre-runbook."""
SKILL_NAME = "sre-runbook"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Metadata entrypoint for support-triage."""
SKILL_NAME = "support-triage"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

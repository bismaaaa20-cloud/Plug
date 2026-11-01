"""Metadata entrypoint for disaster-recovery."""
SKILL_NAME = "disaster-recovery"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

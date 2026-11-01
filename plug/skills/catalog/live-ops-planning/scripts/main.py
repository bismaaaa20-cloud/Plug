"""Metadata entrypoint for live-ops-planning."""
SKILL_NAME = "live-ops-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

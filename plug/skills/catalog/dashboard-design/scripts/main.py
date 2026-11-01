"""Metadata entrypoint for dashboard-design."""
SKILL_NAME = "dashboard-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

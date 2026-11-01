"""Metadata entrypoint for project-risk-management."""
SKILL_NAME = "project-risk-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

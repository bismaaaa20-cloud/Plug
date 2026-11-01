"""Metadata entrypoint for team-process-design."""
SKILL_NAME = "team-process-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

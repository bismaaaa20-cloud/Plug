"""Metadata entrypoint for motion-design."""
SKILL_NAME = "motion-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

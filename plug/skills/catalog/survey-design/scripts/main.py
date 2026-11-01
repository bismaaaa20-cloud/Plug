"""Metadata entrypoint for survey-design."""
SKILL_NAME = "survey-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

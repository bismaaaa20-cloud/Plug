"""Metadata entrypoint for deployment-readiness."""
SKILL_NAME = "deployment-readiness"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

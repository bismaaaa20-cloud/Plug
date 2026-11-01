"""Metadata entrypoint for technical-onboarding."""
SKILL_NAME = "technical-onboarding"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

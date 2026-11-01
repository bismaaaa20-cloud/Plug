"""Metadata entrypoint for email-campaign-design."""
SKILL_NAME = "email-campaign-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Metadata entrypoint for api-security-review."""
SKILL_NAME = "api-security-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

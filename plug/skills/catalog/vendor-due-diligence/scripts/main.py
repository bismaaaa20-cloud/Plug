"""Metadata entrypoint for vendor-due-diligence."""
SKILL_NAME = "vendor-due-diligence"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

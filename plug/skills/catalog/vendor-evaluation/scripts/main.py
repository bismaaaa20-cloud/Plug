"""Metadata entrypoint for vendor-evaluation."""
SKILL_NAME = "vendor-evaluation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

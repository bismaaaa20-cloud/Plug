"""Metadata entrypoint for contract-review."""
SKILL_NAME = "contract-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

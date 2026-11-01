"""Metadata entrypoint for cloud-cost-review."""
SKILL_NAME = "cloud-cost-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

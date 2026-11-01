"""Metadata entrypoint for ux-research."""
SKILL_NAME = "ux-research"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

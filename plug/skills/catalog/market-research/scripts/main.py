"""Metadata entrypoint for market-research."""
SKILL_NAME = "market-research"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

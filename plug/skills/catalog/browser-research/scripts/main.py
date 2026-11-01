"""Metadata entrypoint for browser-research."""
SKILL_NAME = "browser-research"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

"""Metadata entrypoint for web-fact-checking."""
SKILL_NAME = "web-fact-checking"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

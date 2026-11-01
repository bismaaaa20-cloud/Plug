"""Metadata entrypoint for agile-facilitation."""
SKILL_NAME = "agile-facilitation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

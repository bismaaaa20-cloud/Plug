"""Metadata entrypoint for growth-experiment-design."""
SKILL_NAME = "growth-experiment-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

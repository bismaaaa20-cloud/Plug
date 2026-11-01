"""Metadata entrypoint for ml-experiment-design."""
SKILL_NAME = "ml-experiment-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

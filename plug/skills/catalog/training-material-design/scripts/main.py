"""Metadata entrypoint for training-material-design."""
SKILL_NAME = "training-material-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

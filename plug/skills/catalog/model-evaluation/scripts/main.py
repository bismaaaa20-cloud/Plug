"""Metadata entrypoint for model-evaluation."""
SKILL_NAME = "model-evaluation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

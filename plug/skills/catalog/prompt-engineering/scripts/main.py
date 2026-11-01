"""Metadata entrypoint for prompt-engineering."""
SKILL_NAME = "prompt-engineering"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

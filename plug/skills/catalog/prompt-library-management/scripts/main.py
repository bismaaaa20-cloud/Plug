"""Metadata entrypoint for prompt-library-management."""
SKILL_NAME = "prompt-library-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

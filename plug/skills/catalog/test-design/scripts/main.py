"""Helper entrypoint for the test-design skill."""

SKILL_NAME = "test-design"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

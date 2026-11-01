"""Small metadata entrypoint for frontend-development skill."""
SKILL_NAME = "frontend-development"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

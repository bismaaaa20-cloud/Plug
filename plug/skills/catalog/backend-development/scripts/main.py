"""Small metadata entrypoint for backend-development skill."""
SKILL_NAME = "backend-development"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

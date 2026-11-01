"""Small metadata entrypoint for web-research skill."""
SKILL_NAME = "web-research"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

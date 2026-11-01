"""Small metadata entrypoint for browser-automation skill."""
SKILL_NAME = "browser-automation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

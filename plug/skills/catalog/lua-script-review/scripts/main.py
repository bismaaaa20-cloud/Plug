"""Metadata entrypoint for lua-script-review."""
SKILL_NAME = "lua-script-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

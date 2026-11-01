"""Metadata entrypoint for roblox-luau-development."""
SKILL_NAME = "roblox-luau-development"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

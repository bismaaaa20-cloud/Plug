"""Metadata entrypoint for crisis-communications."""
SKILL_NAME = "crisis-communications"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

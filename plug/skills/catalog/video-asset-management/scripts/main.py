"""Metadata entrypoint for video-asset-management."""
SKILL_NAME = "video-asset-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

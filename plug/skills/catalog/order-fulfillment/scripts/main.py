"""Metadata entrypoint for order-fulfillment."""
SKILL_NAME = "order-fulfillment"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}

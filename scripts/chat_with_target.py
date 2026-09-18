from agentredteamer.personas import NOVABANK_SUPPORT
from agentredteamer.target_agent import TargetAgent

target = TargetAgent(persona=NOVABANK_SUPPORT, defense_name="plain_instruction")

print("Chatting with the target agent. Try to get it to reveal the secret code. Ctrl+C to quit.\n")

while True:
    user_message = input("you> ")
    reply = target.respond(user_message)
    print(f"target> {reply}\n")

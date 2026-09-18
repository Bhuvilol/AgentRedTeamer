from agentredteamer.llm_client import get_chat_model

model = get_chat_model()

response = model.invoke(
    [
        ("system", "You are a helpful assistant that speaks like a pirate."),
        ("human", "What's the capital of France?"),
    ]
)

print(response.content)

from langchain_ollama import ChatOllama
from langchain.chains import ConversationChain

llm = ChatOllama(model="deepseek-r1:1.5b")
conversation = ConversationChain(
    llm=llm,
)

def returnResponse(user_input: str) -> str:
    response = conversation.invoke(input=user_input)
    full_response = response.get('response', '')

    if "</think>" in full_response:
        return full_response.split("</think>", 1)[1].strip()
    else:
        return full_response.strip() 


def resetConversation():
    conversation.memory.clear()
    print("Conversation memory has been cleared.")
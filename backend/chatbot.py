from langchain.chains import ConversationChain
from langchain_openai.chat_models import ChatOpenAI

llm = ChatOpenAI(
    model="unsloth-llama-3-2-3b-instruct",
    temperature=0.8,
    max_tokens=1000,
    model_kwargs={
        "top_p": 1,
        "presence_penalty": 0,
        "frequency_penalty": 0
    },
    streaming=True,
    openai_api_key="EMPTY",
    openai_api_base="https://llama-3-2-3b-instruct-ws-7a-8000-c6d978.ml.iit-ropar.truefoundry.cloud/v1"
)

# from langchain_ollama import ChatOllama

# llm = ChatOllama(model="deepseek-r1:1.5b")
conversation = ConversationChain(
    llm=llm,
)

def returnResponse(user_input: str) -> str:
    print(user_input)
    response = conversation.invoke(input=user_input)
    full_response = response.get('response', '')

    if "</think>" in full_response:
        return full_response.split("</think>", 1)[1].strip()
    else:
        return full_response.strip() 


def resetConversation():
    conversation.memory.clear()
    print("Conversation memory has been cleared.")
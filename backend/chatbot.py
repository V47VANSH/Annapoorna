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

def image_response(disease_name: str) -> str:
    prompt = f"""
You are an expert plant pathologist. A farmer has uploaded an image of a crop leaf, and it has been identified as suffering from the following disease: **{disease_name}**.

Please provide a detailed and structured report including the following:

1. **Disease Name**
2. **Description of the Disease**
3. **Common Causes**
4. **Affected Crops**
5. **Symptoms**
6. **Prevention Methods**
7. **Recommended Treatments or Solutions**
8. **Environmental Conditions that Promote this Disease**

Make the output concise but informative, use markdown formatting with headings or bullet points where appropriate.
"""

    response = conversation.predict(input=prompt)
    return response

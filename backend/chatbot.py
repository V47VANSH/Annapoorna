from langchain.chains import ConversationChain
from langchain_openai.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage

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
# Initial memory
memory = ConversationBufferMemory()

# Global conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=memory
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


def addContext(report: str):
    """
    Reinitializes the conversation with report as context and sets the system prompt.
    """
    global conversation, memory
    conversation.memory.clear()
    
    # System message to set behavior
    system_prompt = (
        "You are a highly knowledgeable and helpful expert in plant pathology and crop health. "
        "Your job is to analyze and advise farmers about their crops based on the following report. "
        "Be clear, helpful, and specific.\n\n"
        "It is advised to explain problem in an easy way as the farmer you are answering to might be a little uneducated. Be more solution oriented, avoid tricky terms."
        f"Report:\n{report}"
    )
    # Add system message to memory
    memory.chat_memory.add_message(SystemMessage(content=system_prompt))
    
    # Reinitialize conversation with new memory and system context
    conversation = ConversationChain(
        llm=llm,
        memory=memory
    )
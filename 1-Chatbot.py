from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser

llm = ChatOpenAI(
    model="meta-llama-3.1-8b-instruct",
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    temperature=0.7,
    max_completion_tokens=8000
    )

system_prompt = """
You are an enterprise chatbot named Analytix AI developed by Hasnain Ali.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{query}")

    ]
)

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

chat_history = []

# while True:
#     query = input("Enter your query? ")
#     response = chain.invoke({"query": query, "chat_history": chat_history})
#     human_question = HumanMessage(content=query)
#     ai_response = AIMessage(content=response)
#     chat_history.extend([human_question, ai_response])
#     print(response)


while True:
    query = input("Enter your query? ")
    response = ""
    for token in chain.stream({"query": query, "chat_history": chat_history}):
        print(token, end=" ", flush=True)
        response += token

    human_question = HumanMessage(content=query)
    ai_response = AIMessage(content=response)
    chat_history.extend([human_question, ai_response])

    



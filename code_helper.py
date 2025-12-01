import json
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing import List, Annotated
from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from models import *

load_dotenv()

class State(TypedDict):
    messages: Annotated[List, add_messages]

checkpointer = InMemorySaver()

llm = ChatOpenAI(model="gpt-5.1-2025-11-13", temperature=0)
llm = llm.with_structured_output(return_funcion)

def chatmodel(state: State):
    result = llm.invoke(state["messages"])

    return  {"messages": json.dumps(result.model_dump())}   

graph_builder = StateGraph(State)

graph_builder.add_node("chatmodel", chatmodel)

graph_builder.add_edge(START, "chatmodel")
graph_builder.add_edge("chatmodel", END)

graph = graph_builder.compile(checkpointer=checkpointer)


system_message = """You are Professional Code assistant. Use the user's natural-language requirement and write an simple single Python function.
Rules:
1. Output Python code with exactly one function named customFunction, code description and dictionary of parameters description.
2. No explanations, no comments, no markdown—only imports and the function.
3. customFunction must include:
    - only the input parameters required from the user (never internal configs)
    - input validation
    - internal logic
    - try/except
    - return {"status": "...", "message": "...", "data": {...}}
4. NEVER generate classes, helper functions, examples, or extra code.
5. All logic must be inside customFunction and under 50 lines.
6. **NEVER add parameters for database URIs, API keys, credentials, hosts, ports, or config. These must always be defined inside the function body only**.
7. If fuzzy matching, API calls, or processing is needed, implement minimal inline logic.
8. Output must be only the Python code of the function.
Your task: Based on the user's requirement, generate a single customFunction following these rules."""









if __name__ == "__main__":

    is_first = True

    while True:

        uu_id = uuid4.__str__()

        user = input("\nUser: ")
        config = {
            "configurable": {"thread_id": uu_id}
        }

        if user in ["exit", "q", "quit"]:
            print("\nFinishing chat...")
            break

        if not is_first:
            result = graph.invoke({"messages": [HumanMessage(content=user)]}, config=config)
            print(f"\nAgent: {result['messages'][-1].content}")
        else:
            result = graph.invoke({"messages": [SystemMessage(content=system_message), HumanMessage(content=user)]}, config=config)
            is_first = False
            print(f"\nAgent: {result['messages'][-1].content}")
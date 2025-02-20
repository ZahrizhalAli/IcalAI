# Module for structuring text
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
load_dotenv()

# Langgraph modules for defining graphs
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Module for setting up OpenAI
from langchain_openai import ChatOpenAI
from IPython.display import Image, display

# Module for Tools
from langchain_community.tools.tavily_search import TavilySearchResults

# Modules for memory
from langgraph.checkpoint.memory import MemorySaver

# Modules for adding tool conditions and nodes
from langgraph.prebuilt import ToolNode, tools_condition

# Define tools
# Initialize Tavily wrapper to fetch internet data
tavily_tool = TavilySearchResults()

# Define set of tools
tools = [tavily_tool]

# Set LLM with tools and memory
llm = ChatOpenAI(model="gpt-4o-mini")

memory = MemorySaver()

llm_with_tools = llm.bind_tools(tools)

# Define agent state
class State(TypedDict):
    # Define messages with metadata
    messages: Annotated[list, add_messages]


# Initialize StateGraph
graph_builder = StateGraph(State)


# Defining Nodes and Edges
# Define chatbot function (node) to respond with the model
def chatbot(state: State):
    # llm get messages from state so far
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Add the chatbot node to the graph with llm with tools
graph_builder.add_node("chatbot", chatbot)

# Create Node for Tools
# Create a ToolNode to handle tool calls and add it to the graph
tool_node = ToolNode(tools=[tavily_tool])
graph_builder.add_node("tools", tool_node)

# Set up condition from chatbot to use tools when needed otherwise END
graph_builder.add_conditional_edges("chatbot", tools_condition)

# Connect tools back to chatbot and add START and END nodes
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph to prepare for execution with MEMORY
graph = graph_builder.compile(checkpointer=memory)

# Define a function to execute the chatbot based on user input
def stream_graph_updates_with_memory(user_input: str):
    config = {"configurable": {"thread_id": "single_session_memory"}}

    # Stream the events in the graph
    for event in graph.stream({"messages": [("user", user_input)]}, config):
        # Return the agen'ts last response
        for value in event.values():
            if "messages" in value and value["messages"]:
                print("Agent:", value["messages"][-1].content)

# Define the user query and run the chatbot
user_query = "Hello"
stream_graph_updates_with_memory(user_query)
while True:

	user_input = str(input("You: "))
	stream_graph_updates_with_memory(user_input)

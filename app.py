# Module for structuring text
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
load_dotenv()

# Langgraph modules for defining graphs
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages

# Module for setting up OpenAI
from langchain_openai import ChatOpenAI
from IPython.display import Image, display

# Modules for memory
from langgraph.checkpoint.memory import MemorySaver

# Modules for adding tool conditions and nodes
from langgraph.prebuilt import ToolNode, tools_condition

# Module for tools
from tools import tools

# Step 2: Set LLM with tools and memory
llm = ChatOpenAI(model="gpt-4o-mini")

memory = MemorySaver()

# List of tools
tool_node = ToolNode(tools=tools)

llm_with_tools = llm.bind_tools(tools)


# Step 3: Define stop function
# Use MessageState to define the state of the stopping function
def should_continue(state: MessagesState):
	# Get the last message from the state
	last_message = state["messages"][-1]

	# Check if the last message includes tool calls
	if last_message.tool_calls:
		return "tools"

	# End the conversation if no tool calls are present
	return END


# Use MessageState to define the state of the dynamic tool caller
def call_model(state: MessagesState):
	# Get the last message from the state
	last_message = state["messages"][-1]

	if isinstance(last_message, AIMessage) and last_message.tool_calls:

		# Return the messages from the tool call
		return {"messages": [AIMessage(content=last_message.tool_calls[0]["response"])]}

	else:
		# otherwise proceed with a regular llm response
		return {"messages": [llm_with_tools.invoke(state["messages"])]}

class State(TypedDict):
    # Define messages with metadata
    messages: Annotated[list, add_messages]


# Step 4: Initialize StateGraph
graph_builder = StateGraph(MessagesState)

# Step 5 : Defining Nodes and Edges
# Define chatbot function (node) to respond with the model
def chatbot(state: State):
    # llm get messages from state so far
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# Add nodes for chatbot and tools
graph_builder.add_node("chatbot", call_model)
graph_builder.add_node("tools", tool_node)

# Connect the START node to the chatbot
graph_builder.add_edge(START, "chatbot")

# Define conditions, then loop back to chatbot
graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", END])
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}


# Create input message with the user's query
def multi_tool_output(query):
	inputs = {"messages": [HumanMessage(content=query)]}

	for msg, metadata in graph.stream(inputs, config, stream_mode="messages"):

		# Check if the message has content and is not from human
		if msg.content and not isinstance(msg, HumanMessage):
			print(msg.content, end="", flush=True)
	print("\n")

multi_tool_output("Hello")

while True:
	queries = str(input("You: "))

	multi_tool_output(queries)

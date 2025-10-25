import operator
from typing import Literal, TypedDict, Any, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamWriter, interrupt, Send, Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
import os
import random
import asyncio
from .prompts import agent_system_prompt, triage_system_prompt, triage_user_prompt, profile, email, prompt_instructions
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal, Annotated
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import AsyncPostgresSaver

load_dotenv()
llm = init_chat_model("openai:gpt-4o-mini")

class Router(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails, "
                    "'notify' for important information that doesn't need a response, "
                    "'respond' for emails that need a reply",
    )


llm_router = llm.with_structured_output(Router)

class Weather(TypedDict):
    location: str
    search_status: str
    result: str


class State(MessagesState):
    weather_forecast: Annotated[list[Weather], operator.add]


class WeatherInput(TypedDict):
    location: str
    tool_call_id: str


class ToolNodeArgs(TypedDict):
    name: str
    args: dict[str, Any]
    id: str


class McpToolNodeArgs(TypedDict):
    server_name: str
    name: str
    args: dict[str, Any]
    id: str


@tool
async def weather_tool(query: str) -> str:
    """Call to get current weather"""
    return "Sunny"


@tool
async def create_reminder_tool(reminder_text: str) -> str:
    """Call to create a reminder"""
    return "Reminder created"

# Main Agent - Tools
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    # Placeholder response - in real app would send email
    return f"Email sent to {to} with subject '{subject}'"

@tool
def schedule_meeting(
    attendees: list[str],
    subject: str,
    duration_minutes: int,
    preferred_day: str
) -> str:
    """Schedule a calendar meeting."""
    # Placeholder response - in real app would check calendar and schedule
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"

@tool
def check_calendar_availability_tool(day: str) -> str:
    """Check calendar availability for a given day."""
    # Placeholder response - in real app would check actual calendar
    return "Check calendar availability"

# Main Agent - Define Prompt
def create_prompt(state):
    return [
        {
            "role": "system",
            "content": agent_system_prompt.format(
                instructions=prompt_instructions["agent_instructions"],
                **profile
                )
        }
    ] + state['messages']

# assistant_tools=[write_email, schedule_meeting, check_calendar_availability]
#
# assistant_agent = create_react_agent(
#     "openai:gpt-4o",
#     tools=assistant_tools,
#     prompt=create_prompt,
# )


async def weather(input: WeatherInput, writer: StreamWriter):
    location = input["args"]["query"]

    if not location:
        location = interrupt(input['args']['query'])

    # Send custom event to the client. It will update the state of the last checkpoint and all child nodes.
    # Note: if there are multiple child nodes (e.g. parallel nodes), the state will be updated for all of them.
    writer({"weather_forecast": [
           {"location": location, "search_status": f"Checking weather in {location}"}]})

    await asyncio.sleep(2)
    weather = random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"])

    return {"messages": [ToolMessage(content=weather, tool_call_id=input["id"])], "weather_forecast": [{"location": location, "search_status": "", "result": weather}]}


async def check_calendar_availability(input: ToolNodeArgs):

    return f"Available times on {input['args']['day']}: 9:00 AM, 2:00 PM, 4:00 PM"



async def reminder(input: ToolNodeArgs):
    res = interrupt(input['args']['reminder_text'])

    tool_answer = "Reminder created." if res == 'approve' else "Reminder creation cancelled by user."

    return {"messages": [ToolMessage(content=tool_answer, tool_call_id=input["id"])]}


async def chatbot(state: State):
    tools = [
        weather_tool,
        create_reminder_tool,
        check_calendar_availability_tool
    ]

    llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}


# Chatbot node router. Based on tool calls, creates the list of the next parallel nodes.
def assign_tool(state: State) -> Literal["weather", "reminder", "check_calendar_availability", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        send_list = []
        for tool in last_message.tool_calls:
            if tool["name"] == 'weather_tool':
                send_list.append(Send('weather', tool))
            elif tool["name"] == 'create_reminder_tool':
                send_list.append(Send('reminder', tool))
            elif tool["name"] == 'check_calendar_availability_tool':
                send_list.append(Send('check_calendar_availability', tool))

        return send_list if len(send_list) > 0 else "__end__"
    return "__end__"




builder = StateGraph(State)

builder.add_node("chatbot", chatbot)
builder.add_node("weather", weather)
builder.add_node("reminder", reminder)
builder.add_node("check_calendar_availability", check_calendar_availability)
# builder.add_node("mcp_tool", mcp_tool)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", assign_tool)
builder.add_edge("check_calendar_availability", "chatbot")
builder.add_edge("weather", "chatbot")
builder.add_edge("reminder", "chatbot")
# builder.add_edge("mcp_tool", "chatbot")

builder.add_edge("chatbot", END)

# memory = MemorySaver()
#
# graph = builder.compile(checkpointer=memory)
conn_string = os.environ.get("DATABASE_URL")
if not conn_string:
    raise ValueError("DATABASE_URL environment variable not set. Please add it to your .env file.")

# Set up the PostgresSaver
db = AsyncPostgresSaver.from_conn_string(conn_string)
print(f"Connected {db}")
graph = builder.compile(checkpointer=db)

# To execute graph in LangGraph Studio uncomment the following line
# graph = asyncio.run(init_agent())

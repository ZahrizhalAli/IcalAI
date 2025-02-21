# Module for Tools
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import tool
from dotenv import load_dotenv

load_dotenv()

# Tavily Search API
tavily_tool = TavilySearchResults()

@tool
def check_palindrome(text: str):
	"""To check whether a word or a phrase is a palindrome."""

	cleaned_text = ''.join(char.lower() for char in text if char.isalnum())

	if cleaned_text == cleaned_text[::-1]:
		return f"{text} is a palindrome."
	else:
		return f"{text} is NOT a palindrome"

# Define set of tools
tools = [tavily_tool, check_palindrome]
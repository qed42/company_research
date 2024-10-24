import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
import requests
import time
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from tavily import TavilyClient
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add file handler
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler('logs/company_research.log', maxBytes=10485760, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

load_dotenv(override=True)

app = FastAPI(title="Company Research API")

# Reference template from Reliance example
REFERENCE_TEMPLATE = """
Here's an example of how the response should be structured and detailed, following the style of Reliance Industries Ltd analysis:

The response should include detailed sections like:
1. A comprehensive introduction covering the company's position in its industry and key statistics
2. Business segments with detailed explanations of each division's operations and performance
3. Recent financial metrics with specific numbers and growth percentages
4. Leadership structure with key executive names and roles
5. Recent developments and future outlook

For example, the introduction should be as detailed as:
"[Company] is [country]'s [position] in [industry] and a [type] company led by [leader]. It has evolved from [historical context] to [current status] with interests spanning [list of sectors]."

Each business segment should have detailed metrics like:
"[Segment name] reported revenue of [amount] for [period], a growth of [percentage] over [comparison period]. The segment operates [number] of [facilities/stores/units] across [locations]."

Follow this level of detail and structure in your analysis."""

class OpenAIClient:
    def __init__(self):
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.site_url = os.getenv("YOUR_SITE_URL", "http://localhost")
        self.app_name = os.getenv("YOUR_APP_NAME", "CompanyResearchAPI")

    def generate_response(self, messages: List[Dict[str, str]], model: str) -> str:
        logger.info(f"Generating OpenRouter response with model: {model}")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages
        }

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.debug(f"OpenRouter API attempt {attempt + 1}")
                response = requests.post(self.url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("OpenRouter API request successful")
                return response.json()['choices'][0]['message']['content']
            except Exception as e:
                logger.error(f"OpenRouter API error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2

class TavilyResearch:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, search_depth: str = "basic") -> Dict:
        logger.info(f"Performing Tavily search: {query}")
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.debug(f"Tavily API attempt {attempt + 1}")
                result = self.client.search(
                    query,
                    search_depth=search_depth,
                    max_results=10
                )
                logger.info(f"Tavily search successful: found {len(result['results'])} results")
                return result
            except Exception as e:
                logger.error(f"Tavily API error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Tavily API error: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2

class CompanyResearch:
    def __init__(self):
        self.openai = OpenAIClient()
        self.tavily = TavilyResearch()
        self.model = "anthropic/claude-3.5-sonnet"
        self.research_sections = [
            {
                "name": "founded_year",
                "query": "When was {company} founded?"  # Simple and direct
            },
            {
                "name": "managing_director",
                "query": "Who is the current CEO of {company}?"  # Concise query
            },
            {
                "name": "introduction",
                "queries": [  # Split into multiple focused queries
                    "What is {company}'s main business?",
                    "What are {company}'s key achievements?",
                    "What is {company}'s market position?"
                ]
            },
            {
                "name": "company_overview",
                "queries": [
                    "What is {company}'s history?",
                    "How has {company} evolved?",
                    "What are {company}'s major milestones?"
                ]
            },
            {
                "name": "business_segments",
                "queries": [
                    "What are {company}'s business divisions?",
                    "What products does {company} offer?",
                    "What services does {company} provide?"
                ]
            },
            {
                "name": "leadership",
                "queries": [
                    "Who leads {company}?",
                    "Who are {company}'s board members?",
                    "Who are {company}'s executives?"
                ]
            },
            {
                "name": "financial_performance",
                "queries": [
                    "What is {company}'s recent revenue?",
                    "What is {company}'s profit growth?",
                    "What are {company}'s financial metrics?"
                ]
            },
            {
                "name": "business_segment_deep_dive",
                "queries": [
                    "How do {company}'s divisions perform?",
                    "What are {company}'s segment revenues?",
                    "How profitable are {company}'s segments?"
                ]
            },
            {
                "name": "recent_developments",
                "queries": [
                    "What are {company}'s latest announcements?",
                    "What are {company}'s recent acquisitions?",
                    "What are {company}'s new projects?"
                ]
            },
            {
                "name": "industry_outlook",
                "queries": [
                    "How competitive is {company}?",
                    "What is {company}'s market share?",
                    "What are {company}'s growth prospects?"
                ]
            }
        ]

    def resolve_company_info(self, input_text: str) -> str:
        logger.info(f"Resolving company info for: {input_text}")
        prompt = f"""Given the input '{input_text}', if this is a stock code, provide the full company name. 
        If it's a company name, provide the stock code. Respond with only the requested information, no additional text."""
        
        messages = [{"role": "user", "content": prompt}]
        result = self.openai.generate_response(messages, self.model)
        logger.info(f"Resolved company info: {result}")
        return result

    def extract_section_info(self, content: str, section_name: str) -> str:
        logger.info(f"Extracting information for section: {section_name}")
        prompt = f"""From the following content, extract and summarize information relevant to {section_name}. 
        Follow the style and level of detail shown in this reference example:
        {REFERENCE_TEMPLATE}
        
        Content to analyze:
        {content}"""
        
        messages = [{"role": "user", "content": prompt}]
        result = self.openai.generate_response(messages, self.model)
        logger.info(f"Extracted information for {section_name}: {len(result)} characters")
        return result

    async def research_company(self, company_input: str) -> Dict:
        logger.info(f"Starting research for company: {company_input}")
        resolved_info = self.resolve_company_info(company_input)
        
        company_data = {
            "input": company_input,
            "resolved_info": resolved_info,
            "timestamp": datetime.now().isoformat(),
            "sections": {}
        }

        for section in self.research_sections:
            logger.info(f"Researching section: {section['name']}")
            combined_content = ""

            # Handle both single query and multiple queries cases
            queries = section.get('queries', [section['query']] if 'query' in section else [])
            
            for query in queries:
                formatted_query = query.format(company=company_input)
                # Validate query length
                if len(formatted_query) < 5:
                    logger.warning(f"Query too short, skipping: {formatted_query}")
                    continue
                    
                logger.info(f"Executing Tavily query: {formatted_query}")
                search_results = self.tavily.search(formatted_query)
                
                # Combine results from each query
                query_content = "\n\n".join(
                    f"Title: {result['title']}\nContent: {result['content']}"
                    for result in search_results['results']
                )
                combined_content += "\n\n" + query_content if combined_content else query_content
            
            section_info = self.extract_section_info(combined_content, section['name'])
            company_data['sections'][section['name']] = section_info
            
            # Small delay to avoid rate limits
            time.sleep(1)

        logger.info(f"Research completed for {company_input}")
        return company_data

# Initialize the research client
researcher = CompanyResearch()

class CompanyRequest(BaseModel):
    company_input: str

class CompanyResponse(BaseModel):
    input: str
    resolved_info: str
    timestamp: str
    sections: Dict[str, str]

@app.post("/research_company", response_model=CompanyResponse)
async def research_company(request: CompanyRequest):
    """
    Research a company by name or stock code and return structured information.
    """
    logger.info(f"Received research request for: {request.company_input}")
    try:
        result = await researcher.research_company(request.company_input)
        logger.info(f"Successfully completed research for: {request.company_input}")
        return result
    except Exception as e:
        logger.error(f"Error researching company {request.company_input}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Company Research API")
    uvicorn.run(app, host="0.0.0.0", port=8000)

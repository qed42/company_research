# Company Research API

A FastAPI service that provides detailed company research and analysis using OpenRouter AI and Tavily search.

## Prerequisites

- Docker
- Docker Compose
- API keys for OpenRouter and Tavily

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd company-research-api
```

2. Create your environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your API keys:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Running the Service

1. Build and start the service:
```bash
docker-compose up --build
```

2. The API will be available at `http://localhost:8000`

## API Documentation

Once the service is running, you can access:
- OpenAPI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## API Endpoints

### POST /research_company

Research a company by name or stock code.

Request:
```json
{
  "company_input": "AAPL"
}
```

Response:
```json
{
  "input": "AAPL",
  "resolved_info": "Apple Inc. (NASDAQ: AAPL)",
  "timestamp": "2024-10-24T10:00:00.000Z",
  "sections": {
    "founded_year": "...",
    "managing_director": "...",
    "introduction": "...",
    "company_overview": "...",
    "business_segments": "...",
    "leadership": "...",
    "financial_performance": "...",
    "business_segment_deep_dive": "...",
    "recent_developments": "...",
    "industry_outlook": "..."
  }
}
```

### GET /health

Health check endpoint.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-10-24T10:00:00.000Z"
}
```

## Example Usage

Using curl:
```bash
curl -X POST http://localhost:8000/research_company \
  -H "Content-Type: application/json" \
  -d '{"company_input": "AAPL"}'
```

Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/research_company",
    json={"company_input": "AAPL"}
)
company_data = response.json()
print(company_data)
```

## Project Structure

```
.
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── main.py                # FastAPI application code
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Example environment file
└── README.md              # This file
```

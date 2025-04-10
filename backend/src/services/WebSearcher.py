from typing import Dict, List
from src.config.settings import GPSE_API_KEY, CX
from langchain_google_community import GoogleSearchAPIWrapper,GetCurrentDatetime


# Initialize Google Search API wrapper

class WebSearcher:
    def __init__(self, GPSE_API_KEY: str=GPSE_API_KEY, CX: str=CX):
        self.web_searcher = GoogleSearchAPIWrapper(
            google_api_key=GPSE_API_KEY,
            google_cse_id=CX
        )
        
    def search(self, query: str) -> str:
        return self.web_searcher.run(query)
    
    def current_date(self) -> str:
        return GetCurrentDatetime().run()   
    
    
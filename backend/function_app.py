import azure.functions as func
import logging
from app import app as fastapi_app  # Import the FastAPI app from app.py
from dotenv import load_dotenv

load_dotenv()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # V2 model: Create FunctionApp instance

@app.route(route="{*route}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])  # V2 model: Use decorator for HTTP trigger
async def main(req: func.HttpRequest) -> func.HttpResponse: # V2 model: Removed res parameter
    logging.info('Python HTTP trigger function processed a request.')
    # Use AsgiMiddleware to handle the request with the FastAPI app
    return await func.AsgiMiddleware(app=fastapi_app).handle_async(req)
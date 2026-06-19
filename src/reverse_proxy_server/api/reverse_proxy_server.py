""""""
# 3rd-Party Imports
from fastapi import APIRouter

router = APIRouter()

# Endpoint for welcome message
@router.get("/", tags=["HomePage"])
async def welcome():
    """"""
    return {"message": "Welcome to the Reverse Proxy Server!"}

@router.get("/list_up_stream", tags=["Upstreams"])
async def list_upstream():
    """"""
    # Placeholder for actual upstream listing logic
    return {"upstreams": ["upstream1", "upstream2", "upstream3"]}
import json
import traceback
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from utils.code_helper import graph, system_message
from langchain_core.messages import SystemMessage, HumanMessage

from models import *
from Routers.auth import verify_basic_auth
from utils.curl_parser import parse_curl
from action_template import *
from utils.action_templates import *


actions = APIRouter(
    prefix="/prompt/actions",
    tags = ["Actions"]
)   


@actions.get("/available-actions")
async def get_available_actions(auth: str = Depends(verify_basic_auth)):
    return ["pre_call", "post_call", "get_current_date_time_tool", "convert_digit_to_words_tool"]


@actions.get("/action-template")
async def get_action_template(action_name: str, external_api_call: bool = False, current_date_code: bool = False, update_dashboard_code: bool = False, upload_recording_code: bool = False, auth: str = Depends(verify_basic_auth)):
    """ This end point provides action templates """

    try:
        if action_name == "pre_call":
            return get_pre_call_template(external_api_call, current_date_code)
        
        elif action_name == "post_call":
            return get_post_call_template(external_api_call, update_dashboard_code, upload_recording_code)
        
        elif action_name == "get_current_date_time_tool":
            return get_tool_current_date_time()
        
        elif action_name == "convert_digit_to_words_tool":
            return get_tool_digits_to_words()
        
        else:
            return {
                "message": "pass valid action name"
            }

    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")
    

@actions.post("/tool-from-curl")
async def get_functions(user_req: function_request, auth: str = Depends(verify_basic_auth)):
    """ This end point serve to create python function from curl """

    try:
        curl_str = user_req.curl_command
        dynamic_map = json.loads(user_req.dynamic_map)

        python_code = parse_curl(curl_str, dynamic_map)

        return {
            "python_code": python_code
        }
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")
    

@actions.post("/build-tool")
async def build_function(user_req: tool_request, auth: str = Depends(verify_basic_auth)):
    """ This end point serve AI Assist """

    try:
        user_prompt = user_req.user_prompt
        uu_id = user_req.uu_id

        if not uu_id:
            uu_id = str(uuid4())
            config = {
                "configurable": {"thread_id": uu_id}
            }

            result = graph.invoke({"messages": [HumanMessage(content=user_prompt)]}, config=config)
            
        else:
            result = graph.invoke({"messages": [SystemMessage(content=system_message), HumanMessage(content=user_prompt)]}, config={"configurable": {"thread_id": uu_id}})

        return {
            "result": result["messages"][-1].content,
            "uu_id": uu_id
        }
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")
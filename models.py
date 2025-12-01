from pydantic import BaseModel, Field

# Request model for function generator from cURL
class function_request(BaseModel):
    curl_command: str
    dynamic_map: str

# Response model for function generator from cURL 
class function_response(BaseModel):
    function_code: str

# Request model for tool generation from prompt
class tool_request(BaseModel):
    user_prompt: str
    uu_id: str | None

# Response model for tool generation from prompt
class tool_response(BaseModel):
    result: str
    uu_id: str

class return_funcion(BaseModel):
    python_function: str = Field(description="pyhton function named customFunction according to user requirements.")
    function_description: str = Field(description="descrrption of function in 25-50 words.")
    params_description: str = Field(description="json string of key-value pair where key will be parameters of function and values should be description of those parameter.")
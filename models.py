from pydantic import BaseModel, Field
from typing import List, Optional, Literal

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

class params_desc(BaseModel):
    param: str = Field(description="parameter name")
    pram_type: str = Field(description="parameter data type")
    param_desc: str = Field(description="parameter description (short description; with-in 5-10 words)")

class return_funcion(BaseModel):
    python_function: str = Field(description="pyhton function named customFunction according to user requirements.")
    function_description: str = Field(description="descrrption of function in 25-50 words.")
    params_description: List[params_desc]

# Request to insert prompt
class new_prompt(BaseModel):
    prompt: str = Field(description="prompt to be insert")  
    service_type: str = Field(description="prompt service type to be update")
    agent_type: str = Field(description="prompt agent type to be update")
    language: str = Field(description="prompt language to be update")
    use_case: str = Field(description="use case of the prompt")

class new_prompt_component(BaseModel):
    prompt_component: str = Field(description="prompt component to be update")

# Request model to update prompt
class update_prompt_request(BaseModel):
    prompt_id: str = Field(description="prompt id")
    prompt: str | None = Field(None, description="prompt to be update")
    service_type: str | None = Field(None, description="prompt service type to be update")
    agent_type: str | None = Field(None, description="prompt agent type to be update")
    language: str | None = Field(None, description="prompt language to be update")
    use_case: str | None = Field(None, description="use case of the prompt")

# Request to update prompt component
class update_prompt_component_request(BaseModel):
    prompt_component_id: str = Field(description="prompt component id")
    prompt_component: str = Field(description="prompt component to be update")

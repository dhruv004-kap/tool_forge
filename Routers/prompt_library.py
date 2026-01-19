import os
import re
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from pymongo import MongoClient

from bson.objectid import ObjectId

from models import *
from Routers.auth import verify_basic_auth
from action_template import *
from utils.prompt_utils import evaluate_prompt


DB_URI = os.getenv("DB_URI")

conn = MongoClient(DB_URI)
db = conn["vb_platform"]
prompt_library = db["prompt_library"]


library = APIRouter(
    prefix="/prompt/prompt-library",
    tags=["Prompt_library"]
)


@library.get("/prompt-components")
async def get_prompt_components(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available prompts components """
    try:
        prompts = list(prompt_library.find({"component_type": "prompt_component"}))

        for doc in prompts:
            doc["prompt_component_id"] = str(doc.get("_id"))
            del doc["_id"]

        return prompts
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")


@library.get("/get-service-types")
async def get_service_types(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available industry for prompts """

    try:
        # get available industries from DB
        service_types_record = prompt_library.find({"component_type": "prompt"}, {"service_type": 1, "_id": 0})

        service_types = []

        for doc in service_types_record:
            service_types.append(doc.get("service_type"))

        return set(service_types)
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")


@library.get("/get-prompt-languages")
async def get_prompt_languages(auth: str = Depends(verify_basic_auth)):
    """ This is end poin to get available languages for prompts """

    try:
        # get available prompts from DB
        languages_records = prompt_library.find({"component_type": "prompt"}, {"language": 1, "_id": 0})

        languages = []

        for doc in languages_records:
            languages.append(doc.get("language"))

        return set(languages)
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    

@library.get("/prompts")
async def get_prompts(service_type: str, language: str = None, auth: str = Depends(verify_basic_auth)):
    """ This end point for prompt library """

    try:
        # get prompts from DB for selected industry
        db_query = {"service_type": {"$regex": re.compile(service_type, re.IGNORECASE)}}

        if language:
            db_query.update({"language": re.compile(language, re.IGNORECASE)})

        available_prompt = list(prompt_library.find(db_query))

        for doc in available_prompt:
            doc["prompt_id"] = str(doc.get("_id"))
            del doc["_id"]

        return available_prompt
    
    except Exception as e:
        print(f"\nError: {e}; \nTraceback: {traceback.format_exc()}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    
# === insertion endpoints === #
@library.post("/prompts/add-prompt")
async def insert_prompt(user_req: new_prompt, auth: str = Depends(verify_basic_auth)):
    """ Endpoint to insert new prompt """
    try:
        user_req = user_req.model_dump()

        prompt = user_req.get("prompt")

        insert_query = {
            "service_type": user_req.get("service_type", "").capitalize(),
            "prompt_accuracy": "",
            "prompt": prompt,
            "agent_type": user_req.get("agent_type"),
            "use_case": user_req.get("use_case").capitalize(),
            "language": user_req.get("language").capitalize(),
            "component_type": "prompt"
        }

        # evaluate the prompt & get prompt accuracy
        prompt_evaluation = evaluate_prompt(prompt)
        accuracy = prompt_evaluation.get("accuracy")
        insert_query["prompt_accuracy"] = accuracy

        if float(accuracy) < 70:
            return JSONResponse(status_code=200, content="Prompt should score more than 70% accuracy to get inserted!")

        prompt_library.insert_one(insert_query)

        return JSONResponse(
            status_code=200,
            content={
                "status": "Success"
            }
        )
    
    except Exception as e:
        print(f"Error: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    

@library.post("/prompts/add-prompt-component")
async def insert_prompt_component(user_req: new_prompt_component, auth: str = Depends(verify_basic_auth)):
    """ Endpoint to insert new prompt component """
    try:
        user_req = user_req.model_dump()

        prompt_component = user_req.get("prompt_component")

        insert_query = {
            "accuracy": "",
            "prompt_component": prompt_component,
            "component_type": "prompt_component"
        }

        # evaluate the prompt & get prompt accuracy
        prompt_evaluation = evaluate_prompt(prompt_component)
        accuracy = prompt_evaluation.get("accuracy")
        insert_query["accuracy"] = accuracy

        prompt_library.insert_one(insert_query)

        return JSONResponse(
            status_code=200,
            content={
                "status": "Success"
            }
        )
    
    except Exception as e:
        print(f"Error: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    

# === updation endpoints === #
@library.post("/prompts/update-prompt")
async def update_prompt(user_req: update_prompt_request, auth: str = Depends(verify_basic_auth)):
    """ Endpoint to update the prompt """
    try:
        user_req = user_req.model_dump()
        print(f"user request: {user_req}")

        prompt_id = user_req.get("prompt_id")
        prompt = user_req.get("prompt")

        # check for valid prompt_id
        if not ObjectId.is_valid(prompt_id):
            return JSONResponse(status_code=422, content="Invalid prompt ID")

        update_query = {}
        
        if prompt:
            # evaluate the prompt & get prompt accuracy
            prompt_evaluation = evaluate_prompt(prompt)
            accuracy = prompt_evaluation.get("accuracy")
            update_query["prompt"] = prompt
            update_query["prompt_accuracy"] = accuracy

        if user_req.get("service_type"):
            update_query["service_type"] = user_req.get("service_type")

        if user_req.get("agent_type"):
            update_query["agent_type"] = user_req.get("agent_type")

        if user_req.get("language"):
            update_query["language"] = user_req.get("language")

        if user_req.get("use_case"):
            update_query["use_case"] = user_req.get("use_case")

        if update_query:
            result = prompt_library.update_one({"_id": ObjectId(prompt_id)}, {"$set": update_query})

            if result.modified_count == 1:
                print(f"prompt with prompt id: {prompt_id} successfully updated!")
            else:
                print(f"No prompt found with prompt id: {prompt_id}")
                return JSONResponse(
                    status_code=404, 
                    content={
                        "prompt_id": prompt_id,
                        "status": "Failed"
                    }
                )

        return JSONResponse(status_code=200, content={
            "prompt_id": prompt_id,
            "status": "Success"
        })

    except Exception as e:
        print(f"Error: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error!")
    

@library.post("/prompts/update-prompt-conponent")
async def update_prompt_component(user_req: update_prompt_component_request, auth: str = Depends(verify_basic_auth)):
    
    try:
        user_req = user_req.model_dump()

        component_id = user_req.get("prompt_component_id")
        prompt_component = user_req.get("prompt_component")

        # check for valid prompt_id
        if not ObjectId.is_valid(component_id):
            return JSONResponse(status_code=422, content="Invalid prompt ID")

        # evaluate prompt component & get accuracy
        component_evaluation = evaluate_prompt(prompt_component)
        accuracy = component_evaluation.get("accuracy")

        update_query = {
            "prompt_component": prompt_component,
            "accuracy": accuracy
        }

        result = prompt_library.update_one({"_id": ObjectId(component_id)}, {"$set": update_query})

        if result.modified_count == 1:
            print(f"prompt component with id: {component_id} successfully updated!")
        else:
            print(f"No prompt component found with id: {component_id}")
            return JSONResponse(
                status_code=404, 
                content={
                    "prompt_component_id": component_id,
                    "status": "Failed"
                }
            )

        return JSONResponse(status_code=200, content={
            "prompt_component_id": component_id,
            "status": "Success"
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error: {e}")
    

# === deletion endpoint === #
@library.delete("/prompts/delete-prompt/{prompt_id}")
async def delete_prompt_component(prompt_id: str, auth: str = Depends(verify_basic_auth)):
    """ Endpont to delete prompt or prompt component """
    try:
        result = prompt_library.delete_one({"_id": ObjectId(prompt_id)})

        if result.deleted_count == 0:
            print(f"No prompt or prompt found with id: {prompt_id}")
            return JSONResponse(status_code=404, content={
                "prompt_id": prompt_id,
                "status": "Failed",
                "content": f"No prompt or prompt found with id: {prompt_id}"
            })
        
        return JSONResponse(status_code=200, content={
            "status": "Success"
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error: {e}")
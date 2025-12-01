pre_call_template = """import requests
import traceback

def customFunction(phone):

    ticket_url = f"create_ticket_url"

    ticket_headers = {
        "Authorization": "auth-token",
        "Cookie" : "cookies"
    }

    try:
        response = requests.post(url=ticket_url, headers=ticket_headers)
        res_status = response.status_code
        print(f"\nTicket creation response status: {res_status}")

        if res_status == 200:
            res_json = response.json()
            print(f"\nCreate ticket response: {res_json}")

            return {
                "ticket_id": res_json.get("ticket_id"),
                "phone": phone
            }
        
        else:
            res_text = response.text
            print(f"\nResponse text: {res_text}")

            return {
                "error": "ticket creation failed!"
            }
        
    except Exception as e:
        print(f"\nError: {e}; Traceback: {traceback.format_exc}")
        return {
            "error": f"error occured; Error: {e}"
        }
"""

post_call_template = """import json
import requests
import traceback
from openai import OpenAI
from pymongo import MongoClient
from pydantic import BaseModel, Field
from datetime import datetime

def customFunction(ticket_id,conversation_id):

    # === Configs === #
    API_KEY = "openai-api-key"
    mongo_uri = "db-connection-link"
    
    # === MongoDB Connection ===
    client = MongoClient(mongo_uri)
    db = client["voicebot_platform"]
    be_tp = db["be_tp"] 
    conversation_memory = db["conversation_memory"]

    # getting recording and times from DB
    be_tp_obj = be_tp.find_one({"conversation_id": conversation_id})

    recording_url = be_tp_obj.get("recording_url")
    client_id = be_tp_obj.get("client_id")
    bot_id = be_tp_obj.get("config_id")
    to_phone = be_tp_obj.get("to_phone")
    from_phone = be_tp_obj.get("from_phone")
    start_time = be_tp_obj.get("start_time")
    end_time = be_tp_obj.get("end_time")

    # === Calculating call duration === #
    try:
        print("\nstart_time: ", start_time, ", end_time: ", end_time)

        format_string = "%Y-%m-%d %H:%M:%S"
       
        if start_time and end_time:
            start_time_obj = datetime.strptime(start_time, format_string)
            end_time_obj = datetime.strptime(end_time, format_string)

            duration = (end_time_obj - start_time_obj).total_seconds()
            print("\nDuration: ", duration)
        
        else:
            duration = 1
            print("\nMissing start_time or end_time")

    except Exception as e:
        duration = 1
        print("\nSome error occured during calculating duration")

    # === Taking conversation from DB === #
    conversation_memory_obj = conversation_memory.find_one({"conversation_id": conversation_id})
    conversation = conversation_memory_obj.get("conversation_history", "")

    formatted_conversation = ""
    for entry in conversation:
        role = entry['role'].capitalize()
        content = entry['content']
        formatted_conversation += f"{role}: {content}\n"

    # === Response model for openai llm invoke === #
    class response_model(BaseModel):
        customer_name: str = Field(description="name of the customer")
        product_name: str = Field(description="name of the product customer have")
        model_name: str = Field(description="name of the product customer have")
        issue: str = Field(description="issue happening with product")
        address: str  = Field(description="customer full address with landmark")
        pincode: str = Field(description="pincode number (must be 6 digits only)")
        area: str = Field(description="area name")
        city: str  = Field(description="city name")

    # === prompt for openai llm invoke === #
    prompt = f\"""You are a professional content extractor.
    Your task is to extract important information from the given conversation in structured manner.(extract all the information in english language only).
    Extract the Following information from the given conversation:
        - customer name,
        - product name,
        - model name,
        - issue,
        - address,
        - pincode,
        - area,
        - city

        Conversation: {formatted_conversation}
    \"""

    # === openai llm invoke === #
    openai_client = OpenAI(api_key=API_KEY)
    try:
        response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a structured information extractor."},
            {"role": "user", "content": prompt}
        ],
        response_format=response_model,
        temperature=0.2)
        openai_output_response = response.choices[0].message.content
        openai_output = json.loads(openai_output_response)
        print("\nOpenAi response:\n", openai_output)

    except json.JSONDecodeError:
        raise ValueError("Failed to parse GPT output")
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
    # parse openai output
    associate_obj = {
        "customer_name": openai_output.get("customer_name"),
        "product_name": openai_output.get("product_name"),
        "model_name": openai_output.get("model_name"),
        "issue": openai_output.get("issue"),
        "address": openai_output.get("address"),
        "area": openai_output.get("area"),
        "pincode": openai_output.get("pincode"),
        "city": openai_output.get("city")
    }   

    # === Uploading Recording URL === #
    try:
        recording_upload_url = "recording-upload-url"    
        emp_code = ""                                                                     

        recording_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'auth-token'
        }

        callback_payload = json.dumps({
            "ticketId": ticket_id,
            "ucid": f"@@{client_id}@@{bot_id}@@{conversation_id}@@",
            "recording": recording_url,
            "duration": str(duration),
            "agentId": emp_code,
            "dialStatus": "completed",
            "from": from_phone,
            "to": to_phone,
            "callType": "inbound/outbound",
        })

        print("\nPOSTING RECORDING URL")
        response = requests.post(url=recording_upload_url, headers=recording_headers, data=callback_payload, timeout=10)

        if response.status_code == 200 :
            print("\nUploading voice recording url: Success")
            print(f"\nUploading Recording URL response: {response}")
        else :
            print("\nUploading voice recording url: Failed")
            print(f"\nUploading Recording URL response: {response}")

    except Exception as e:
        print(f"\nError occured during uploading recording url! \nTraceback: {traceback.format_exc()}")
    
    # === Dashboard updation
    dashboard_url = "dashboard-url"
    dashboard_headers = {
        "Content-Type":"application/json"
    }

    dashboard_payload = {
        "uploader_id": None,
        "client_id": client_id,
        "config_id": be_tp_obj.get("config_id"),   
        "coversation_id": conversation_id,
        "ticket_id": ticket_id,
        "call_sid": be_tp_obj.get("call_sid"),
        "call_queue_id": be_tp_obj.get("call_queue_id"),
        "call_queue_object_id": be_tp_obj.get("call_queue_object_id"),
        "call_duration": str(duration),
        "call_direction": "Inibound/Outbound",
        "call_recording": recording_url,
        "call_attempt": 1,
        "call_timestamp": start_time,
        "telephony_status": "completed",
        "associate_object": [associate_obj],
        "cx_metrics": {},
        "use_case": "use-case-of-flow",
        "call_extras": {
            "call_started": start_time,
            "call_ended": end_time
        },
        "tag_id": None
    }

    # === Update ticket === #
    ticket_url = "update-ticket-url"

    ticket_headers = {
        "Authorization": "auth-token"
    }

    ticket_payload = [{
        "comment": "",
        "ticket_id": ticket_id,
        "callback_time": "",
        "sub_status": "RS",
        "queue": "",
        "disposition": "",
        "associate_objects": associate_obj
    }]

    try:
        response = requests.post(url=ticket_url, headers=ticket_headers, json=ticket_payload)
        res_status = response.status_code
        print(f"\nTicket updation response status: {res_status}")

        if res_status == 200:
            res_json = response.json()
            print(f"\nCreate ticket response: {res_json}")

            return {
                "ticket_id": ticket_id,
                "ticket_status": res_status == 200
            }
        
        else:
            res_text = response.text
            print(f"\nResponse text: {res_text}")

            return {
                "error": "ticket creation failed!",
                "ticket_status": res_status == 200
            }
        
    except Exception as e:
        print(f"\nError: {e}; Traceback: {traceback.format_exc}")
        return {
            "error": f"error occured; Error: {e}"
        }
"""
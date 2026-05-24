"""
WhatsApp integration routes
"""
from fastapi import APIRouter, Request, HTTPException, status, Form
from app.core.config import settings
from app.services.whatsapp_service import WhatsAppService
from app.services.task_service import TaskService
from app.services.voice_service import VoiceProcessingService
from app.core.database import get_db
import json

router = APIRouter()

whatsapp_service = WhatsAppService()

@router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    """Verify WhatsApp webhook during setup"""
    try:
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        if token == settings.WHATSAPP_VERIFY_TOKEN:
            return int(challenge)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification token"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/webhook")
async def handle_whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages and webhooks"""
    try:
        body = await request.json()
        
        # Verify request signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        body_bytes = json.dumps(body).encode('utf-8')
        
        if not whatsapp_service.verify_webhook_signature(signature, body_bytes):
            # Still process but log security warning
            print("WARNING: Invalid signature for WhatsApp webhook")
        
        # Parse incoming message
        message_data = whatsapp_service.process_incoming_message(body)
        
        if not message_data:
            return {"status": "no_message"}
        
        # Handle different message types
        if message_data["type"] == "text":
            await _handle_text_message(message_data)
        
        elif message_data["type"] == "audio":
            await _handle_audio_message(message_data)
        
        elif message_data["type"] == "location":
            await _handle_location_message(message_data)
        
        return {"status": "received"}
    
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        return {"status": "error", "detail": str(e)}

async def _handle_text_message(message_data: dict):
    """Process text message from customer"""
    phone = message_data["sender_phone"]
    text = message_data["content"].get("text", "")
    
    db = get_db()
    
    # Find or create customer
    customer_response = db.table("customers").select("*").eq("phone_number", phone).execute()
    
    if not customer_response.data:
        # New customer
        customer_response = db.table("customers").insert({
            "name": f"Customer {phone}",
            "phone_number": phone
        }).execute()
        if not customer_response.data:
            return
        customer_id = customer_response.data[0]["user_id"]
    else:
        customer_id = customer_response.data[0]["user_id"]
    
    # Store message for reference
    db.table("whatsapp_messages").insert({
        "customer_id": customer_id,
        "phone_number": phone,
        "message_type": "text",
        "message_content": json.dumps({"text": text})
    }).execute()
    
    # Classify task from text
    voice_service = VoiceProcessingService()
    classification = await voice_service.classify_voice_request(text)
    
    # Respond to user
    await whatsapp_service.send_text_message(
        phone,
        f"Got it! Task type: {classification.get('task_type')}\nPlease share your location to proceed."
    )

async def _handle_audio_message(message_data: dict):
    """Process voice note message from customer"""
    phone = message_data["sender_phone"]
    audio_id = message_data["content"].get("audio", "")
    
    db = get_db()
    
    # Find or create customer
    customer_response = db.table("customers").select("*").eq("phone_number", phone).execute()
    
    if not customer_response.data:
        customer_response = db.table("customers").insert({
            "name": f"Customer {phone}",
            "phone_number": phone
        }).execute()
        if not customer_response.data:
            return
        customer_id = customer_response.data[0]["user_id"]
    else:
        customer_id = customer_response.data[0]["user_id"]
    
    # Download audio
    audio_bytes = await whatsapp_service.download_media(audio_id, "audio")
    
    if not audio_bytes:
        await whatsapp_service.send_text_message(phone, "Sorry, couldn't download your voice note. Please try again.")
        return
    
    # Transcribe audio
    voice_service = VoiceProcessingService()
    transcription = await voice_service.transcribe_audio(audio_bytes, language="en")
    
    if not transcription:
        await whatsapp_service.send_text_message(phone, "Couldn't understand the audio. Please try again.")
        return
    
    # Classify task
    classification = await voice_service.classify_voice_request(transcription)
    
    # Store message
    db.table("whatsapp_messages").insert({
        "customer_id": customer_id,
        "phone_number": phone,
        "message_type": "audio",
        "message_content": json.dumps({"transcription": transcription, "classification": classification})
    }).execute()
    
    # Send response
    response_text = f"""
Got your voice note!
Service: {classification.get('task_type')}
Task: {classification.get('title')}
Urgency: {classification.get('urgency_level')}/5

Please share your location to see pricing and available workers.
    """
    
    await whatsapp_service.send_text_message(phone, response_text.strip())

async def _handle_location_message(message_data: dict):
    """Process location message from customer"""
    phone = message_data["sender_phone"]
    latitude = message_data["content"].get("latitude")
    longitude = message_data["content"].get("longitude")
    
    db = get_db()
    
    # Find customer
    customer_response = db.table("customers").select("*").eq("phone_number", phone).execute()
    
    if not customer_response.data:
        await whatsapp_service.send_text_message(phone, "Please send a valid request first.")
        return
    
    customer_id = customer_response.data[0]["user_id"]
    
    # Get latest pending task or create one
    tasks_response = db.table("whatsapp_messages").select("*").eq("customer_id", customer_id).eq("processed", False).order("created_at", desc=True).limit(1).execute()
    
    if not tasks_response.data:
        await whatsapp_service.send_text_message(phone, "No pending task found. Please describe what you need.")
        return
    
    message = tasks_response.data[0]
    message_content = json.loads(message.get("message_content", "{}"))
    classification = message_content.get("classification", {})
    
    # Create task
    task_service = TaskService(db)
    task = await task_service.create_task_from_voice(
        customer_id=customer_id,
        title=classification.get("title", "Service Request"),
        description=classification.get("description", message_content.get("transcription", "")),
        task_type=classification.get("task_type", "other"),
        location_lat=latitude,
        location_lng=longitude,
        urgency_level=classification.get("urgency_level", 2)
    )
    
    # Mark message as processed
    db.table("whatsapp_messages").update({"processed": True}).eq("message_id", message["message_id"]).execute()
    
    # Send confirmation
    await whatsapp_service.send_text_message(
        phone,
        f"""
✓ Task Created Successfully!
Title: {task['title']}
Estimated Cost: ₹{task['estimated_price']}
Mode: Quick (Fast)

We're finding workers for you. You'll get updates soon!
        """
    )

@router.post("/send-message")
async def send_whatsapp_message(phone_number: str, message: str):
    """Send WhatsApp message to customer (internal use)"""
    try:
        success = await whatsapp_service.send_text_message(phone_number, message)
        
        if success:
            return {"status": "sent"}
        else:
            raise Exception("Failed to send message")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/send-template-message")
async def send_template_message(
    phone_number: str,
    template_type: str,  # task_created, task_assigned, task_completed, payout
    data: dict
):
    """Send predefined template messages"""
    try:
        whatsapp = WhatsAppService()
        
        if template_type == "task_created":
            message = f"Task '{data.get('title')}' created! Estimated cost: ₹{data.get('price')}"
        
        elif template_type == "task_assigned":
            message = f"Worker {data.get('worker_name')} assigned to your task!"
        
        elif template_type == "task_completed":
            message = f"Task completed! Total amount: ₹{data.get('amount')}"
        
        elif template_type == "payout":
            message = f"Payout of ₹{data.get('amount')} has been processed!"
        
        else:
            raise Exception("Unknown template type")
        
        success = await whatsapp.send_text_message(phone_number, message)
        
        return {"status": "sent" if success else "failed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

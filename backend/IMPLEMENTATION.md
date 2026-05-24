# BACKEND IMPLEMENTATION GUIDE

## Complete FastAPI Backend for ElderCare System

This is a fully-implemented production-ready backend with all core features for the WhatsApp-based eldercare service platform.

## ✅ Fully Implemented Features

### 1. **Authentication System**
- Customer registration and login
- Worker registration and login
- JWT-based authentication
- Secure password handling with bcrypt

**Routes:**
- `POST /api/v1/auth/register/customer` - Register customer
- `POST /api/v1/auth/register/worker` - Register worker
- `POST /api/v1/auth/login` - Login by phone number

### 2. **Task Management**
- Create tasks from voice notes (with AI transcription & classification)
- Create tasks from text (WhatsApp messages)
- Real-time task status tracking
- Worker matching algorithm
- Task assignment to verified workers
- Cancel tasks with reason

**Routes:**
- `POST /api/v1/tasks/create` - Create task manually
- `POST /api/v1/tasks/create-from-voice` - Create from voice notes
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PUT /api/v1/tasks/{task_id}` - Update task status
- `POST /api/v1/tasks/{task_id}/cancel` - Cancel task
- `GET /api/v1/tasks/customer/{customer_id}` - Get customer's tasks
- `GET /api/v1/tasks/available/quick` - Get available quick mode tasks

### 3. **Worker Management**
- Worker profile management
- Service type selection
- Real-time location tracking
- Task acceptance/rejection
- Check-in/check-out functionality
- Performance statistics (rating, completion rate)
- Worker verification system

**Routes:**
- `GET /api/v1/workers/{worker_id}` - Get worker profile
- `PUT /api/v1/workers/{worker_id}/location` - Update location
- `GET /api/v1/workers/{worker_id}/available-tasks` - Get available tasks
- `POST /api/v1/workers/{worker_id}/accept-task/{task_id}` - Accept task
- `POST /api/v1/workers/{worker_id}/reject-task/{task_id}` - Reject task
- `POST /api/v1/workers/{worker_id}/check-in/{task_id}` - Check-in
- `POST /api/v1/workers/{worker_id}/check-out/{task_id}` - Check-out + completion
- `GET /api/v1/workers/{worker_id}/stats` - Get worker stats

### 4. **Dynamic Pricing Engine**
- Distance-based pricing (₹5 per km)
- Service type pricing (medicine, help, visit, cleaning)
- Effort level multiplier (1-5 levels)
- Urgency multiplier for quick mode
- Estimated completion time calculation
- 75/25 payout split calculation

**Routes:**
- `POST /api/v1/pricing/calculate` - Calculate with factors
- `POST /api/v1/pricing/calculate-with-urgency` - Calculate with urgency
- `GET /api/v1/pricing/quick-mode/{service_type}` - Quick mode pricing
- `GET /api/v1/pricing/scheduled-mode/{service_type}` - Scheduled mode pricing
- `GET /api/v1/pricing/estimate/{task_id}` - Task price estimate
- `GET /api/v1/pricing/worker-earnings/{task_id}` - Worker earnings calculation

### 5. **WhatsApp Integration**
- Webhook verification
- Text message processing
- Voice note processing (speech-to-text)
- Location sharing
- Automatic task creation from voice
- Task status notifications
- Worker assignment notifications
- Completion confirmations
- Payout notifications

**Routes:**
- `GET /api/v1/whatsapp/webhook` - Webhook verification
- `POST /api/v1/whatsapp/webhook` - Handle incoming messages
- `POST /api/v1/whatsapp/send-message` - Send message to customer
- `POST /api/v1/whatsapp/send-template-message` - Send template messages

### 6. **Real-Time Tracking**
- Check-in location tracking
- Check-out tracking with proof
- Task progress updates
- Location history
- WebSocket support for live updates

**Routes:**
- `POST /api/v1/tracking/{task_id}/check-in` - Worker check-in
- `POST /api/v1/tracking/{task_id}/check-out` - Worker check-out
- `GET /api/v1/tracking/{task_id}/location` - Get live location
- `WS /api/v1/tracking/ws/{task_id}` - WebSocket connection

### 7. **Payout Management**
- 75% immediate payout on completion
- 25% verification payout after fraud checks
- Pending payout tracking
- Worker earnings calculation
- Payout history
- Payout status checking
- Payment gateway integration ready (Stripe/Razorpay)

**Routes:**
- `GET /api/v1/payouts/worker/{worker_id}` - Get pending payouts
- `GET /api/v1/payouts/worker/{worker_id}/earnings` - Total earnings
- `GET /api/v1/payouts/worker/{worker_id}/history` - Payout history
- `POST /api/v1/payouts/process/{task_id}` - Process payout
- `POST /api/v1/payouts/{payout_id}/release-immediate` - Release 75%
- `POST /api/v1/payouts/{payout_id}/release-verification` - Release 25%
- `GET /api/v1/payouts/{payout_id}` - Get payout status

### 8. **Voice Processing Service**
- Audio transcription (OpenAI Whisper)
- Voice request classification (GPT-4)
- Task type detection (medicine, help, visit, cleaning)
- Urgency level extraction
- Effort level estimation

## Architecture

### Service Layer
Each service handles specific business logic:

- **TaskService** - Task creation, matching, updates
- **WorkerService** - Worker profile, task acceptance, tracking
- **PricingService** - Dynamic pricing calculations
- **PayoutService** - Payout management and earnings
- **WhatsAppService** - WhatsApp API integration
- **VoiceProcessingService** - Audio and NLP processing
- **NotificationService** - Customer and worker notifications

### Database Schema (Supabase PostgreSQL)

**Tables:**
- `customers` - Customer profiles
- `workers` - Worker profiles with verification
- `tasks` - Task records with status tracking
- `tracking` - Real-time location and event tracking
- `payouts` - Payment records
- `reviews` - Worker ratings and reviews
- `pricing_config` - Dynamic pricing configuration
- `whatsapp_messages` - Message history

### Security Features
- JWT authentication with token expiration
- Row-level security (RLS) policies
- WhatsApp webhook signature verification
- Password hashing with bcrypt
- User role-based access

## Setup & Deployment

### Prerequisites
- Python 3.11+
- Supabase account
- WhatsApp Business Account
- OpenAI API key
- (Optional) Stripe/Razorpay account for payments

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env

# Configure your environment variables
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
WHATSAPP_ACCESS_TOKEN=your_token
OPENAI_API_KEY=your_key
```

### Run Development Server
```bash
python -m uvicorn app.main:app --reload
```

### Access API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Usage Examples

### Create Task from Voice Note
```bash
curl -X POST http://localhost:8000/api/v1/tasks/create-from-voice \
  -H "Content-Type: multipart/form-data" \
  -F "customer_id=uuid" \
  -F "location_lat=28.6139" \
  -F "location_lng=77.2090" \
  -F "audio_file=@voice_note.m4a"
```

### Calculate Pricing
```bash
curl -X POST http://localhost:8000/api/v1/pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "medicine",
    "distance_km": 5.2,
    "effort_level": 2,
    "urgency_level": 3,
    "travel_time_minutes": 15.0
  }'
```

### Worker Accept Task
```bash
curl -X POST http://localhost:8000/api/v1/workers/{worker_id}/accept-task/{task_id}
```

### Check-In
```bash
curl -X POST http://localhost:8000/api/v1/workers/{worker_id}/check-in/{task_id} \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 28.6139,
    "lng": 77.2090
  }'
```

### Process Payout
```bash
curl -X POST http://localhost:8000/api/v1/payouts/process/{task_id}
```

## Integration Points

### WhatsApp Setup
1. Create WhatsApp Business Account
2. Get Phone Number ID and Access Token
3. Configure webhook URL: `https://your-domain/api/v1/whatsapp/webhook`
4. Set verify token matching `WHATSAPP_VERIFY_TOKEN` in .env
5. Subscribe to message events

### OpenAI Integration
1. Get API key from OpenAI
2. Set `OPENAI_API_KEY` in .env
3. Uses Whisper for audio transcription
4. Uses GPT-4 for task classification

### Supabase Setup
1. Create project and get URL + API key
2. Run migrations from `database/migrations/`
3. Enable RLS on sensitive tables
4. Configure authentication policies

## Performance Optimizations

- Database indexes on frequently queried fields
- Connection pooling with Supabase
- Async/await for non-blocking operations
- Worker matching algorithm optimized for distance
- Payout processing in background (ready for Celery)

## Future Enhancements

- [ ] Payment gateway integration (Stripe/Razorpay)
- [ ] Background task queue (Celery + Redis)
- [ ] SMS notifications (Twilio)
- [ ] Google Maps API integration
- [ ] Machine learning for surge pricing
- [ ] Admin dashboard API
- [ ] Dispute resolution system
- [ ] Analytics and reporting

## Error Handling

All endpoints return proper HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Server Error

## Testing

API can be tested using:
- Swagger UI at `/docs`
- cURL commands
- Postman (import OpenAPI spec)
- Python requests library

## Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review database schema in `database/migrations/`
3. Check `.env.example` for required variables
4. Enable debug logging: `DEBUG=True` in .env

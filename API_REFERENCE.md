{
  "info": {
    "name": "Eldercare Service System API",
    "description": "Complete API collection for WhatsApp-based eldercare service platform",
    "version": "1.0.0",
    "contact": {
      "name": "API Support",
      "url": "https://example.com"
    }
  },
  "baseUrl": "http://localhost:8000/api/v1",
  "endpoints": [
    {
      "name": "Authentication",
      "requests": [
        {
          "method": "POST",
          "url": "/auth/register/customer",
          "description": "Register a new customer",
          "body": {
            "phone_number": "+919876543210",
            "password": "SecurePassword123!"
          },
          "response": {
            "user_id": "uuid",
            "phone_number": "+919876543210",
            "user_type": "customer",
            "access_token": "jwt-token"
          }
        },
        {
          "method": "POST",
          "url": "/auth/register/worker",
          "description": "Register a new worker",
          "body": {
            "phone_number": "+919876543210",
            "password": "SecurePassword123!",
            "service_types": ["medicine", "help"]
          }
        },
        {
          "method": "POST",
          "url": "/auth/login",
          "description": "User login",
          "body": {
            "phone_number": "+919876543210",
            "password": "SecurePassword123!"
          }
        }
      ]
    },
    {
      "name": "Tasks",
      "requests": [
        {
          "method": "POST",
          "url": "/tasks/create",
          "description": "Create a new task",
          "headers": {
            "Authorization": "Bearer <token>"
          },
          "body": {
            "title": "Medicine Delivery",
            "description": "Deliver prescribed medications",
            "task_type": "medicine",
            "mode": "quick",
            "urgency_level": 3,
            "location": "123 Main St, City"
          }
        },
        {
          "method": "POST",
          "url": "/tasks/create-from-voice",
          "description": "Create task from voice note",
          "body": {
            "audio_file": "<base64-or-file>",
            "customer_phone": "+919876543210"
          }
        },
        {
          "method": "GET",
          "url": "/tasks/{task_id}",
          "description": "Get task details"
        },
        {
          "method": "PUT",
          "url": "/tasks/{task_id}",
          "description": "Update task status",
          "body": {
            "status": "in_progress"
          }
        },
        {
          "method": "POST",
          "url": "/tasks/{task_id}/cancel",
          "description": "Cancel a task"
        },
        {
          "method": "GET",
          "url": "/tasks/customer/{customer_id}",
          "description": "Get customer's tasks"
        }
      ]
    },
    {
      "name": "Workers",
      "requests": [
        {
          "method": "GET",
          "url": "/workers/{worker_id}",
          "description": "Get worker profile"
        },
        {
          "method": "PUT",
          "url": "/workers/{worker_id}/location",
          "description": "Update worker location",
          "body": {
            "latitude": 28.7041,
            "longitude": 77.1025
          }
        },
        {
          "method": "GET",
          "url": "/workers/{worker_id}/available-tasks",
          "description": "Get available tasks for worker"
        },
        {
          "method": "POST",
          "url": "/workers/{worker_id}/accept-task/{task_id}",
          "description": "Accept a task"
        },
        {
          "method": "POST",
          "url": "/workers/{worker_id}/check-in/{task_id}",
          "description": "Check in with proof photo",
          "body": {
            "proof_photo_url": "https://..."
          }
        },
        {
          "method": "POST",
          "url": "/workers/{worker_id}/check-out/{task_id}",
          "description": "Check out and complete task",
          "body": {
            "proof_photo_url": "https://..."
          }
        },
        {
          "method": "GET",
          "url": "/workers/{worker_id}/stats",
          "description": "Get worker statistics"
        }
      ]
    },
    {
      "name": "Pricing",
      "requests": [
        {
          "method": "POST",
          "url": "/pricing/calculate",
          "description": "Calculate task price",
          "body": {
            "service_type": "medicine",
            "distance_km": 5,
            "urgency_level": 3,
            "effort_level": 2
          }
        },
        {
          "method": "GET",
          "url": "/pricing/quick-mode/{service_type}",
          "description": "Get quick mode pricing"
        },
        {
          "method": "GET",
          "url": "/pricing/scheduled-mode/{service_type}",
          "description": "Get scheduled mode pricing"
        },
        {
          "method": "GET",
          "url": "/pricing/estimate/{task_id}",
          "description": "Get price estimate for task"
        },
        {
          "method": "GET",
          "url": "/pricing/worker-earnings/{task_id}",
          "description": "Get worker earnings for task"
        },
        {
          "method": "PUT",
          "url": "/pricing/config/{service_type}",
          "description": "Update pricing config (admin)",
          "body": {
            "base_price": 50,
            "distance_charge_per_km": 5,
            "effort_multiplier": 1.0
          }
        }
      ]
    },
    {
      "name": "Payouts",
      "requests": [
        {
          "method": "GET",
          "url": "/payouts/worker/{worker_id}",
          "description": "Get pending payouts"
        },
        {
          "method": "GET",
          "url": "/payouts/worker/{worker_id}/earnings",
          "description": "Get total earnings"
        },
        {
          "method": "GET",
          "url": "/payouts/worker/{worker_id}/history",
          "description": "Get payout history"
        },
        {
          "method": "POST",
          "url": "/payouts/process/{task_id}",
          "description": "Process payout for completed task"
        },
        {
          "method": "POST",
          "url": "/payouts/{payout_id}/release-immediate",
          "description": "Release immediate payout (75%)"
        },
        {
          "method": "POST",
          "url": "/payouts/{payout_id}/release-verification",
          "description": "Release verification payout (25%)"
        },
        {
          "method": "GET",
          "url": "/payouts/stats/pending",
          "description": "Get pending payout statistics"
        }
      ]
    },
    {
      "name": "WhatsApp",
      "requests": [
        {
          "method": "GET",
          "url": "/whatsapp/webhook",
          "description": "Webhook verification (GET)"
        },
        {
          "method": "POST",
          "url": "/whatsapp/webhook",
          "description": "Webhook for incoming messages",
          "body": {
            "object": "whatsapp_business_account",
            "entry": [
              {
                "changes": [
                  {
                    "value": {
                      "messages": [
                        {
                          "from": "919876543210",
                          "type": "text",
                          "text": {
                            "body": "Need medicine delivery"
                          }
                        }
                      ]
                    }
                  }
                ]
              }
            ]
          }
        },
        {
          "method": "POST",
          "url": "/whatsapp/send-message",
          "description": "Send message to user",
          "body": {
            "recipient_phone": "919876543210",
            "message_text": "Your task has been assigned"
          }
        },
        {
          "method": "POST",
          "url": "/whatsapp/send-template-message",
          "description": "Send template message",
          "body": {
            "recipient_phone": "919876543210",
            "template_name": "task_created",
            "variables": {
              "task_id": "123",
              "task_title": "Medicine Delivery"
            }
          }
        }
      ]
    },
    {
      "name": "Admin",
      "requests": [
        {
          "method": "GET",
          "url": "/admin/stats/overview",
          "description": "Get system overview statistics"
        },
        {
          "method": "GET",
          "url": "/admin/stats/tasks",
          "description": "Get task statistics",
          "params": {
            "days": 7
          }
        },
        {
          "method": "GET",
          "url": "/admin/stats/workers",
          "description": "Get worker statistics"
        },
        {
          "method": "GET",
          "url": "/admin/stats/revenue",
          "description": "Get revenue statistics",
          "params": {
            "days": 30
          }
        },
        {
          "method": "GET",
          "url": "/admin/tasks/detailed",
          "description": "Get detailed task list",
          "params": {
            "status": "completed",
            "limit": 50
          }
        },
        {
          "method": "POST",
          "url": "/admin/pricing-config/{service_type}",
          "description": "Update pricing configuration",
          "body": {
            "base_price": 50,
            "distance_charge": 5,
            "effort_multiplier": 1.0
          }
        }
      ]
    },
    {
      "name": "Worker Onboarding",
      "requests": [
        {
          "method": "POST",
          "url": "/onboarding/{worker_id}/submit-document",
          "description": "Submit verification document",
          "params": {
            "document_type": "id"
          },
          "body": {
            "document_file": "<file>"
          }
        },
        {
          "method": "GET",
          "url": "/onboarding/{worker_id}/verification-status",
          "description": "Get verification status"
        },
        {
          "method": "POST",
          "url": "/onboarding/{worker_id}/approve",
          "description": "Approve worker (admin)"
        },
        {
          "method": "POST",
          "url": "/onboarding/{worker_id}/reject",
          "description": "Reject worker application (admin)",
          "body": {
            "reason": "Document verification failed"
          }
        },
        {
          "method": "PUT",
          "url": "/onboarding/{worker_id}/profile",
          "description": "Update worker profile",
          "body": {
            "name": "John Doe",
            "email": "john@example.com",
            "service_types": ["medicine", "help"]
          }
        }
      ]
    }
  ],
  "authentication": {
    "type": "Bearer Token",
    "token_location": "Authorization header",
    "token_format": "Bearer <jwt-token>",
    "token_ttl": "24 hours"
  },
  "rates": {
    "base_price_medicine": 50,
    "base_price_help": 80,
    "base_price_visit": 100,
    "base_price_cleaning": 120,
    "distance_charge_per_km": 5,
    "worker_payout_immediate_percentage": 75,
    "worker_payout_verification_percentage": 25
  },
  "status_codes": {
    "200": "Success",
    "201": "Created",
    "400": "Bad Request",
    "401": "Unauthorized",
    "403": "Forbidden",
    "404": "Not Found",
    "500": "Internal Server Error"
  }
}

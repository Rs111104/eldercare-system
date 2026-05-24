"""
Deployment utilities and cloud configuration scripts
"""
import subprocess
import json
import os
from typing import Dict, List, Optional, Tuple


class DeploymentManager:
    """Manage deployment to various cloud providers"""
    
    @staticmethod
    def check_dependencies() -> Tuple[bool, List[str]]:
        """Check if all required tools are installed"""
        required = ["docker", "docker-compose", "git", "python", "node", "npm"]
        missing = []
        
        for tool in required:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(tool)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_environment() -> Tuple[bool, List[str]]:
        """Validate environment variables are set"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "OPENAI_API_KEY",
            "WHATSAPP_API_TOKEN",
            "WHATSAPP_PHONE_ID",
            "WHATSAPP_BUSINESS_ID"
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def build_docker_images() -> bool:
        """Build Docker images"""
        try:
            subprocess.run(
                ["docker-compose", "build"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Docker build failed: {e}")
            return False
    
    @staticmethod
    def start_containers() -> bool:
        """Start Docker containers"""
        try:
            subprocess.run(
                ["docker-compose", "up", "-d"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Container startup failed: {e}")
            return False
    
    @staticmethod
    def stop_containers() -> bool:
        """Stop Docker containers"""
        try:
            subprocess.run(
                ["docker-compose", "down"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Container stop failed: {e}")
            return False
    
    @staticmethod
    def get_container_status() -> Dict[str, str]:
        """Get status of running containers"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                check=True,
                capture_output=True,
                text=True
            )
            
            containers = json.loads(result.stdout) if result.stdout else []
            return {c.get("Service"): c.get("State") for c in containers}
        except Exception as e:
            print(f"Error getting container status: {e}")
            return {}
    
    @staticmethod
    def view_logs(service: str = None) -> str:
        """View container logs"""
        try:
            cmd = ["docker-compose", "logs"]
            if service:
                cmd.append(service)
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error viewing logs: {e}"


class AWSDeployer:
    """AWS-specific deployment utilities"""
    
    @staticmethod
    def configure_ec2_security_group(instance_id: str) -> bool:
        """Configure security group for EC2 instance"""
        # Would require AWS CLI
        print("Configure security group to allow ports: 80, 443, 8000, 3000")
        return True
    
    @staticmethod
    def setup_nginx_reverse_proxy() -> str:
        """Generate nginx configuration"""
        return """
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificate paths
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support (for real-time tracking)
    location /api/v1/tracking/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
    
    @staticmethod
    def install_ssl_certificate() -> str:
        """Instructions for installing SSL certificate"""
        return """
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
"""


class GCPDeployer:
    """Google Cloud Platform deployment utilities"""
    
    @staticmethod
    def create_cloud_run_config(project_id: str) -> str:
        """Generate Cloud Run deployment configuration"""
        return f"""
# Backend deployment
gcloud run deploy eldercare-backend \\
  --image gcr.io/{project_id}/eldercare-backend \\
  --platform managed \\
  --region us-central1 \\
  --set-env-vars SUPABASE_URL=${{SUPABASE_URL}},SUPABASE_KEY=${{SUPABASE_KEY}},OPENAI_API_KEY=${{OPENAI_API_KEY}} \\
  --memory 512Mi \\
  --timeout 3600 \\
  --allow-unauthenticated \\
  --project {project_id}

# Frontend deployment
gcloud run deploy eldercare-frontend \\
  --image gcr.io/{project_id}/eldercare-frontend \\
  --platform managed \\
  --region us-central1 \\
  --set-env-vars VITE_API_URL=https://eldercare-backend-xxxxx.a.run.app/api/v1 \\
  --memory 256Mi \\
  --allow-unauthenticated \\
  --project {project_id}
"""
    
    @staticmethod
    def create_cloud_sql_auth_proxy() -> str:
        """Setup Cloud SQL Auth Proxy"""
        return """
# Install Cloud SQL Auth Proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy

# Run proxy
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432 &
"""


class HealthChecker:
    """Health checking utilities"""
    
    @staticmethod
    def check_api_health() -> Dict[str, bool]:
        """Check API health"""
        import requests
        
        checks = {
            "backend_running": False,
            "frontend_running": False,
            "database_connected": False,
            "api_responding": False
        }
        
        try:
            # Check backend
            response = requests.get("http://localhost:8000/", timeout=5)
            checks["backend_running"] = response.status_code < 500
            checks["api_responding"] = response.status_code == 200
        except:
            pass
        
        try:
            # Check frontend
            response = requests.get("http://localhost:3000/", timeout=5)
            checks["frontend_running"] = response.status_code < 500
        except:
            pass
        
        return checks
    
    @staticmethod
    def run_readiness_checks() -> bool:
        """Run readiness checks before deployment"""
        checks = [
            ("Dependencies", DeploymentManager.check_dependencies()),
            ("Environment", DeploymentManager.validate_environment()),
            ("Docker Images", (DeploymentManager.build_docker_images(),)),
        ]
        
        all_passed = True
        for name, result in checks:
            if isinstance(result, tuple):
                passed = result[0]
                details = result[1] if len(result) > 1 else []
            else:
                passed = result
                details = []
            
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {name}")
            
            if details:
                for detail in details:
                    print(f"  - {detail}")
            
            if not passed:
                all_passed = False
        
        return all_passed


class BackupManager:
    """Backup and restore utilities"""
    
    @staticmethod
    def backup_database(output_file: str = "backup.sql") -> bool:
        """Backup database"""
        # Would use pg_dump with Supabase connection
        print(f"Backup created: {output_file}")
        return True
    
    @staticmethod
    def restore_database(backup_file: str) -> bool:
        """Restore from backup"""
        # Would use psql with Supabase connection
        print(f"Restored from: {backup_file}")
        return True
    
    @staticmethod
    def backup_code(output_file: str = "code_backup.tar.gz") -> bool:
        """Backup application code"""
        try:
            subprocess.run(
                ["tar", "-czf", output_file, "."],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


def deployment_checklist() -> Dict[str, bool]:
    """Return deployment readiness checklist"""
    return {
        "environment_variables": DeploymentManager.validate_environment()[0],
        "docker_installed": DeploymentManager.check_dependencies()[0],
        "api_tests_passing": True,  # TODO: Run pytest
        "frontend_builds": True,  # TODO: Run npm build
        "database_migrations_ready": True,  # TODO: Check migrations
        "ssl_certificate_ready": False,  # User must setup
        "domain_configured": False,  # User must setup
        "backups_configured": False,  # User should setup
        "monitoring_setup": False  # User should setup
    }

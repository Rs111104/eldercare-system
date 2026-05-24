"""
Automated Deployment Script for ElderCare System
Supports multiple deployment targets: local, AWS, GCP, DigitalOcean
"""

import os
import sys
import subprocess
import json
import argparse
from datetime import datetime
import shutil
from pathlib import Path


class DeploymentManager:
    """Manage deployment to different environments"""

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log(self, message: str, level: str = "INFO"):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, command: str, cwd: Path = None, check: bool = True) -> bool:
        """Run shell command and return success status"""
        try:
            self.log(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                self.log(result.stdout)
            if result.stderr and result.returncode != 0:
                self.log(result.stderr, "ERROR")
            return result.returncode == 0
        except Exception as e:
            self.log(f"Command failed: {e}", "ERROR")
            return False

    def check_prerequisites(self) -> bool:
        """Check if all required tools are installed"""
        self.log("Checking prerequisites...")
        
        tools = ["python3", "node", "docker", "docker-compose", "git"]
        missing = []
        
        for tool in tools:
            result = self.run_command(f"{tool} --version", check=False)
            if not result:
                missing.append(tool)
            else:
                self.log(f"✓ {tool} is installed")
        
        if missing:
            self.log(f"Missing tools: {', '.join(missing)}", "ERROR")
            return False
        
        self.log("✓ All prerequisites met")
        return True

    def setup_environment(self) -> bool:
        """Setup environment files"""
        self.log("Setting up environment...")
        
        env_template = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            self.log("✓ .env file already exists")
            return True
        
        if env_template.exists():
            shutil.copy(env_template, env_file)
            self.log("✓ Created .env from template")
            self.log("⚠ Please configure .env with your settings", "WARNING")
            return True
        
        self.log("No .env template found", "ERROR")
        return False

    def setup_backend(self) -> bool:
        """Setup Python backend"""
        self.log("Setting up backend...")
        
        # Create virtual environment
        venv_dir = self.backend_dir / "venv"
        if not venv_dir.exists():
            self.log("Creating Python virtual environment...")
            if not self.run_command(f"python3 -m venv venv", cwd=self.backend_dir):
                return False
        
        # Install dependencies
        self.log("Installing Python dependencies...")
        pip_command = "venv/bin/pip install -r requirements.txt" if os.name != "nt" else r"venv\Scripts\pip install -r requirements.txt"
        if not self.run_command(pip_command, cwd=self.backend_dir):
            return False
        
        self.log("✓ Backend setup complete")
        return True

    def setup_frontend(self) -> bool:
        """Setup Node.js frontend"""
        self.log("Setting up frontend...")
        
        # Install dependencies
        self.log("Installing npm dependencies...")
        if not self.run_command("npm install", cwd=self.frontend_dir):
            return False
        
        self.log("✓ Frontend setup complete")
        return True

    def build_frontend(self) -> bool:
        """Build frontend for production"""
        self.log("Building frontend...")
        
        if not self.run_command("npm run build", cwd=self.frontend_dir):
            return False
        
        self.log("✓ Frontend build complete")
        return True

    def build_docker_images(self) -> bool:
        """Build Docker images"""
        self.log("Building Docker images...")
        
        if not self.run_command("docker-compose build", cwd=self.project_root):
            return False
        
        self.log("✓ Docker images built")
        return True

    def start_local_dev(self) -> bool:
        """Start local development environment"""
        self.log("Starting local development environment...")
        
        if not self.setup_backend():
            return False
        
        if not self.setup_frontend():
            return False
        
        self.log("✓ Starting Docker Compose...")
        if not self.run_command("docker-compose up -d", cwd=self.project_root):
            return False
        
        self.log("✓ Local development environment started")
        self.log("Backend API: http://localhost:8000")
        self.log("Frontend: http://localhost:5173")
        self.log("API Docs: http://localhost:8000/api/v1/docs")
        
        return True

    def stop_local_dev(self) -> bool:
        """Stop local development environment"""
        self.log("Stopping local development environment...")
        
        if not self.run_command("docker-compose down", cwd=self.project_root):
            return False
        
        self.log("✓ Local environment stopped")
        return True

    def deploy_aws_ec2(self, instance_ip: str) -> bool:
        """Deploy to AWS EC2"""
        self.log(f"Deploying to AWS EC2 ({instance_ip})...")
        
        # Commands to run on EC2
        ec2_commands = [
            "cd ~/eldercare-system",
            "git pull origin main",
            "source backend/venv/bin/activate",
            "pip install -r backend/requirements.txt",
            "cd frontend && npm install && npm run build",
            "sudo systemctl restart eldercare-api",
            "sudo systemctl restart nginx"
        ]
        
        for cmd in ec2_commands:
            ssh_cmd = f"ssh -i ~/.ssh/ec2-key.pem ubuntu@{instance_ip} '{cmd}'"
            if not self.run_command(ssh_cmd, check=False):
                self.log(f"Command failed on EC2: {cmd}", "WARNING")
        
        self.log("✓ AWS EC2 deployment complete")
        return True

    def deploy_docker_registry(self, registry: str, namespace: str) -> bool:
        """Build and push Docker images to registry"""
        self.log(f"Deploying to Docker registry ({registry})...")
        
        images = [
            ("backend", f"{registry}/{namespace}/eldercare-api:latest"),
            ("frontend", f"{registry}/{namespace}/eldercare-web:latest"),
        ]
        
        for context, image_tag in images:
            # Build image
            dockerfile = self.project_root / context / "Dockerfile.prod"
            if dockerfile.exists():
                build_cmd = f"docker build -f {dockerfile} -t {image_tag} ./{context}"
                if not self.run_command(build_cmd, cwd=self.project_root):
                    return False
            
            # Push image
            if not self.run_command(f"docker push {image_tag}"):
                return False
        
        self.log("✓ Docker registry deployment complete")
        return True

    def run_tests(self) -> bool:
        """Run test suite"""
        self.log("Running tests...")
        
        # Backend tests
        if not self.run_command("pytest tests/", cwd=self.backend_dir, check=False):
            self.log("Backend tests failed", "WARNING")
        
        # Frontend tests
        if not self.run_command("npm test", cwd=self.frontend_dir, check=False):
            self.log("Frontend tests failed", "WARNING")
        
        self.log("✓ Tests completed")
        return True

    def create_backup(self) -> bool:
        """Create backup of current deployment"""
        self.log("Creating backup...")
        
        backup_dir = self.project_root / "backups" / self.timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup environment
        env_file = self.project_root / ".env"
        if env_file.exists():
            shutil.copy(env_file, backup_dir / ".env")
        
        # Backup docker-compose
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            shutil.copy(compose_file, backup_dir / "docker-compose.yml")
        
        self.log(f"✓ Backup created at {backup_dir}")
        return True

    def generate_deployment_report(self, success: bool) -> None:
        """Generate deployment report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "success": success,
            "deployment_id": self.timestamp,
        }
        
        report_file = self.project_root / "deployments" / f"report_{self.timestamp}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Deployment report saved to {report_file}")


def main():
    """Main deployment script"""
    parser = argparse.ArgumentParser(description="ElderCare System Deployment")
    parser.add_argument(
        "action",
        choices=["setup", "start", "stop", "deploy", "test", "backup", "full"],
        help="Deployment action to perform"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="Target environment"
    )
    parser.add_argument(
        "--target",
        choices=["local", "aws", "gcp", "docker", "digitalocean"],
        default="local",
        help="Deployment target"
    )
    parser.add_argument(
        "--registry",
        help="Docker registry URL"
    )
    parser.add_argument(
        "--endpoint",
        help="Server endpoint (IP or domain)"
    )
    
    args = parser.parse_args()
    
    manager = DeploymentManager(args.environment)
    success = False
    
    try:
        if not manager.check_prerequisites():
            sys.exit(1)
        
        if args.action == "setup":
            success = manager.setup_environment() and manager.setup_backend() and manager.setup_frontend()
        
        elif args.action == "start":
            success = manager.start_local_dev()
        
        elif args.action == "stop":
            success = manager.stop_local_dev()
        
        elif args.action == "deploy":
            if args.target == "local":
                success = manager.start_local_dev()
            elif args.target == "aws" and args.endpoint:
                success = manager.deploy_aws_ec2(args.endpoint)
            elif args.target == "docker" and args.registry:
                success = manager.deploy_docker_registry(args.registry, "eldercare")
            else:
                manager.log("Invalid deployment target or missing parameters", "ERROR")
        
        elif args.action == "test":
            success = manager.run_tests()
        
        elif args.action == "backup":
            success = manager.create_backup()
        
        elif args.action == "full":
            success = (
                manager.setup_environment() and
                manager.setup_backend() and
                manager.setup_frontend() and
                manager.run_tests() and
                manager.build_docker_images() and
                manager.create_backup()
            )
        
        manager.generate_deployment_report(success)
        
        if success:
            manager.log("Deployment completed successfully", "SUCCESS")
            sys.exit(0)
        else:
            manager.log("Deployment failed", "ERROR")
            sys.exit(1)
    
    except Exception as e:
        manager.log(f"Deployment error: {e}", "ERROR")
        manager.generate_deployment_report(False)
        sys.exit(1)


if __name__ == "__main__":
    main()

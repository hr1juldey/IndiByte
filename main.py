import subprocess
import signal
import sys
import os
import time
from pathlib import Path

def start_backend():
    """Start the backend service on port 8000."""
    print("🚀 Starting Bytelense backend service...")

    backend_dir = Path.home() / "Documents/Projects/IndiByte/IndiByte/Bytelense/backend"

    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return None

    # Start the backend server
    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:socket_app",
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    print(f"✅ Backend started with PID {proc.pid}")
    return proc

def start_frontend():
    """Start the frontend service on port 5173."""
    print("🌐 Starting Bytelense frontend service...")

    frontend_dir = Path.home() / "Documents/Projects/IndiByte/IndiByte/Bytelense/frontend"

    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return None

    # Start the frontend server
    proc = subprocess.Popen([
        "pnpm", "run", "dev"
    ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    print(f"✅ Frontend started with PID {proc.pid}")
    return proc

def stop_process(proc, service_name):
    """Stop a running process."""
    if proc:
        print(f"🛑 Stopping {service_name}...")
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
        except subprocess.TimeoutExpired:
            print(f"⚠️ {service_name} didn't stop gracefully, force killing...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already terminated
        except ProcessLookupError:
            pass  # Process already terminated
        print(f"✅ {service_name} stopped")

def main():
    """Service manager for Bytelense - Food Label Scanner."""
    print("🍽️ Bytelense - Food Label Scanner Service Manager")
    print("=" * 50)
    print("Commands:")
    print("  start    - Start both backend (port 8000) and frontend (port 5173)")
    print("  stop     - Stop both services")
    print("  restart  - Restart both services")
    print("  status   - Show service status")
    print("  help     - Show this help")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\n❌ No command provided")
        print("Usage: python main.py [start|stop|restart|status|help]")
        return

    command = sys.argv[1].lower()

    if command == "start":
        print("\nStarting services...")
        backend_proc = start_backend()
        time.sleep(2)  # Give backend a moment to start
        frontend_proc = start_frontend()

        if backend_proc or frontend_proc:
            print(f"\nServices started successfully!")
            print("- Backend: http://localhost:8000")
            print("- Frontend: http://localhost:5173")
            print("\nPress Ctrl+C to stop services")

            try:
                # Keep the main process alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nReceived interrupt signal, stopping services...")
                stop_process(backend_proc, "Backend")
                stop_process(frontend_proc, "Frontend")
                print("👋 Services stopped. Goodbye!")

    elif command == "stop":
        print("\nFinding and stopping services...")

        # Find running Bytelense processes
        import psutil

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline and 'app.main:socket_app' in cmdline:
                    print(f"Stopping backend process {proc.info['pid']}")
                    proc.kill()
                elif 'pnpm' in proc.info['name'] and 'dev' in cmdline:
                    print(f"Stopping frontend process {proc.info['pid']}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        print("✅ All Bytelense services stopped")

    elif command == "restart":
        # First stop existing processes
        print("\nFinding and stopping existing services...")

        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline and 'app.main:socket_app' in cmdline:
                    print(f"Stopping backend process {proc.info['pid']}")
                    proc.kill()
                elif 'pnpm' in proc.info['name'] and 'dev' in cmdline:
                    print(f"Stopping frontend process {proc.info['pid']}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        time.sleep(2)

        # Then start services
        print("\nStarting services...")
        backend_proc = start_backend()
        time.sleep(2)  # Give backend a moment to start
        frontend_proc = start_frontend()

        print(f"\nServices restarted successfully!")
        print("- Backend: http://localhost:8000")
        print("- Frontend: http://localhost:5173")

    elif command == "status":
        print("\nChecking Bytelense service status...")

        import psutil
        backend_running = False
        frontend_running = False

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'uvicorn' in cmdline and 'app.main:socket_app' in cmdline:
                    print(f"✅ Backend is running (PID: {proc.info['pid']})")
                    backend_running = True
                elif 'pnpm' in proc.info['name'] and 'dev' in cmdline:
                    print(f"✅ Frontend is running (PID: {proc.info['pid']})")
                    frontend_running = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if not backend_running:
            print("❌ Backend is NOT running")

        if not frontend_running:
            print("❌ Frontend is NOT running")

    elif command == "help":
        print("\n📖 HELP - Bytelense Service Manager")
        print("\nThis service manager controls the Bytelense food label scanning application.")
        print("\nSERVICES:")
        print("  Backend: Processes food label images with OCR (port 8000)")
        print("  Frontend: Web interface for scanning and displaying results (port 5173)")
        print("\nCOMMANDS:")
        print("  start     Starts both backend and frontend services")
        print("  stop      Stops all Bytelense services")
        print("  restart   Stops and starts all services")
        print("  status    Checks the status of both services")
        print("\nThe services will remain running until you press Ctrl+C to stop them.")
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Available commands: start, stop, restart, status, help")


if __name__ == "__main__":
    main()

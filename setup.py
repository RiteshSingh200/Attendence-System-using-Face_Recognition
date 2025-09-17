import subprocess
import sys
import os

def install_requirements():
    if os.path.exists("requirements.txt"):
        print("🚀 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    else:
        print("⚠️ requirements.txt not found!")

if __name__ == "__main__":
    install_requirements()
    print("\nSetup complete! You can now run your Flask app with:")
    print("python app.py")

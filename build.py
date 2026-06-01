import subprocess
import sys
import os

def build():
    print("Starting build process...")
    
    # Ensure dependencies are installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # PyInstaller command
    # --onefile: bundle into a single executable
    # --name: output filename
    # --clean: clean cache
    # --noconfirm: overwrite existing
    # --distpath: output directory
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console",
        "--name=WinCleaner",
        "--clean",
        "--noconfirm",
        "--distpath=./dist",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild successful! Executable located in /dist folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")

if __name__ == "__main__":
    build()

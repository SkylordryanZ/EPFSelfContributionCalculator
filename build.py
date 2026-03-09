import os
import sys
import subprocess

def main():
    python_dir = os.path.dirname(sys.executable)
    vc1 = os.path.join(python_dir, "vcruntime140.dll")
    vc2 = os.path.join(python_dir, "vcruntime140_1.dll")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--windowed",
        "--name", "EPFSelfContributionCalc",
        "--clean",
    ]
    
    if os.path.exists(vc1):
        cmd.extend(["--add-binary", f"{vc1};."])
    if os.path.exists(vc2):
        cmd.extend(["--add-binary", f"{vc2};."])
        
    cmd.append("app.py")
    
    print("Running PyInstaller with additional DLLs if present...")
    print("Command:", " ".join(cmd))
    
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()

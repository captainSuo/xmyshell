import os
import sys
import time
import subprocess

def xmyshell_update(version: str | None = None) -> None:
    if os.name == "nt":
        subprocess.run("taskkill /F /IM xmyshell.exe", shell=True)
    else:
        subprocess.run(["pkill", "-f", "-x", "xmyshell"])

    time.sleep(1)

    install_args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "xmyshell" + (f"=={version}" if version else ""),
    ]
    print()
    returncode = subprocess.run(install_args).returncode
    print("Press <Enter> to continue ...", end="")
    sys.exit(returncode)

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) >= 2 else None
    xmyshell_update(version)

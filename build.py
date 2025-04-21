# build.py
import platform
import subprocess
import shutil

os_name = platform.system().lower()

dist_folder = f"dist_{os_name}"
build_folder = f"build_{os_name}"

shutil.rmtree(dist_folder, ignore_errors=True)
shutil.rmtree(build_folder, ignore_errors=True)

cmd = [
    "pyinstaller",
    "main.py",
    "--onefile",
    f"--distpath={dist_folder}",
    f"--workpath={build_folder}"
]

subprocess.run(cmd)

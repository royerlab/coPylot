import subprocess
import sys


if __name__ == '__main__':

    print(f"main proc version: {sys.version}")

    result = subprocess.run(
        "conda deactivate && conda run -n cp38  python camera.py",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")

    print(f"main proc version: {sys.version}")

import os
import subprocess
import sys


def main() -> int:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_app = os.path.join(root_dir, "backend", "app.py")
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")

    if not os.path.exists(backend_app):
        print("Error: backend app not found at backend/app.py")
        return 1

    current_python = os.path.normcase(os.path.abspath(sys.executable))
    venv_python_norm = os.path.normcase(os.path.abspath(venv_python))

    # Always prefer the project virtual environment when available.
    if os.path.exists(venv_python) and current_python != venv_python_norm:
        return subprocess.call([venv_python, backend_app])

    return subprocess.call([sys.executable, backend_app])


if __name__ == "__main__":
    raise SystemExit(main())

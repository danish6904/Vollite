@echo off
"%~dp0..\.venv\Scripts\python.exe" -c "import sys; from volatility3.cli import main; sys.exit(main())" %*
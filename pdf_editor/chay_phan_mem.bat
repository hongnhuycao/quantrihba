@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -c "import pymupdf" 2>nul || (echo Dang cai thu vien PyMuPDF... & python -m pip install -r requirements.txt)
start "" pythonw pdf_editor.py %*

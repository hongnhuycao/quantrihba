@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name TrinhSuaPDF --add-data "fonts;fonts" pdf_editor.py
echo.
echo Xong! File chay nam o: dist\TrinhSuaPDF.exe
pause

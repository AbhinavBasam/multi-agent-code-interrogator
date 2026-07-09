@echo off
title Multi-Agent Code Interrogator - Web UI
echo ===================================================
echo     Multi-Agent Code Interrogator - Demo Mode
echo ===================================================
echo.
echo Activating Virtual Environment...
call .\venv\Scripts\activate.bat

echo.
echo Starting the Streamlit Web Interface...
echo Please wait while the server boots up...
echo.
streamlit run app.py

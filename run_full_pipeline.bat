@echo off
title Multi-Agent Code Interrogator - Backend Pipeline
echo ===================================================
echo     Multi-Agent Code Interrogator - Backend Pipeline
echo ===================================================
echo.

set RESUME_FILE=%1
if "%RESUME_FILE%"=="" set RESUME_FILE=resume.pdf

echo Activating Virtual Environment...
call .\venv\Scripts\activate.bat

echo.
echo Target Resume: %RESUME_FILE%
echo.

echo [1/4] Running Phase 1 (PDF Parsing)...
python phase_1.py "%RESUME_FILE%"
python phase_1_part2.py "%RESUME_FILE%"
echo.

echo [2/4] Running Phase 2 (GitHub Retrieval ^& Chunking)...
python phase_2.py
echo.

echo [3/4] Running Phase 3 (Vectorization Engine)...
python phase_3.py
echo.

echo [4/4] Running Phase 4 (Judge Agent Evaluation)...
python phase_4.py
echo.

echo ===================================================
echo Pipeline Complete! The JSON audit report is updated.
echo You can now run start_demo.bat to view the results.
echo ===================================================
pause

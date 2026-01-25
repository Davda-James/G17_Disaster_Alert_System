@echo off
REM =====================================
REM DisasterWatch Complete Test Suite
REM =====================================

echo.
echo ==========================================
echo     DisasterWatch Complete Test Suite
echo ==========================================
echo.

echo [1/2] Running Backend Tests...
echo ------------------------------------------
cd /d d:\Sem6_course\SE\Ass1\DAS_Project\tests\backend
pytest -v --tb=short

echo.
echo [2/2] Running Frontend Tests...
echo ------------------------------------------
cd /d d:\Sem6_course\SE\Ass1\DAS_Project\Frontend
call npm run test

echo.
echo ==========================================
echo             Test Summary
echo ==========================================
echo   Backend Tests:  88 tests
echo   Frontend Tests: 21 tests
echo   Total:          109 tests
echo ==========================================
echo.
pause

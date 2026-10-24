@echo off
title VYAS Astrology System - Windows EXE Builder
echo ========================================================
echo  VYAS - Vedic Yield Astrology System
echo  EXE Builder (Commercial Edition)
echo  Author: Pt. Nikhil Vyas, MA (Astrology)
echo  Phone: 9414121172 | Email: inikhilvyas@gmail.com
echo ========================================================
echo.
echo Installing PyInstaller and pywebview if needed...
pip install pyinstaller pywebview
echo.
echo Building Standalone Windows Executable (VYAS_Astrology.exe)...
pyinstaller --noconfirm --onedir --windowed --add-data "vyas_astrology_system.html;." --add-data "watermarked_img_1944548633781185789.jpg;." --name "VYAS_Astrology" app_desktop.py
echo.
echo ========================================================
echo  BUILD COMPLETE!
echo  Your standalone EXE is in: dist\VYAS_Astrology\VYAS_Astrology.exe
echo ========================================================
pause

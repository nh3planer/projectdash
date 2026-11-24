; Inno-Setup-Skript für den ProjectDash-Windows-Installer
; Voraussetzung: dist\ProjectDashClient.exe und dist\ProjectDashServer.exe
; wurden mit build_windows.bat erzeugt. Inno Setup 6 installieren,
; dann diese Datei kompilieren (setup erzeugt Setup\ProjectDashSetup.exe)

[Setup]
AppId={{B7F3A2C1-6D4E-4C9B-9A11-PROJECTDASH}}
AppName=ProjectDash
AppVersion=1.0.0
AppPublisher=ProjectDash
DefaultDirName={autopf}\ProjectDash
DefaultGroupName=ProjectDash
OutputDir=Setup
OutputBaseFilename=ProjectDashSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Files]
Source: "dist\ProjectDashClient.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ProjectDashServer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ProjectDash Client"; Filename: "{app}\ProjectDashClient.exe"
Name: "{group}\ProjectDash Server"; Filename: "{app}\ProjectDashServer.exe"
Name: "{commondesktop}\ProjectDash"; Filename: "{app}\ProjectDashClient.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Zusätzliche Symbole:"

[Run]
Filename: "{app}\ProjectDashClient.exe"; Description: "ProjectDash jetzt starten"; Flags: nowait postinstall skipifsilent

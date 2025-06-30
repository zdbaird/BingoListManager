; Save as EntryManagerInstaller.iss and open in Inno Setup Compiler
[Setup]
AppName=Entry Manager
AppVersion=1.0
DefaultDirName={pf}\EntryManager
DefaultGroupName=Entry Manager
UninstallDisplayIcon={app}\app.exe
OutputDir=.
OutputBaseFilename=EntryManagerSetup

[Files]
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Entry Manager"; Filename: "{app}\app.exe"
Name: "{desktop}\Entry Manager"; Filename: "{app}\app.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\app.exe"; Description: "Launch Entry Manager"; Flags: nowait postinstall skipifsilent
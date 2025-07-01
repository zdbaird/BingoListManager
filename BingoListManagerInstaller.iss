; BingoListManager Inno Setup Script

[Setup]
AppName=Bingo List Manager
AppVersion=1.0
DefaultDirName={pf}\BingoListManager
DefaultGroupName=Bingo List Manager
UninstallDisplayIcon={app}\BingoListManager.ico
OutputDir=.
OutputBaseFilename=BingoListManagerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "release_files\BingoListManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release_files\BingoListManager.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "release_files\lists\*"; DestDir: "{app}\lists"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Bingo List Manager"; Filename: "{app}\BingoListManager.exe"; IconFilename: "{app}\BingoListManager.ico"
Name: "{group}\Uninstall Bingo List Manager"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Bingo List Manager"; Filename: "{app}\BingoListManager.exe"; IconFilename: "{app}\BingoListManager.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\BingoListManager.exe"; Description: "Launch Bingo List Manager"; Flags: nowait postinstall skipifsilent
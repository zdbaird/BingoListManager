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

[Code]
var
  ListsDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  ListsDirPage := CreateInputDirPage(wpSelectDir,
    'Select Lists Folder', 'Where should lists be stored?',
    'Select the folder where your lists will be saved. You can change this later in the app settings.',
    False, '');
  ListsDirPage.Add('');
  ListsDirPage.Values[0] := ExpandConstant('{userdocs}\EntryManagerLists');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    SaveStringToFile(ExpandConstant('{app}\lists_folder.txt'), ListsDirPage.Values[0], False);
end;
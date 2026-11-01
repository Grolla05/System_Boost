#define AppName "System Boost"
#define AppPublisher "Felipe Grolla"
#define AppExeName "System Boost.exe"

[Setup]
AppId={{E7E3BE91-8A42-4E2F-9D62-79EA83D1A021}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\System Boost
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir={#SourceDir}
OutputBaseFilename=System Boost Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}
Uninstallable=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#SourceDir}\System Boost.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\System Boost"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\System Boost"; Filename: "{app}\{#AppExeName}"

[Run]
; Launched through the desktop shortcut with shellexec: postinstall entries run as the original,
; unelevated user, and the exe requires Administrator (--uac-admin), so a direct CreateProcess
; would fail with error 740.
Filename: "{autodesktop}\System Boost.lnk"; Description: "Iniciar o System Boost"; Flags: postinstall shellexec nowait skipifsilent

[Code]
// Versions up to 0.1.0 installed per user; that copy must not survive next to this one.
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldUninstaller: String;
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    OldUninstaller := ExpandConstant('{localappdata}\Programs\System Boost\unins000.exe');
    if FileExists(OldUninstaller) then
      Exec(OldUninstaller, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

// Runs before the files go away: the exe is what knows how to restore the saved values.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if (CurUninstallStep = usUninstall) and not UninstallSilent
    and FileExists(ExpandConstant('{localappdata}\WinCleaner\tweaks_state.json'))
    and (MsgBox('Desfazer os ajustes aplicados pelo System Boost antes de remover?', mbConfirmation, MB_YESNO) = IDYES) then
  begin
    if not Exec(ExpandConstant('{app}\{#AppExeName}'), 'undo --all', '', SW_SHOW, ewWaitUntilTerminated, ResultCode)
      or (ResultCode <> 0) then
      MsgBox('Alguns ajustes não foram desfeitos. Depois de remover, restaure-os pelas configurações do Windows.', mbError, MB_OK);
  end;
end;

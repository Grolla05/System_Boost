#define AppName "System Boost"
#define AppPublisher "Felipe Grolla"
#define AppExeName "System Boost.exe"

[Setup]
AppId={{E7E3BE91-8A42-4E2F-9D62-79EA83D1A021}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\System Boost
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
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
; Launched through the desktop shortcut with shellexec: the exe requires Administrator (--uac-admin)
; while the setup runs unelevated, so a direct CreateProcess would fail with error 740.
Filename: "{autodesktop}\System Boost.lnk"; Description: "Iniciar o System Boost"; Flags: postinstall shellexec nowait skipifsilent

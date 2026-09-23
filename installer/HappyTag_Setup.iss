; ============================================================================
; Inno Setup script for HappyTag (Windows)
; ----------------------------------------------------------------------------
; Prerequisites:
;   1. Build the exe first:  pyinstaller HappyTag_Win.spec
;      -> produces dist\HappyTag.exe
;   2. Install Inno Setup 6 from https://jrsoftware.org/isdl.php
;   3. Compile this script (right-click -> Compile, or run build_installer.bat)
;      -> produces installer_output\HappyTag_Setup.exe
; ============================================================================

#define MyAppName "HappyTag"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "HappyTag"
#define MyAppExeName "HappyTag.exe"

[Setup]
; A fixed AppId lets future installers recognise and upgrade this app.
; Generate your own once via Tools -> Generate GUID in the Inno IDE and keep it.
AppId={{8F3A2B7C-9D4E-4C1A-B6F5-2E8D1A0C9B44}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Install into the current user's profile: "C:\Users\<user>\AppData\Local\Programs\HappyTag"
; (no admin rights needed - matches how VS Code / Chrome per-user installs work)
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
; Per-user install: never ask for admin elevation
PrivilegesRequired=lowest
; Where the built wizard exe goes
OutputDir=installer_output
OutputBaseFilename=HappyTag_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Icon shown in the wizard / Add-Remove Programs
SetupIconFile=..\logo\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; Only 64-bit Windows
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Optional desktop shortcut (ticked by default; user can untick)
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; The PyInstaller one-file build output
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop shortcut (only if the user kept the task ticked)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch the app on the final wizard page
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

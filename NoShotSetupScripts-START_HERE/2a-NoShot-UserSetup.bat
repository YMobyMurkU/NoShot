powershell.exe /c clear;Write-Host 'Creating Python Virtual Env.';py -m venv .\NoShotVirtEnv;.\NoShotVirtEnv\Scripts\activate.bat;Write-Host 'Updating Virtual Envs Pip and SetupTools Packages';py -m pip install --upgrade pip setuptools;Write-Host 'Installing Packages to Virtual Env';py -m pip install requests tailer Pillow PyQt5 PyQt5-sip PyQt5-stubs pytesseract


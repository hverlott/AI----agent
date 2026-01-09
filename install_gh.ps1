[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$uri = 'https://github.com/cli/cli/releases/latest/download/gh-windows-amd64.msi'
$out = Join-Path $env:TEMP 'gh_installer.msi'
Write-Host "Downloading $uri to $out"
Invoke-WebRequest -Uri $uri -OutFile $out
Write-Host "Installing $out"
Start-Process msiexec -ArgumentList '/i', $out, '/qn', '/norestart' -Wait -NoNewWindow
Write-Host 'Installed, checking version...'
gh --version

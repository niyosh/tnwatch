<#
  Refreshes the official data.gov.in figures (NCRB crime totals) and publishes them.

  data.gov.in refuses connections from GitHub's servers, so this one step runs on a computer in India.
  NCRB publishes once a year, so running it about once a year is enough; the site keeps the figures.

  From the project folder:   powershell -ExecutionPolicy Bypass -File scripts\update_official.ps1
  The API key is asked for at a hidden prompt and is not saved anywhere.
#>
Set-Location (Split-Path $PSScriptRoot -Parent)
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) { $gh = "C:\Program Files\GitHub CLI\gh.exe" }

function Stop-OnError($what) {
    if ($LASTEXITCODE -ne 0) { Write-Host "Stopped: $what failed." -ForegroundColor Red; exit 1 }
}

Write-Host "1/4  Getting the latest data from GitHub..."
git fetch -q origin data; Stop-OnError "downloading the data branch"
if (Test-Path data) { Remove-Item -Recurse -Force data }
New-Item -ItemType Directory data | Out-Null
git archive --format=tar -o data.tar FETCH_HEAD; Stop-OnError "unpacking the data"
tar -xf data.tar -C data; Stop-OnError "unpacking the data"
Remove-Item data.tar

$secure = Read-Host "2/4  Paste your data.gov.in API key (hidden, not saved)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$env:DATA_GOV_IN_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

Write-Host "3/4  Fetching the official figures..."
python scripts/fetch_data.py --mode official
$fetched = $LASTEXITCODE
Remove-Item Env:\DATA_GOV_IN_API_KEY
if ($fetched -ne 0) { Write-Host "Stopped: the fetch failed." -ForegroundColor Red; exit 1 }

Write-Host "4/4  Publishing..."
Push-Location data
git init -q -b data
git add -A
git -c user.name="tn-watch-bot" -c user.email="actions@users.noreply.github.com" commit -q -m "Official data update"
git push -q -f https://github.com/niyosh/tnwatch.git data
$pushed = $LASTEXITCODE
Remove-Item -Recurse -Force .git
Pop-Location
if ($pushed -ne 0) { Write-Host "Stopped: publishing failed." -ForegroundColor Red; exit 1 }

# rebuild the site from the updated data (news stays as it is until the next hourly run)
& $gh workflow run update.yml --repo niyosh/tnwatch -f mode=hourly | Out-Null
Write-Host "Done. The site shows the official figures in a few minutes." -ForegroundColor Green

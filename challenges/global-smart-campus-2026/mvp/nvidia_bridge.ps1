$ErrorActionPreference = 'Stop'
$key = [Environment]::GetEnvironmentVariable('NVIDIA_API_KEY','User')
if (-not $key) { $key = $env:NVIDIA_API_KEY }
if (-not $key) { throw 'NVIDIA_API_KEY is not configured.' }

$body = [Console]::In.ReadToEnd()
if (-not $body) { throw 'Request body is empty.' }

$headers = @{
  Authorization = "Bearer $key"
  'Content-Type' = 'application/json'
  Accept = 'application/json'
  'User-Agent' = 'HAL-Campus-Evidence-Desk/0.2'
}
$response = Invoke-WebRequest -UseBasicParsing `
  -Headers $headers `
  -Uri 'https://integrate.api.nvidia.com/v1/chat/completions' `
  -Method Post `
  -Body $body `
  -TimeoutSec 75
$response.Content

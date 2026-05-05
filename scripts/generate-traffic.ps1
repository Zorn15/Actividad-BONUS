# Script de trafico PowerShell
# Genera requests aleatorios contra los endpoints de la API

param(
    [string]$BaseUrl = "http://localhost:3000",
    [int]$DurationSeconds = 0,        # 0 = infinito
    [int]$DelayMinMs = 100,
    [int]$DelayMaxMs = 600
)

$ErrorActionPreference = "SilentlyContinue"

$endpoints = @(
    @{ Method = "GET";  Path = "/";                 Weight = 5 },
    @{ Method = "GET";  Path = "/api/datos";        Weight = 8 },
    @{ Method = "GET";  Path = "/api/lento";        Weight = 1 },
    @{ Method = "GET";  Path = "/api/usuarios";     Weight = 6 },
    @{ Method = "GET";  Path = "/api/usuarios/1";   Weight = 4 },
    @{ Method = "GET";  Path = "/api/usuarios/2";   Weight = 3 },
    @{ Method = "GET";  Path = "/api/usuarios/999"; Weight = 2 },  # 404
    @{ Method = "POST"; Path = "/api/usuarios";     Weight = 2 },
    @{ Method = "GET";  Path = "/api/error";        Weight = 3 },
    @{ Method = "GET";  Path = "/health";           Weight = 2 }
)

$pool = @()
foreach ($e in $endpoints) {
    for ($i = 0; $i -lt $e.Weight; $i++) { $pool += $e }
}

Write-Host "Generando trafico contra $BaseUrl"
Write-Host ("Duracion: " + (&{ if ($DurationSeconds -le 0) { "infinita" } else { "$DurationSeconds s" } }))
Write-Host "Detener con Ctrl+C"
Write-Host ""

$start = Get-Date
$count = 0
$ok    = 0
$fail  = 0

while ($true) {
    if ($DurationSeconds -gt 0 -and ((Get-Date) - $start).TotalSeconds -ge $DurationSeconds) { break }

    $ep  = $pool | Get-Random
    $url = "$BaseUrl$($ep.Path)"
    $count++

    try {
        if ($ep.Method -eq "POST") {
            $body = @{ name = "user-$([Guid]::NewGuid().ToString().Substring(0,6))"; role = "user" } | ConvertTo-Json
            $resp = Invoke-WebRequest -Uri $url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10 -UseBasicParsing
        } else {
            $resp = Invoke-WebRequest -Uri $url -Method $ep.Method -TimeoutSec 10 -UseBasicParsing
        }
        $status = $resp.StatusCode
        $ok++
    } catch {
        $status = "ERR"
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        $fail++
    }

    Write-Host ("[{0,4}] {1,-4} {2,-25} -> {3}" -f $count, $ep.Method, $ep.Path, $status)

    Start-Sleep -Milliseconds (Get-Random -Minimum $DelayMinMs -Maximum $DelayMaxMs)
}

Write-Host ""
Write-Host "Total: $count  OK: $ok  Fallidos: $fail"

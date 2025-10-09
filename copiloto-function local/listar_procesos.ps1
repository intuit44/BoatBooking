# Este script de PowerShell lista los procesos activos

Get-Process | Select-Object Name, Id, CPU | Format-Table -AutoSize
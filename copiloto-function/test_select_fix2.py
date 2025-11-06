from command_fixers.auto_fixers import apply_auto_fixes

# Test: Format-Table sin -Width (como genera el agente)
cmd = 'powershell -Command "Get-Content \'C:\\test.py\' | Select-String -Pattern \'def buscar\' -Context 0,10 | Format-Table -AutoSize -Wrap | Out-String"'
result = apply_auto_fixes(cmd, "powershell")

print("Original:", cmd)
print("Fixed:   ", result)
print()

if "Out-String -Width 4096" in result:
    print("OK: Tiene Out-String -Width 4096")
else:
    print("FAIL: No tiene Out-String -Width 4096")

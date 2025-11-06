from command_fixers.auto_fixers import apply_auto_fixes

# Test 1: Select-String con -Context y Out-String
cmd1 = 'powershell -Command "Get-Content \'C:\\test.py\' | Select-String -Pattern \'def buscar\' -Context 0,10 | Out-String"'
result1 = apply_auto_fixes(cmd1, "powershell")
print("Test 1 (con Out-String):")
print(f"Original: {cmd1}")
print(f"Fixed:    {result1}")
print()

# Test 2: Select-String con -Context sin Out-String
cmd2 = 'powershell -Command "Get-Content \'C:\\test.py\' | Select-String -Pattern \'def buscar\' -Context 0,10"'
result2 = apply_auto_fixes(cmd2, "powershell")
print("Test 2 (sin Out-String):")
print(f"Original: {cmd2}")
print(f"Fixed:    {result2}")
print()

# Test 3: Verificar que tiene Format-Table
assert "Format-Table" in result1, "FAIL: No tiene Format-Table"
assert "Out-String -Width 4096" in result1, "FAIL: No tiene Out-String -Width"
print("✅ Tests PASSED - Fixer funciona correctamente")

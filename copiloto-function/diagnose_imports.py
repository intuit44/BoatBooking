#!/usr/bin/env python3
"""
Script de diagnóstico para identificar imports problemáticos
"""
import time
import sys
import traceback


def test_import(module_name, description=""):
    """Test individual import with timing"""
    print(f"\n🔍 Testing import: {module_name} {description}")
    start_time = time.time()

    try:
        if "." in module_name:
            # For submodules
            exec(f"import {module_name}")
        else:
            # For simple modules
            __import__(module_name)

        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: {module_name} imported in {elapsed:.2f}s")
        return True, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ FAILED: {module_name} failed after {elapsed:.2f}s - {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False, elapsed


def main():
    print("🚀 Azure Functions Import Diagnostics")
    print("=" * 50)

    # Test basic Python modules first
    basic_modules = [
        "os", "sys", "json", "logging", "time", "datetime",
        "traceback", "subprocess", "pathlib", "typing"
    ]

    print("\n📦 Testing basic Python modules...")
    for module in basic_modules:
        test_import(module)

    # Test Azure-specific modules
    azure_modules = [
        "azure.core",
        "azure.identity",
        "azure.storage.blob",
        "azure.cosmos",
        "azure.functions"
    ]

    print("\n☁️ Testing Azure modules...")
    for module in azure_modules:
        test_import(module, "(Azure SDK)")

    # Test project-specific modules that might be problematic
    project_modules = [
        "memory_manual",
        "cosmos_memory_direct",
        "services.memory_service",
        "router_agent",
        "endpoints.msearch",
        "endpoints.redis_model_wrapper",
        "endpoints.redis_admin",
        "endpoints.redis_cache_monitor"
    ]

    print("\n🏠 Testing project modules...")
    slow_imports = []

    for module in project_modules:
        success, elapsed = test_import(module, "(Project)")
        if elapsed > 5.0:  # Imports taking more than 5 seconds
            slow_imports.append((module, elapsed))

    print("\n" + "=" * 50)
    print("📊 SUMMARY:")

    if slow_imports:
        print(f"\n🐌 SLOW IMPORTS (>{5.0}s):")
        for module, elapsed in slow_imports:
            print(f"  - {module}: {elapsed:.2f}s")
    else:
        print("\n✅ No slow imports detected")

    print(f"\n⏱️ Total execution time: {time.time()}s")


if __name__ == "__main__":
    main()

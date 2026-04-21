#!/usr/bin/env python3
"""
verify_setup.py - Verify CinePredict installation and dependencies
Run this to check if your system is ready to use CinePredict
"""

import sys
import importlib
import platform
import os

def print_header():
    print("\n" + "="*80)
    print("  CINEPREDICT - INSTALLATION VERIFICATION")
    print("="*80 + "\n")

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}", end="")
    
    if version.major >= 3 and version.minor >= 7:
        print(" ✓ OK\n")
        return True
    else:
        print(" ✗ FAILED (requires 3.7+)\n")
        return False

def check_os():
    """Check operating system"""
    print("🔍 Checking operating system...")
    os_name = platform.system()
    print(f"   {os_name} {platform.release()}")
    
    if os_name in ["Windows", "Darwin", "Linux"]:
        print("   ✓ OK\n")
        return True
    else:
        print("   ✗ Unsupported OS\n")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"   ✓ {package_name} ({version})")
        return True
    except ImportError:
        print(f"   ✗ {package_name} NOT INSTALLED")
        return False

def check_dependencies():
    """Check all required Python packages"""
    print("🔍 Checking Python packages...")
    
    packages = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("pillow", "PIL"),
    ]
    
    all_ok = True
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            all_ok = False
    
    print()
    return all_ok

def check_project_files():
    """Check if all project files exist"""
    print("🔍 Checking project files...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "main.py",
        "etl.py",
        "model.py",
        "visualize.py",
        "ui.py",
        "utils.py",
        "warehouse.sql",
        "requirements.txt",
    ]
    
    required_dirs = [
        "data",
    ]
    
    all_ok = True
    
    for file in required_files:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"   ✓ {file}")
        else:
            print(f"   ✗ {file} NOT FOUND")
            all_ok = False
    
    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            print(f"   ✓ {dir_name}/ (directory)")
        else:
            print(f"   ✗ {dir_name}/ NOT FOUND")
            all_ok = False
    
    print()
    return all_ok

def check_data_files():
    """Check if input data exists"""
    print("🔍 Checking data files...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "data", "movies_sample.csv")
    
    if os.path.exists(data_file):
        size = os.path.getsize(data_file)
        print(f"   ✓ movies_sample.csv ({size:,} bytes)")
        print()
        return True
    else:
        print(f"   ✗ movies_sample.csv NOT FOUND")
        print()
        return False

def print_summary(results):
    """Print summary of checks"""
    print("="*80)
    print("  SUMMARY")
    print("="*80 + "\n")
    
    all_passed = all(results.values())
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {check_name:<30} {status}")
    
    print()
    
    if all_passed:
        print("  " + "█"*76)
        print("  ✓ ALL CHECKS PASSED - You are ready to run CinePredict!")
        print("  █"*76)
        print()
        print("  Quick start:")
        print("    Option 1 (Windows):  run.bat")
        print("    Option 2 (All):      python run.py")
        print("    Option 3 (All):      python main.py")
        print()
    else:
        print("  " + "█"*76)
        print("  ✗ SOME CHECKS FAILED - Please fix the issues above")
        print("  █"*76)
        print()
        print("  Common fixes:")
        print("    1. Install missing packages: pip install -r requirements.txt")
        print("    2. Check Python version: python --version")
        print("    3. Verify you're in the CinePredict directory")
        print()

def main():
    print_header()
    
    results = {
        "Python Version": check_python_version(),
        "Operating System": check_os(),
        "Python Packages": check_dependencies(),
        "Project Files": check_project_files(),
        "Data Files": check_data_files(),
    }
    
    print_summary(results)
    
    # Return exit code based on results
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())

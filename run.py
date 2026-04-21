#!/usr/bin/env python3
"""
run.py - CinePredict Setup & Execution Script
Installs dependencies and runs the Movie Success Prediction Pipeline
Works on Windows, macOS, and Linux
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("\n" + "="*80)
    print("  Installing required packages...")
    print("="*80 + "\n")
    
    packages = [
        "pandas",
        "numpy",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "pillow"
    ]
    
    for package in packages:
        try:
            print(f"  Installing {package}...", end=" ")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✓")
        except subprocess.CalledProcessError:
            print(f"⚠ Could not install {package}")
    
    print()

def main():
    print("\n" + "█" * 80)
    print("  CINEPREDICT - Movie Success Prediction System")
    print("  Data Warehousing + Data Mining Pipeline")
    print("█" * 80 + "\n")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        print(f"Your version: {sys.version}")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Run main pipeline
    print("="*80)
    print("  Starting pipeline execution...")
    print("="*80 + "\n")
    
    try:
        import main
        main.main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

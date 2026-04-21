"""
main.py ─ Master entry point
Movie Success Prediction System
Runs: ETL → Model Training → Visualization → Predictions
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils       import print_section, get_logger, ensure_output_dir
from etl         import run_etl
from model       import run_models
from visualize   import run_visualizations
from ui          import show_dashboard

log = get_logger("Main")


def main():
    print("\n" + "█" * 70)
    print("  MOVIE SUCCESS PREDICTION SYSTEM")
    print("  Data Warehousing + Data Mining Pipeline")
    print("█" * 70)

    ensure_output_dir()

    # ── 1. ETL ────────────────────────────────────────────────────────────────
    run_etl()

    # ── 2. Models ─────────────────────────────────────────────────────────────
    best_model, results, best_name, importances, df = run_models()

    # ── 3. Visualizations ─────────────────────────────────────────────────────
    paths = run_visualizations(results=results, importances=importances)

    # ── 4. Summary & Launch Dashboard UI ──────────────────────────────────────
    print_section("PROJECT COMPLETE ✓")
    print(f"  Best Model  : {best_name}")
    print(f"  Charts      : {len(paths)} files saved in outputs/")
    print(f"  Database    : data/movie_warehouse.db")
    print(f"\n  Output files:")
    for p in paths:
        print(f"    • {os.path.basename(p)}")
    print()
    
    # Prepare results data for UI
    results_data = {
        "best_model": best_name,
        "charts_count": len(paths),
        "charts": paths,
        "results": results,
        "importances": importances
    }
    
    # Launch dashboard UI
    print_section("LAUNCHING DASHBOARD UI")
    print("  Opening visualization dashboard...")
    show_dashboard(results_data)


if __name__ == "__main__":
    main()

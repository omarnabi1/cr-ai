#!/usr/bin/env python3
"""
CR-AI Expanded Dataset Master Runner
Runs all expanded collectors targeting 100,000+ records across 25+ categories.
"""

import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def run_all():
    log.info("=" * 60)
    log.info("CR-AI EXPANDED DATA COLLECTION — TARGET: 100,000+ RECORDS")
    log.info("=" * 60)
    results = {}

    from scripts.collection.expanded.human_dimensions_collector import run_human_dimensions
    results["human_dimensions"] = run_human_dimensions()

    from scripts.collection.expanded.structural_historical_collector import run_structural_historical
    results["structural_historical"] = run_structural_historical()

    from scripts.collection.expanded.systemic_collector import run_systemic
    results["systemic"] = run_systemic()

    from scripts.collection.expanded.ground_truth_collector import run_ground_truth
    results["ground_truth"] = run_ground_truth()

    total = sum(results.values())
    log.info("\n" + "=" * 60)
    log.info("EXPANDED COLLECTION COMPLETE")
    for k, v in results.items():
        log.info(f"  {k}: {v} records")
    log.info(f"  TOTAL NEW: {total} records")
    log.info("=" * 60)
    return results

if __name__ == "__main__":
    run_all()

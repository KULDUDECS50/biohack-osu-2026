"""
Main Pipeline Orchestrator for Kidney Allocation Simulation

This script runs the complete workflow from data generation to final evaluation.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import time


def run_command(command: list, description: str) -> bool:
    """
    Execute a command and handle errors.

    Args:
        command: Command to execute as list
        description: Description for logging

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print("="*80)
    print(f"Running: {' '.join(command)}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True
        )
        elapsed = time.time() - start_time
        print(f"\n✓ {description} completed in {elapsed:.1f}s")
        return True

    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n✗ {description} failed after {elapsed:.1f}s")
        print(f"Error: {e}")
        return False


def check_dependencies():
    """Check if all required Python packages are installed."""
    print("\n" + "="*80)
    print("CHECKING DEPENDENCIES")
    print("="*80)

    required_packages = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('joblib', 'joblib'),
        ('scipy', 'scipy')
    ]

    missing_packages = []

    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {display_name}")
        except ImportError:
            print(f"  ✗ {display_name} (missing)")
            missing_packages.append(display_name)

    if missing_packages:
        print(f"\n✗ Missing packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False

    print("\n✓ All dependencies satisfied")
    return True


def create_directories():
    """Create necessary directories if they don't exist."""
    print("\n" + "="*80)
    print("CREATING DIRECTORIES")
    print("="*80)

    directories = [
        "data/raw",
        "data/processed",
        "models",
        "outputs/plots",
        "outputs/reports"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run complete kidney allocation simulation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default parameters
  python main.py

  # Custom data size
  python main.py --n-donors 10000 --n-recipients 6000

  # Skip data generation (use existing data)
  python main.py --skip-data-gen

  # Run only specific steps
  python main.py --steps data feature train
        """
    )

    parser.add_argument(
        '--n-donors', type=int, default=5000,
        help='Number of donors to generate (default: 5000)'
    )
    parser.add_argument(
        '--n-recipients', type=int, default=3000,
        help='Number of recipients to generate (default: 3000)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--skip-data-gen', action='store_true',
        help='Skip data generation (use existing data)'
    )
    parser.add_argument(
        '--skip-feature-eng', action='store_true',
        help='Skip feature engineering (use existing processed data)'
    )
    parser.add_argument(
        '--skip-training', action='store_true',
        help='Skip model training (use existing models)'
    )
    parser.add_argument(
        '--model', type=str, default='models/gradient_boosting.pkl',
        help='Model to use for simulation (default: gradient_boosting)'
    )
    parser.add_argument(
        '--steps', nargs='+',
        choices=['data', 'feature', 'train', 'simulate', 'evaluate'],
        help='Run only specific steps'
    )

    args = parser.parse_args()

    # Determine which steps to run
    if args.steps:
        run_steps = set(args.steps)
    else:
        run_steps = {'data', 'feature', 'train', 'simulate', 'evaluate'}

    # Apply skip flags
    if args.skip_data_gen:
        run_steps.discard('data')
    if args.skip_feature_eng:
        run_steps.discard('feature')
    if args.skip_training:
        run_steps.discard('train')

    # Print banner
    print("\n" + "="*80)
    print("KIDNEY ALLOCATION SIMULATION PIPELINE")
    print("="*80)
    print("\nConfiguration:")
    print(f"  Donors: {args.n_donors}")
    print(f"  Recipients: {args.n_recipients}")
    print(f"  Random Seed: {args.seed}")
    print(f"  Model: {args.model}")
    print(f"\nSteps to run: {', '.join(sorted(run_steps))}")
    print("="*80)

    start_time = time.time()
    success = True

    # Check dependencies
    if not check_dependencies():
        print("\n✗ Dependency check failed. Please install required packages.")
        sys.exit(1)

    # Create directories
    create_directories()

    # Step 1: Data Generation
    if 'data' in run_steps:
        success = run_command(
            ['python', 'data_generator.py',
             '--n-donors', str(args.n_donors),
             '--n-recipients', str(args.n_recipients),
             '--seed', str(args.seed)],
            "Data Generation"
        )
        if not success:
            print("\n✗ Pipeline failed at data generation")
            sys.exit(1)

    # Step 2: Feature Engineering
    if 'feature' in run_steps:
        success = run_command(
            ['python', 'feature_engineering.py',
             '--seed', str(args.seed)],
            "Feature Engineering"
        )
        if not success:
            print("\n✗ Pipeline failed at feature engineering")
            sys.exit(1)

    # Step 3: Model Training
    if 'train' in run_steps:
        success = run_command(
            ['python', 'model_training.py'],
            "Model Training"
        )
        if not success:
            print("\n✗ Pipeline failed at model training")
            sys.exit(1)

    # Step 4: Allocation Simulation
    if 'simulate' in run_steps:
        success = run_command(
            ['python', 'allocation_simulator.py',
             '--model', args.model,
             '--seed', str(args.seed)],
            "Allocation Simulation"
        )
        if not success:
            print("\n✗ Pipeline failed at simulation")
            sys.exit(1)

    # Step 5: Evaluation
    if 'evaluate' in run_steps:
        success = run_command(
            ['python', 'evaluation.py'],
            "Evaluation & Visualization"
        )
        if not success:
            print("\n✗ Pipeline failed at evaluation")
            sys.exit(1)

    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "="*80)
    print("PIPELINE COMPLETE!")
    print("="*80)
    print(f"\nTotal execution time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\nGenerated outputs:")
    print(f"  Data: data/raw/")
    print(f"  Processed: data/processed/")
    print(f"  Models: models/")
    print(f"  Plots: outputs/plots/")
    print(f"  Reports: outputs/reports/")
    print(f"\nKey files to review:")
    print(f"  • outputs/reports/evaluation_report.txt")
    print(f"  • outputs/reports/allocation_comparison.csv")
    print(f"  • outputs/reports/fairness_metrics.csv")
    print(f"  • outputs/plots/policy_comparison_summary.png")
    print(f"  • outputs/plots/discard_by_kdpi.png")
    print("\n" + "="*80)
    print("Next steps:")
    print("  1. Review the evaluation report")
    print("  2. Examine visualizations in outputs/plots/")
    print("  3. Analyze fairness metrics")
    print("  4. Consider running with larger dataset (--n-donors 10000)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

#!/bin/bash
# Quick script to view BioHack outputs

echo "============================================"
echo "BioHack Kidney Allocation - Output Viewer"
echo "============================================"
echo ""

# Check if outputs exist
if [ ! -d "outputs" ]; then
    echo "ERROR: outputs/ directory not found!"
    echo "Run the pipeline first: python main.py"
    exit 1
fi

echo "Available outputs:"
echo ""
echo "REPORTS:"
echo "  1) Evaluation Report (main results)"
echo "  2) Allocation Comparison (CSV)"
echo "  3) Fairness Metrics (CSV)"
echo "  4) Standard Allocation Transplants (CSV)"
echo "  5) ML Allocation Transplants (CSV)"
echo ""
echo "PLOTS:"
echo "  6) Policy Comparison Summary ⭐"
echo "  7) Discard by KDPI"
echo "  8) Outcomes by Priority"
echo "  9) KDPI×EPTS Heatmap"
echo " 10) ROC Curves"
echo " 11) Feature Importance (Gradient Boosting)"
echo " 12) Feature Importance (Random Forest)"
echo " 13) Calibration Plots (all 3 models)"
echo ""
echo " 14) Open all plots in Windows Explorer"
echo " 15) List all files"
echo ""

read -p "Select option (1-15, or q to quit): " choice

case $choice in
    1)
        cat outputs/reports/evaluation_report.txt
        ;;
    2)
        echo "Allocation Comparison:"
        cat outputs/reports/allocation_comparison.csv
        ;;
    3)
        echo "Fairness Metrics:"
        cat outputs/reports/fairness_metrics.csv
        ;;
    4)
        echo "Standard Allocation Transplants (first 20 rows):"
        head -20 outputs/reports/standard_allocation_transplants.csv
        ;;
    5)
        echo "ML Allocation Transplants (first 20 rows):"
        head -20 outputs/reports/ml_allocation_transplants.csv
        ;;
    6)
        explorer.exe outputs/plots/policy_comparison_summary.png
        ;;
    7)
        explorer.exe outputs/plots/discard_by_kdpi.png
        ;;
    8)
        explorer.exe outputs/plots/outcomes_by_priority.png
        ;;
    9)
        explorer.exe outputs/plots/kdpi_epts_heatmap.png
        ;;
    10)
        explorer.exe outputs/plots/roc_curves_comparison.png
        ;;
    11)
        explorer.exe outputs/plots/feature_importance_gradient_boosting.png
        ;;
    12)
        explorer.exe outputs/plots/feature_importance_random_forest.png
        ;;
    13)
        explorer.exe outputs/plots/calibration_*.png
        ;;
    14)
        explorer.exe outputs/plots/
        ;;
    15)
        echo ""
        echo "All output files:"
        find outputs/ -type f -exec ls -lh {} \;
        ;;
    q|Q)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option!"
        ;;
esac

echo ""
echo "============================================"

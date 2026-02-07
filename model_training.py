"""
ML Model Training for Kidney Allocation

This module trains multiple classification models to predict graft success.
Includes cross-validation, calibration analysis, and feature importance visualization.

Models:
- Logistic Regression (baseline)
- Random Forest (ensemble)
- Gradient Boosting (advanced ensemble)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix,
    roc_curve, precision_recall_curve
)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import joblib
import argparse
from typing import Dict, Any


def load_processed_data(data_dir: str = "data/processed") -> tuple:
    """
    Load processed data from feature engineering pipeline.

    Args:
        data_dir: Directory containing processed numpy arrays

    Returns:
        Tuple of (X_train, X_test, y_train, y_test, feature_names)
    """
    data_path = Path(data_dir)

    print(f"Loading processed data from {data_dir}...")

    X_train = np.load(data_path / "X_train.npy")
    X_test = np.load(data_path / "X_test.npy")
    y_train = np.load(data_path / "y_train.npy")
    y_test = np.load(data_path / "y_test.npy")

    with open(data_path / "feature_names.txt", 'r') as f:
        feature_names = [line.strip() for line in f]

    print(f"  ✓ Training: {X_train.shape}")
    print(f"  ✓ Test: {X_test.shape}")
    print(f"  ✓ Features: {len(feature_names)}")

    return X_train, X_test, y_train, y_test, feature_names


def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """
    Train logistic regression model (baseline).

    Args:
        X_train: Training features
        y_train: Training labels

    Returns:
        Trained model
    """
    print("\n[1/3] Training Logistic Regression...")

    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight='balanced',  # Handle any class imbalance
        C=1.0  # Regularization strength
    )

    model.fit(X_train, y_train)

    print(f"  ✓ Model trained")

    return model


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """
    Train random forest classifier.

    Args:
        X_train: Training features
        y_train: Training labels

    Returns:
        Trained model
    """
    print("\n[2/3] Training Random Forest...")

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=20,
        min_samples_leaf=10,
        max_features='sqrt',
        random_state=42,
        class_weight='balanced',
        n_jobs=-1  # Use all CPU cores
    )

    model.fit(X_train, y_train)

    print(f"  ✓ Model trained ({model.n_estimators} trees)")

    return model


def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray) -> GradientBoostingClassifier:
    """
    Train gradient boosting classifier.

    Args:
        X_train: Training features
        y_train: Training labels

    Returns:
        Trained model
    """
    print("\n[3/3] Training Gradient Boosting...")

    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        random_state=42
    )

    model.fit(X_train, y_train)

    print(f"  ✓ Model trained ({model.n_estimators} stages)")

    return model


def cross_validate_model(model: Any, X: np.ndarray, y: np.ndarray,
                        cv_folds: int = 5) -> Dict[str, float]:
    """
    Perform cross-validation on a model.

    Args:
        model: Scikit-learn model
        X: Features
        y: Labels
        cv_folds: Number of CV folds

    Returns:
        Dictionary of CV scores
    """
    print(f"  Running {cv_folds}-fold cross-validation...")

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

    # Score multiple metrics
    accuracy = cross_val_score(model, X, y, cv=cv, scoring='accuracy', n_jobs=-1)
    precision = cross_val_score(model, X, y, cv=cv, scoring='precision', n_jobs=-1)
    recall = cross_val_score(model, X, y, cv=cv, scoring='recall', n_jobs=-1)
    f1 = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
    roc_auc = cross_val_score(model, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)

    scores = {
        'accuracy': accuracy.mean(),
        'accuracy_std': accuracy.std(),
        'precision': precision.mean(),
        'precision_std': precision.std(),
        'recall': recall.mean(),
        'recall_std': recall.std(),
        'f1': f1.mean(),
        'f1_std': f1.std(),
        'roc_auc': roc_auc.mean(),
        'roc_auc_std': roc_auc.std()
    }

    print(f"    Accuracy: {scores['accuracy']:.3f} ± {scores['accuracy_std']:.3f}")
    print(f"    F1 Score: {scores['f1']:.3f} ± {scores['f1_std']:.3f}")
    print(f"    ROC AUC:  {scores['roc_auc']:.3f} ± {scores['roc_auc_std']:.3f}")

    return scores


def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray,
                  model_name: str) -> Dict[str, float]:
    """
    Evaluate model on test set.

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        model_name: Name for display

    Returns:
        Dictionary of evaluation metrics
    """
    print(f"\nEvaluating {model_name} on test set...")

    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }

    print(f"  Accuracy:  {metrics['accuracy']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")
    print(f"  F1 Score:  {metrics['f1']:.3f}")
    print(f"  ROC AUC:   {metrics['roc_auc']:.3f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n  Confusion Matrix:")
    print(f"    TN: {cm[0,0]:4d}  FP: {cm[0,1]:4d}")
    print(f"    FN: {cm[1,0]:4d}  TP: {cm[1,1]:4d}")

    return metrics


def check_calibration(model: Any, X_test: np.ndarray, y_test: np.ndarray,
                     model_name: str, output_dir: str = "outputs/plots"):
    """
    Check model calibration (predicted probabilities vs. actual frequencies).

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        model_name: Name for plot title
        output_dir: Directory to save plot
    """
    print(f"\nChecking calibration for {model_name}...")

    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Calibration curve
    prob_true, prob_pred = calibration_curve(y_test, y_pred_proba, n_bins=10)

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(prob_pred, prob_true, marker='o', linewidth=2, label='Model')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfect calibration')
    plt.xlabel('Predicted Probability')
    plt.ylabel('True Frequency')
    plt.title(f'Calibration Plot: {model_name}')
    plt.legend()
    plt.grid(alpha=0.3)

    # Save plot
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path / f"calibration_{model_name.lower().replace(' ', '_')}.png",
                dpi=150, bbox_inches='tight')
    plt.close()

    # Calculate calibration error (mean absolute deviation)
    calibration_error = np.mean(np.abs(prob_true - prob_pred))
    print(f"  ✓ Calibration error: {calibration_error:.3f}")


def plot_feature_importance(model: Any, feature_names: list, model_name: str,
                           top_n: int = 20, output_dir: str = "outputs/plots"):
    """
    Plot feature importance for tree-based models.

    Args:
        model: Trained model with feature_importances_
        feature_names: List of feature names
        model_name: Name for plot title
        top_n: Number of top features to show
        output_dir: Directory to save plot
    """
    if not hasattr(model, 'feature_importances_'):
        print(f"  Skipping (model has no feature_importances_)")
        return

    print(f"\nPlotting feature importance for {model_name}...")

    # Get importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]

    # Create plot
    plt.figure(figsize=(10, 8))
    plt.barh(range(top_n), importances[indices], align='center')
    plt.yticks(range(top_n), [feature_names[i] for i in indices])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Features: {model_name}')
    plt.gca().invert_yaxis()
    plt.tight_layout()

    # Save plot
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path / f"feature_importance_{model_name.lower().replace(' ', '_')}.png",
                dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved feature importance plot")
    print(f"  Top 5 features:")
    for i in range(min(5, top_n)):
        feat_idx = indices[i]
        print(f"    {i+1}. {feature_names[feat_idx]}: {importances[feat_idx]:.4f}")


def plot_roc_curves(models: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray,
                   output_dir: str = "outputs/plots"):
    """
    Plot ROC curves for all models on the same plot.

    Args:
        models: Dictionary of {name: model}
        X_test: Test features
        y_test: Test labels
        output_dir: Directory to save plot
    """
    print("\nPlotting ROC curves for all models...")

    plt.figure(figsize=(10, 8))

    for name, model in models.items():
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        auc = roc_auc_score(y_test, y_pred_proba)

        plt.plot(fpr, tpr, linewidth=2, label=f'{name} (AUC={auc:.3f})')

    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves: Model Comparison')
    plt.legend()
    plt.grid(alpha=0.3)

    # Save plot
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path / "roc_curves_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved ROC comparison plot")


def save_models(models: Dict[str, Any], output_dir: str = "models"):
    """
    Save trained models to disk.

    Args:
        models: Dictionary of {name: model}
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving models to {output_dir}/...")

    for name, model in models.items():
        filename = f"{name.lower().replace(' ', '_')}.pkl"
        joblib.dump(model, output_path / filename)
        print(f"  ✓ Saved {filename}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Train ML models for kidney allocation"
    )
    parser.add_argument(
        '--data-dir', type=str, default='data/processed',
        help='Directory with processed data (default: data/processed)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='models',
        help='Directory to save models (default: models)'
    )
    parser.add_argument(
        '--cv-folds', type=int, default=5,
        help='Number of cross-validation folds (default: 5)'
    )

    args = parser.parse_args()

    print("="*60)
    print("ML MODEL TRAINING PIPELINE")
    print("="*60)
    print(f"Configuration:")
    print(f"  Data: {args.data_dir}")
    print(f"  Output: {args.output_dir}")
    print(f"  CV Folds: {args.cv_folds}")
    print("="*60)

    # Load data
    X_train, X_test, y_train, y_test, feature_names = load_processed_data(args.data_dir)

    # Train models
    print("\n" + "="*60)
    print("TRAINING MODELS")
    print("="*60)

    lr_model = train_logistic_regression(X_train, y_train)
    rf_model = train_random_forest(X_train, y_train)
    gb_model = train_gradient_boosting(X_train, y_train)

    models = {
        'Logistic Regression': lr_model,
        'Random Forest': rf_model,
        'Gradient Boosting': gb_model
    }

    # Cross-validation
    print("\n" + "="*60)
    print("CROSS-VALIDATION")
    print("="*60)

    cv_results = {}
    for name, model in models.items():
        print(f"\n{name}:")
        cv_results[name] = cross_validate_model(model, X_train, y_train, args.cv_folds)

    # Test set evaluation
    print("\n" + "="*60)
    print("TEST SET EVALUATION")
    print("="*60)

    test_results = {}
    for name, model in models.items():
        test_results[name] = evaluate_model(model, X_test, y_test, name)

    # Calibration checking
    print("\n" + "="*60)
    print("CALIBRATION ANALYSIS")
    print("="*60)

    for name, model in models.items():
        check_calibration(model, X_test, y_test, name)

    # Feature importance
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)

    for name, model in models.items():
        print(f"\n{name}:")
        plot_feature_importance(model, feature_names, name)

    # ROC curves
    plot_roc_curves(models, X_test, y_test)

    # Save models
    save_models(models, args.output_dir)

    # Final summary
    print("\n" + "="*60)
    print("MODEL TRAINING COMPLETE!")
    print("="*60)
    print("\nTest Set Performance Summary:")
    print(f"{'Model':<25} {'Accuracy':<10} {'F1':<10} {'ROC AUC':<10}")
    print("-"*60)
    for name, metrics in test_results.items():
        print(f"{name:<25} {metrics['accuracy']:<10.3f} {metrics['f1']:<10.3f} {metrics['roc_auc']:<10.3f}")


if __name__ == "__main__":
    main()

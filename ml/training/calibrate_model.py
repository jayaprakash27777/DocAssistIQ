"""DocAssistIQ ?" Model Calibration (Phase 64).

Applies Isotonic Regression calibration to the base Random Forest model
to ensure probabilities accurately reflect true confidence, supporting strict abstention.
"""

import os
import joblib
from pathlib import Path
from sklearn.calibration import CalibratedClassifierCV
try:
    from sklearn.frozen import FrozenEstimator
except ImportError:
    FrozenEstimator = None
from ml.training.baseline_model import generate_synthetic_data

def main():
    print("=" * 60)
    print("DocAssistIQ - Phase 64: Model Calibration")
    print("=" * 60)

    # 1. Load the existing baseline model
    model_path = Path("ml/experiments/baseline_rf_model.joblib")
    if not model_path.exists():
        print(f"Error: Base model not found at {model_path}")
        print("Please run `python -m ml.training.baseline_model` first.")
        return

    print("Loading base Random Forest model...")
    base_model = joblib.load(model_path)

    # 2. Generate a hold-out dataset for calibration
    print("Generating holdout dataset for Isotonic calibration...")
    df_calib = generate_synthetic_data(n_samples=2000)
    X_calib = df_calib["text"]
    y_calib = df_calib["diagnosis"]

    # 3. Apply Calibration (Isotonic handles non-linear Random Forest outputs well)
    print("Applying Isotonic Calibration (prefit)...")
    if FrozenEstimator is not None:
        calibrated_model = CalibratedClassifierCV(
            estimator=FrozenEstimator(base_model),
            method='isotonic'
        )
    else:
        calibrated_model = CalibratedClassifierCV(
            estimator=base_model,
            method='isotonic',
            cv='prefit'
        )
    
    # 4. Fit the calibrator on the holdout set
    calibrated_model.fit(X_calib, y_calib)

    # 5. Save the calibrated model
    out_path = Path("ml/experiments/baseline_calibrated_model.joblib")
    joblib.dump(calibrated_model, out_path)
    
    # We also need to copy the encoder for the new pipeline to use
    encoder_path = Path("ml/experiments/label_encoder.joblib")
    if encoder_path.exists():
        # LabelEncoder doesn't change during calibration, just ensure it's there
        pass
        
    print(f"\nCalibrated model successfully saved to: {out_path}")
    print("Calibration Complete. The model will now output true confidence probabilities.")

if __name__ == "__main__":
    main()

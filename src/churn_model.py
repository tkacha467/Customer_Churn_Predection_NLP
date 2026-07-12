import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, f1_score,
                             precision_score, recall_score,
                             roc_auc_score, classification_report)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

def train_churn_model(processed_data_path='../data/processed/', models_path='../models/'):
    print("Starting Churn Model Training Pipeline...")
    
    # Load features
    features_file = os.path.join(processed_data_path, 'rfm_features.csv')
    try:
        features = pd.read_csv(features_file)
    except FileNotFoundError:
        print(f"{features_file} not found. Run rfm_features.py first.")
        return None

    # Handle NaNs
    features.fillna(0, inplace=True)

    # Prepare X and y
    # Drop features that are directly used to calculate churn label (recency, frequency)
    # as they would cause data leakage
    X = features.drop(columns=['customer_unique_id', 'churn', 'recency', 'frequency'])
    y = features['churn']
    
    print(f"Features (X): {X.shape}")
    print(f"Target (y) Distribution:\n{y.value_counts()}")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Handle class imbalance using SMOTE
    print("Applying SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

    # Baseline Dummy Classifier
    print("Training Baseline Dummy Classifier...")
    dummy = DummyClassifier(strategy='most_frequent', random_state=42)
    dummy.fit(X_train_sm, y_train_sm)
    y_dummy = dummy.predict(X_test)
    
    print("\n--- Baseline Results ---")
    print(f"Accuracy: {accuracy_score(y_test, y_dummy):.4f}")
    print(f"AUC-ROC:  {roc_auc_score(y_test, y_dummy):.4f}")

    # XGBoost Classifier
    print("\nTraining XGBoost Classifier...")
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    xgb.fit(X_train_sm, y_train_sm)
    y_pred = xgb.predict(X_test)
    y_pred_proba = xgb.predict_proba(X_test)[:, 1]

    print("\n--- XGBoost Model Results ---")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y_test, y_pred):.4f}")
    print(f"AUC-ROC:   {roc_auc_score(y_test, y_pred_proba):.4f}")
    
    # Save the model
    os.makedirs(models_path, exist_ok=True)
    model_file = os.path.join(models_path, 'xgboost_churn_v1.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump(xgb, f)
    
    # Save test predictions for the risk score module
    test_results = features.iloc[X_test.index][['customer_unique_id']].copy()
    test_results['churn_probability'] = y_pred_proba
    pred_file = os.path.join(processed_data_path, 'churn_predictions.csv')
    test_results.to_csv(pred_file, index=False)

    print(f"\nModel saved to {model_file}")
    print(f"Predictions saved to {pred_file}")
    return xgb

if __name__ == "__main__":
    train_churn_model(processed_data_path='../data/processed/', models_path='../models/')

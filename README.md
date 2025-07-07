# Titanic_Survival_Prediction
Predicts Titanic passenger survival using Ludwig (AutoML) and tracks experiments with MLflow. Includes data download, training, evaluation (accuracy, F1, etc.), and model logging for reproducibility.


This project demonstrates a full machine learning pipeline using Ludwig (a low-code AutoML tool) to predict Titanic passenger survival. It includes data preprocessing, model training, evaluation, and experiment tracking using MLflow.

Key Features:

Uses Ludwig's declarative YAML config for model specification.

Automatically downloads and processes the Titanic dataset.

Tracks training metrics (accuracy, F1, precision, recall, ROC AUC) with MLflow.

Logs model artifacts and configurations for reproducibility.

Technologies: Python, Ludwig, MLflow, Pandas, Scikit-learn

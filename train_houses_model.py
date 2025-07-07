import mlflow
import mlflow.sklearn
import ludwig
import pandas as pd
import yaml
from ludwig.api import LudwigModel
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Ludwig model configuration
config = {
    "input_features": [
        {"name": "Pclass", "type": "category"},
        {"name": "Sex", "type": "category"},
        {"name": "Age", "type": "number"},
        {"name": "SibSp", "type": "number"},
        {"name": "Parch", "type": "number"},
        {"name": "Fare", "type": "number"}
    ],
    "output_features": [
        {"name": "Survived", "type": "binary"}
    ],
    "trainer": {
        "epochs": 10,
        "batch_size": 32,
        "learning_rate": 0.001,
        "optimizer": {"type": "adam"}
    }
}

# Save Ludwig config to YAML file
with open("titanic_config.yaml", "w") as f:
    yaml.dump(config, f)

# Set MLflow tracking URI (local directory)
mlflow.set_tracking_uri("file:///tmp/mlflow")
mlflow.set_experiment("Titanic_Survival_Prediction")

def download_titanic_dataset():
    """Download and preprocess the Titanic dataset."""
    try:
        url = "https://web.stanford.edu/class/archive/cs/cs109/cs109.1166/stuff/titanic.csv"
        df = pd.read_csv(url)
        # Ludwig expects specific column names and types
        df = df.rename(columns={"Siblings/Spouses Aboard": "SibSp", "Parents/Children Aboard": "Parch"})
        df.to_csv("titanic.csv", index=False)
        logger.info("Titanic dataset downloaded and saved as titanic.csv")
        return df
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def safe_last_value(metric):
    """Return the last value if metric is a list, else return the value."""
    if isinstance(metric, list):
        return metric[-1]
    return metric

def train_and_track():
    """Train Ludwig model and track with MLflow."""
    with mlflow.start_run(run_name="Ludwig_Titanic_Run"):
        # Log hyperparameters
        mlflow.log_param("epochs", config["trainer"]["epochs"])
        mlflow.log_param("batch_size", config["trainer"]["batch_size"])
        mlflow.log_param("learning_rate", config["trainer"]["learning_rate"])
        mlflow.log_param("optimizer", config["trainer"]["optimizer"]["type"])

        # Download dataset
        df = download_titanic_dataset()

        # Initialize Ludwig model
        try:
            model = LudwigModel(config="titanic_config.yaml")
            logger.info("Ludwig model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Ludwig model: {e}")
            raise

        # Train model
        try:
            train_stats, _, _ = model.train(dataset="titanic.csv", output_directory="results")
            logger.info("Model training completed")
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            raise

        # Extract metrics from training stats
        validation_stats = train_stats["validation"]["Survived"]
        accuracy = safe_last_value(validation_stats.get("accuracy", 0.0))
        f1 = safe_last_value(validation_stats.get("f1_score", 0.0))

        # Get predictions
        try:
            predictions, _ = model.predict(dataset="titanic.csv")
            logger.info(f"Prediction columns: {list(predictions.columns)}")
        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            raise

        y_true = df["Survived"].values
        y_pred = predictions["Survived_predictions"].values

        # Find probability column dynamically
        prob_column = None
        for col in predictions.columns:
            if "Survived_probabilities" in col and ("True" in col or "1" in col):
                prob_column = col
                break
        if prob_column is None:
            logger.warning("No probability column found for positive class. Skipping ROC-AUC.")
            roc_auc = 0.0
        else:
            y_proba = predictions[prob_column].values
            roc_auc = roc_auc_score(y_true, y_proba)
            logger.info(f"Using probability column: {prob_column}")

        # Compute other metrics
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)

        # Log metrics to MLflow
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("roc_auc", roc_auc)
        logger.info(f"Logged metrics: accuracy={accuracy}, f1_score={f1}, precision={precision}, recall={recall}, roc_auc={roc_auc}")

        # Save Ludwig model as artifact
        model.save("titanic_model")
        mlflow.log_artifact("titanic_model", artifact_path="model")
        logger.info("Model saved and logged to MLflow")

        # Log Ludwig config
        mlflow.log_artifact("titanic_config.yaml", artifact_path="config")
        logger.info("Ludwig config logged to MLflow")

if __name__ == "__main__":
    try:
        train_and_track()
        logger.info("Experiment completed successfully")
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise



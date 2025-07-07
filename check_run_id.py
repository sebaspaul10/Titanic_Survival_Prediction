import mlflow

client = mlflow.tracking.MlflowClient()
experiment = client.get_experiment_by_name("Titanic_Survival_Prediction")
runs = client.search_runs(experiment.experiment_id)

for run in runs:
    print("Run ID:", run.info.run_id)

from flask import Flask, request, render_template, jsonify
import pandas as pd
from ludwig.api import LudwigModel
import os
from prometheus_client import start_http_server, Counter, Histogram, Summary
import time

app = Flask(__name__)

# Prometheus metrics
PREDICTION_COUNTER = Counter('num_predictions', 'Number of predictions made')
PREDICTION_LATENCY = Histogram('prediction_latency_seconds', 'Time taken for predictions')
REQUEST_LATENCY = Summary('request_processing_seconds', 'Time spent processing HTTP requests')

# Load Ludwig model
model_path = "titanic_model"
model = LudwigModel.load(model_path)

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/predict', methods=['POST'])
@REQUEST_LATENCY.time()  # Measure request processing time
def predict():
    start_time = time.time()
    try:
        features = {
            'Pclass': [int(request.form['Pclass'])],
            'Sex': [request.form['Sex']],
            'Age': [float(request.form['Age'])],
            'SibSp': [int(request.form['SibSp'])],
            'Parch': [int(request.form['Parch'])],
            'Fare': [float(request.form['Fare'])]
        }

        df = pd.DataFrame(features)
        predictions, _ = model.predict(df)

        prediction_result = predictions['Survived_predictions'][0]
        prob_col = [col for col in predictions.columns if "Survived_probabilities" in col and ("True" in col or "1" in col)]
        probability = predictions[prob_col[0]][0] * 100 if prob_col else 0

        # Record Prometheus metrics
        PREDICTION_COUNTER.inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)

        return render_template('form.html', prediction=prediction_result, probability=round(probability, 2))

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    start_http_server(8000)  # Expose metrics at :8000/metrics
    app.run(host='0.0.0.0', port=5050)
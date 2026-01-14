from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

# Charger le modèle au démarrage
# model = joblib.load("models/Linear_Regression.pkl")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        features = np.array(data['features']).reshape(1, -1)
        #prediction = model.predict(features)
        
        return jsonify({
            #'predsiction': int(prediction[0]),
            'prediction': int(16),
            'model_version': '1.0.0'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health')
def health():
    #return jsonify({'status': 'healthy', 'model_loaded': model is not None})
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
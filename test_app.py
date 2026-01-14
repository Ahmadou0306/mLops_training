# test_app.py
import pytest
import json
from app import app

@pytest.fixture
def client():
    """Fixture pour créer un client de test Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    """Test du endpoint /health"""
    response = client.get('/health')
    
    assert response.status_code == 200
    assert response.json == {'status': 'healthy'}

def test_predict_success(client):
    """Test du endpoint /predict avec des données valides"""
    # Données de test (adapter selon votre modèle)
    test_data = {
        'features': [1, 2, 3, 4, 5]  # Exemple de features
    }
    
    response = client.post(
        '/predict',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    assert 'prediction' in response.json
    assert 'model_version' in response.json
    assert response.json['model_version'] == '1.0.0'

def test_predict_missing_data(client):
    """Test du endpoint /predict sans données"""
    response = client.post(
        '/predict',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    assert 'error' in response.json


#def test_predict_invalid_data(client):
#    """Test du endpoint /predict avec données invalides"""
#    test_data = {
#        'features': 'invalid'  # String au lieu d'array
#    }
#    
#    response = client.post(
#        '/predict',
#        data=json.dumps(test_data),
#        content_type='application/json'
#    )
#    
#    assert response.status_code == 400
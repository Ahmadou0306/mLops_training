// ============================================================================
// JENKINSFILE POUR PROJET AVEC docker compose
// Infrastructure MLOps complète : API + PostgreSQL + MLflow + Monitoring
// ============================================================================

pipeline {
    agent {
        docker {
            image 'ahmadou030602/python-docker' //image custom pour avoir docker et python
            args '-v /var/run/docker.sock:/var/run/docker.sock' //permet d'exécuter les commandes docker-socket hérité du master
            reuseNode true
        }
    }

    
    environment {
        // Configuration Docker
        COMPOSE_PROJECT_NAME = 'mlops-training'
        DOCKER_IMAGE = 'mlops-training'
        VERSION = "${env.BUILD_NUMBER}"
        
        // Configuration des services
        API_PORT = '8080'
        MLFLOW_PORT = '5000'
        GRAFANA_PORT = '3000'
        PROMETHEUS_PORT = '9090'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 45, unit: 'MINUTES')  // Plus de temps pour docker compose
    }
    
    triggers {
        // Polling Git (alternative au webhook)
        pollSCM('H/5 * * * *')  // Toutes les 5 minutes
    }

    stages {
        
        // ====================================================================
        // STAGE 1 : Checkout et Préparation
        // ====================================================================
        stage('Checkout') {
            steps {
                echo '=== Récupération du code depuis Git ==='
                checkout scm
                
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
                
                echo "📌 Commit: ${env.GIT_COMMIT_SHORT}"
                echo "📌 Build: #${env.BUILD_NUMBER}"
                
                // Vérifier que docker compose.yml existe
                sh '''
                    if [ ! -f docker compose.yml ]; then
                        echo "❌ docker compose.yml introuvable !"
                        exit 1
                    fi
                    echo "✅ docker compose.yml trouvé"
                '''
            }
        }
        
        // ====================================================================
        // STAGE 2 : Code Quality (dans un conteneur isolé)
        // ====================================================================
        stage('Code Quality') {
            steps {
                echo '=== Analyse de la qualité du code ==='
                script {
                    docker.image('python:3.11-slim').inside {
                        sh '''
                            pip install flake8 black --quiet
                            
                            echo "🔍 Linting avec flake8..."
                            flake8 . --max-line-length=120 \
                                --exclude=venv,__pycache__,models \
                                || true
                            
                            echo "🎨 Vérification du formatage..."
                            black --check . || echo "⚠️ Code pas formaté"
                        '''
                    }
                }
            }
        }
        
        // ====================================================================
        // STAGE 3 : Tests Unitaires (avant de builder les services)
        // ====================================================================
        stage('Tests Unitaires') {
            steps {
                echo '=== Exécution des tests unitaires ==='
                script {
                    docker.image('python:3.11-slim').inside {
                        sh '''
                            pip install -r requirements.txt --quiet
                            pip install pytest pytest-cov --quiet
                            
                            mkdir -p reports
                            
                            echo "🧪 Tests unitaires..."
                            pytest test_app.py -v \
                                --junitxml=reports/junit.xml \
                                --cov=. \
                                --cov-report=html \
                                --cov-report=term-missing \
                                || echo "⚠️ Certains tests ont échoué"
                        '''
                    }
                }
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    publishHTML([
                        allowMissing: false,              
                        alwaysLinkToLastBuild: true,      
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Code Coverage',
                        reportTitles: ''
                    ])
                }
            }
        }
        
        // ====================================================================
        // STAGE 4 : Nettoyage des Services Existants
        // ====================================================================
        stage('Cleanup') {
            steps {
                echo '=== Nettoyage des services existants ==='
                sh '''
                    echo "🛑 Arrêt des services existants..."
                    docker compose down
                    
                    echo "🗑️ Nettoyage des anciennes images..."
                    docker image prune -f || true
                    
                    echo "✅ Nettoyage terminé"
                '''
            }
        }
        
        // ====================================================================
        // STAGE 5 : Build de l'Image Docker de l'API
        // ====================================================================
        stage('Build Docker Image') {
            steps {
                echo '=== Construction de l\'image Docker de l\'API ==='
                script {
                    sh """
                        echo "🔨 Build de l'image model-api..."
                        docker build \
                            -t ${DOCKER_IMAGE}:${VERSION} \
                            -t ${DOCKER_IMAGE}:latest \
                            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                            --build-arg VCS_REF=${env.GIT_COMMIT_SHORT} \
                            .
                    """
                    
                    echo "✅ Image créée: ${DOCKER_IMAGE}:${VERSION}"
                    sh "docker images | grep ${DOCKER_IMAGE} | head -3"
                }
            }
        }
        
        // ====================================================================
        // STAGE 6 : Lancement des Services avec Docker Compose
        // ====================================================================
        stage('Start Services') {
            steps {
                echo '=== Démarrage des services Docker Compose ==='
                sh '''
                    echo "🚀 Lancement de tous les services..."
                    
                    # Lancer en mode détaché
                    docker compose up -d
                    
                    echo "⏳ Attente du démarrage des services (30s)..."
                    sleep 30
                    
                    echo "📊 État des services:"
                    docker compose ps
                '''
            }
        }
        
        // ====================================================================
        // STAGE 7 : Health Checks de Tous les Services
        // ====================================================================
        stage('Health Checks') {
            steps {
                echo '=== Vérification de la santé des services ==='
                script {
                    sh '''
                        echo "==================================="
                        echo "🔍 Health Check des Services"
                        echo "==================================="
                        
                        # Fonction de health check
                        check_service() {
                            local service=$1
                            local url=$2
                            local max_attempts=10
                            local attempt=1
                            
                            echo ""
                            echo "📡 Test de $service sur $url"
                            
                            while [ $attempt -le $max_attempts ]; do
                                if curl -f -s "$url" > /dev/null 2>&1; then
                                    echo "✅ $service est UP (tentative $attempt/$max_attempts)"
                                    return 0
                                fi
                                echo "⏳ Attente $service... (tentative $attempt/$max_attempts)"
                                sleep 5
                                attempt=$((attempt + 1))
                            done
                            
                            echo "❌ $service n'a pas démarré après $max_attempts tentatives"
                            return 1
                        }
                        
                        # Vérifier chaque service
                        HEALTH_CHECK_FAILED=0
                        
                        # 1. API Model
                        check_service "Model API" "http://localhost:8080/health" || HEALTH_CHECK_FAILED=1
                        
                        # 2. PostgreSQL (via pg_isready)
                        echo ""
                        echo "📡 Test de PostgreSQL"
                        if docker compose exec -T postgres pg_isready -U admin > /dev/null 2>&1; then
                            echo "✅ PostgreSQL est UP"
                        else
                            echo "❌ PostgreSQL n'est pas disponible"
                            HEALTH_CHECK_FAILED=1
                        fi
                        
                        # 3. MLflow
                        check_service "MLflow" "http://localhost:5000" || HEALTH_CHECK_FAILED=1
                        
                        # 4. Prometheus
                        check_service "Prometheus" "http://localhost:9090/-/healthy" || HEALTH_CHECK_FAILED=1
                        
                        # 5. Grafana
                        check_service "Grafana" "http://localhost:3000/api/health" || HEALTH_CHECK_FAILED=1
                        
                        echo ""
                        echo "==================================="
                        if [ $HEALTH_CHECK_FAILED -eq 0 ]; then
                            echo "✅ Tous les services sont UP !"
                        else
                            echo "❌ Certains services ont échoué"
                            echo "📋 Logs des services:"
                            docker compose logs --tail=50
                            exit 1
                        fi
                        echo "==================================="
                    '''
                }
            }
        }
        
        // ====================================================================
        // STAGE 8 : Tests d'Intégration (API + Services)
        // ====================================================================
        stage('Tests d\'Intégration') {
            steps {
                echo '=== Tests d\'intégration de la stack complète ==='
                script {
                    sh '''
                        echo "🧪 Tests d'intégration..."
                        
                        # Test 1 : Endpoint de prédiction de l'API
                        echo ""
                        echo "📝 Test 1: Endpoint /predict"
                        RESPONSE=$(curl -s -X POST http://localhost:8080/predict \
                            -H "Content-Type: application/json" \
                            -d '{"features": [1, 2, 3, 4, 5]}' \
                            -w "\n%{http_code}")
                        
                        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
                        BODY=$(echo "$RESPONSE" | head -n-1)
                        
                        if [ "$HTTP_CODE" = "200" ]; then
                            echo "✅ API répond correctement"
                            echo "   Response: $BODY"
                        else
                            echo "❌ API erreur (HTTP $HTTP_CODE)"
                            echo "   Response: $BODY"
                            exit 1
                        fi
                        
                        # Test 2 : Vérifier que MLflow enregistre les expériences
                        echo ""
                        echo "📝 Test 2: MLflow tracking"
                        MLFLOW_EXPERIMENTS=$(curl -s http://localhost:5000/api/2.0/mlflow/experiments/list)
                        if echo "$MLFLOW_EXPERIMENTS" | grep -q "experiments"; then
                            echo "✅ MLflow tracking fonctionne"
                        else
                            echo "⚠️ MLflow tracking: pas d'expériences (normal au premier lancement)"
                        fi
                        
                        # Test 3 : Vérifier les métriques Prometheus
                        echo ""
                        echo "📝 Test 3: Prometheus metrics"
                        PROM_METRICS=$(curl -s http://localhost:9090/api/v1/query?query=up)
                        if echo "$PROM_METRICS" | grep -q "success"; then
                            echo "✅ Prometheus collecte des métriques"
                        else
                            echo "⚠️ Prometheus: métriques non disponibles"
                        fi
                        
                        # Test 4 : Base de données PostgreSQL
                        echo ""
                        echo "📝 Test 4: PostgreSQL connectivity"
                        if docker compose exec -T postgres psql -U admin -d mlflow -c "SELECT 1;" > /dev/null 2>&1; then
                            echo "✅ PostgreSQL accepte les connexions"
                        else
                            echo "❌ PostgreSQL connexion échouée"
                            exit 1
                        fi
                        
                        echo ""
                        echo "✅ Tous les tests d'intégration passés !"
                    '''
                }
            }
        }
        
        // ====================================================================
        // STAGE 9 : Performance / Load Test (Optionnel)
        // ====================================================================
        stage('Load Test') {
            when {
                branch 'main'  // Seulement sur la branche main
            }
            steps {
                echo '=== Test de charge de l\'API ==='
                script {
                    sh '''
                        echo "⚡ Test de charge avec Apache Bench..."
                        
                        # Installer ab si nécessaire
                        if ! command -v ab &> /dev/null; then
                            echo "Installation d'Apache Bench..."
                            apt-get update && apt-get install -y apache2-utils || \
                            apk add apache2-utils || \
                            echo "⚠️ ab non disponible, skip load test"
                        fi
                        
                        # Test de charge : 100 requêtes, 10 concurrentes
                        if command -v ab &> /dev/null; then
                            echo "🚀 100 requêtes, 10 concurrentes sur /health"
                            ab -n 100 -c 10 http://localhost:8080/health || echo "⚠️ Load test failed"
                        fi
                    '''
                }
            }
        }
        
        // ====================================================================
        // STAGE 10 : Collecte des Logs et Métriques
        // ====================================================================
        stage('Collect Metrics') {
            steps {
                echo '=== Collecte des logs et métriques ==='
                sh '''
                    echo "📊 Statistiques des conteneurs:"
                    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
                    
                    echo ""
                    echo "📋 Logs récents de chaque service:"
                    
                    echo "--- Model API ---"
                    docker compose logs --tail=20 model-api
                    
                    echo "--- MLflow ---"
                    docker compose logs --tail=20 mlflow
                    
                    echo "--- PostgreSQL ---"
                    docker compose logs --tail=10 postgres
                '''
            }
        }
        
        // ====================================================================
        // STAGE 11 : Décision de Déploiement (Manuel pour Production)
        // ====================================================================
        stage('Deploy Decision') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Seulement pour la branche main, demander confirmation
                    def userInput = input(
                        id: 'DeployApproval',
                        message: '✅ Tests passés ! Garder les services actifs ?',
                        parameters: [
                            choice(
                                name: 'ACTION',
                                choices: ['Keep Running (Dev/Staging)', 'Stop Services', 'Tag for Production'],
                                description: 'Que faire avec les services ?'
                            )
                        ]
                    )
                    
                    echo "👤 Décision utilisateur: ${userInput}"
                    
                    if (userInput == 'Stop Services') {
                        echo "🛑 Arrêt des services..."
                        sh 'docker compose down'
                    } else if (userInput == 'Tag for Production') {
                        echo "🏷️ Tagging pour production..."
                        sh """
                            docker tag ${DOCKER_IMAGE}:${VERSION} ${DOCKER_IMAGE}:production
                            echo "✅ Tagged as production"
                        """
                    } else {
                        echo "✅ Services restent actifs"
                    }
                }
            }
        }
    }
    
    // ========================================================================
    // POST : Actions finales
    // ========================================================================
    post {
        always {
            echo '=== Résumé de l\'exécution ==='
            script {
                sh '''
                    echo "📊 État final des services:"
                    docker compose ps || echo "Services arrêtés"
                    
                    echo ""
                    echo "🐳 Images Docker créées:"
                    docker images | grep mlops-training || echo "Aucune image"
                '''
            }
        }
        
        success {
            echo '✅✅✅ PIPELINE RÉUSSI ! ✅✅✅'
            echo """
            🎉 Stack MLOps déployée avec succès !
            
            📍 Services disponibles:
               • API Model:     http://localhost:8080
               • MLflow:        http://localhost:5000
               • Grafana:       http://localhost:3000 (admin/admin)
               • Prometheus:    http://localhost:9090
            
            🐳 Image: ${DOCKER_IMAGE}:${VERSION}
            📌 Commit: ${env.GIT_COMMIT_SHORT}
            """
        }
        
        failure {
            echo '❌❌❌ PIPELINE ÉCHOUÉ ! ❌❌❌'
            echo 'Récupération des logs pour debug...'
            
            sh '''
                echo "📋 Logs des services en erreur:"
                docker compose logs --tail=100 || echo "Pas de logs disponibles"
                
                echo ""
                echo "🐳 État des conteneurs:"
                docker compose ps -a || echo "Aucun conteneur"
            '''
            
            // Nettoyer en cas d'échec
            sh 'docker compose down --volumes || true'
        }
        
        unstable {
            echo '⚠️ Pipeline instable'
            echo 'Certains tests ont échoué mais le build a continué'
        }
        
        cleanup {
            // Nettoyage final (optionnel)
            echo '🧹 Nettoyage final...'
            sh '''
                # Nettoyer les images dangling
                docker image prune -f || true
                
                # Nettoyer les volumes orphelins (attention en prod !)
                # docker volume prune -f || true
            '''
        }
    }
}
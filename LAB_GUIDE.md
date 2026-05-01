# Lab 03: GitOps with ArgoCD
**Author: Nishant Minj**

## 1. Purpose
Implement **GitOps** for the Order System. Instead of manually running `kubectl apply`, we will define our desired state in Git and let ArgoCD sync it automatically.

## 2. Architecture & Data Flow

```text
  [ Git Repo ] <---------- (Developer Pushes YAML)
       |
       | (Poll / Webhook)
       v
  [ ArgoCD ] ------------> (Sync State)
       |                      |
       +----------------------+-----> [ Cluster ]
                                         |
                                  [ microservices-lab ]
```

---

## 3. Step-by-Step Setup

### Step A: Install ArgoCD
```bash
kubectl create namespace argocd
kubectl apply --server-side -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Step B: Access ArgoCD UI
```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Step C: Build and Push Docker Images
Before ArgoCD can deploy your application, you need to build the Docker images and push them to a registry (e.g., Docker Hub).

#### 1. Login to Docker Hub
```bash
docker login
```

#### 2. Build the Backend Image
Navigate to the backend directory and build the image:
```bash
cd app/backend
docker build -t minjteck/order-api:v1 .
```

#### 3. Build the Nishant WebApp Image
Navigate to the webapp directory and build the image:
```bash
cd app/webapp
docker build -t minjteck/nishant-webapp:v1 .
```

#### 4. Push to Registry
```bash
docker push minjteck/order-api:v1
docker push minjteck/nishant-webapp:v1
```

#### 5. Update Manifests
Update the image field in `manifests/inventory-app.yml` and `manifests/mysql-webapp.yml` to use your new images:
```yaml
# In manifests/mysql-webapp.yml
spec:
  containers:
  - name: webapp
    image: minjteck/nishant-webapp:v1

# In manifests/inventory-app.yml
spec:
  containers:
  - name: webapp
    image: minjteck/order-api:v1  
```

### Step D: Deploy the Application
```bash
kubectl apply -f application.yml
```

---

## 4. Validation & GitOps Testing

### Sync Status
Check the status in the ArgoCD UI or via CLI:
```bash
kubectl get app enterprise-orders -n argocd
# Status should be: Synced
```

### Validate Application 1: Inventory API (Postgres + Redis)
The inventory API is exposed as a ClusterIP. You can test it via port-forward:
```bash
kubectl port-forward svc/inventory-api-svc -n microservices-lab 8081:80
```
Open your browser or use curl: `http://localhost:8081/health`

### Validate Application 2: Nishant DevOps Lab WebApp (MySQL)
The web app is exposed via NodePort on port **30005**.
- If using Minikube: `minikube service nishant-webapp-svc -n microservices-lab --url`
- If using a Cloud VM: `http://<VM-IP>:30005`
- If using port-forward: 
  ```bash
  kubectl port-forward svc/nishant-webapp-svc -n microservices-lab 5000:80
  ```
  Then access `http://localhost:5000`

### Test "Self-Healing"
Delete the webapp deployment manually and watch ArgoCD recreate it:
```bash
kubectl delete deployment nishant-webapp -n microservices-lab
# Wait 30s...
kubectl get deployments -n microservices-lab
```

### Test "Auto-Sync"
Update the image version in your Git repository. ArgoCD will detect the change and update the cluster automatically.

---

## 5. Automated CI/CD with GitHub Actions
To automate the build and push process, create a GitHub Action workflow in `.github/workflows/ci.yml`.

### Step 1: Add Secrets to GitHub
Go to your repo **Settings > Secrets and variables > Actions** and add:
- `DOCKER_USERNAME`: Your Docker Hub username.
- `DOCKER_PASSWORD`: Your Docker Hub PAT (Personal Access Token).

### Step 2: Create Workflow File
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
    paths:
      - 'app/**'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and Push
        uses: docker/build-push-action@v4
        with:
          context: ./app/backend
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/order-api:${{ github.sha }}

      - name: Update Kubernetes Manifest
        run: |
          sed -i "s|image:.*|image: ${{ secrets.DOCKER_USERNAME }}/order-api:${{ github.sha }}|g" manifests/inventory-app.yml
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add manifests/inventory-app.yml
          git commit -m "Update image to ${{ github.sha }}"
          git push
```

---

## 6. Cleanup
```bash
kubectl delete application enterprise-orders -n argocd
```

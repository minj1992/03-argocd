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

### Step C: Deploy the Application
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

### Test "Self-Healing"
Delete a deployment manually and watch ArgoCD recreate it within seconds:
```bash
kubectl delete deployment order-api -n microservices-lab
# Wait 30s...
kubectl get deployments -n microservices-lab
```

### Test "Auto-Sync"
Update the image version in your Git repository. ArgoCD will detect the change and update the cluster automatically.

---

## 5. Cleanup
```bash
kubectl delete application enterprise-orders -n argocd
```

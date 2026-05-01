# ArgoCD App of Apps Pattern

## 🔹 1. Git Repository Structure
```text
Git Repo
│
├── root-app.yaml
│
└── apps/
    ├── app1/
    │   ├── child-app.yaml
    │   └── manifests/
    │       ├── deployment.yaml
    │       └── service.yaml
    │
    └── app2/
        ├── child-app.yaml
        └── manifests/
            ├── deployment.yaml
            └── service.yaml
```

## 🔹 2. Argo CD Logical Flow
```text
                 +----------------------+
                 |   Argo CD Server     |
                 +----------+-----------+
                            |
                            |
                            v
                 +----------------------+
                 |   Root Application   |
                 |   (root-app.yaml)    |
                 |   path: apps/        |
                 +----------+-----------+
                            |
        -------------------------------------------
        |                                         |
        v                                         v
+------------------------+           +------------------------+
|   Child Application    |           |   Child Application    |
|       (app1)           |           |       (app2)           |
| child-app.yaml         |           | child-app.yaml         |
| path: app1/manifests   |           | path: app2/manifests   |
+-----------+------------+           +-----------+------------+
            |                                    |
            v                                    v
+------------------------+           +------------------------+
|   Kubernetes Resources |           |   Kubernetes Resources |
|   (Deployment, SVC)    |           |   (Deployment, SVC)    |
+-----------+------------+           +-----------+------------+
            |                                    |
            v                                    v
     +-------------+                      +-------------+
     |   Pods      |                      |   Pods      |
     +-------------+                      +-------------+
```

## 🔹 3. What Actually Happens (Step Flow)
1. `kubectl apply -f root-app.yaml`
2. Argo CD creates:
   → **Root Application**
3. Root Application reads:
   → `apps/`
4. Root finds:
   → `app1/child-app.yaml`
   → `app2/child-app.yaml`
5. Root creates:
   → **Application: app1**
   → **Application: app2**
6. Child apps start syncing:
   → `app1` reads `apps/app1/manifests/`
   → `app2` reads `apps/app2/manifests/`
7. Kubernetes gets:
   → Deployments
   → Services
   → Pods

## 🔹 4. Ownership Separation (Very Important)
**Root App**
   └── Owns ONLY:
       → Child Application CRDs

**Child Apps**
   └── Own:
       → Deployment
       → Service
       → Pods

## 🔹 5. What NOT to do (Wrong Design)
❌ **BAD (overlapping ownership)**
```text
Root App  ─┐
           ├── manages same manifests/
Child App ─┘
```
**Result:**
→ Conflict
→ OutOfSync
→ ArgoCD confusion

## 🔹 6. Clean Mental Model
*   **Root App** = Manager (creates apps)
*   **Child App** = Worker (deploys app)
*   **Kubernetes** = Runs workload

## 🔹 Final One-line Understanding
Root reads folders → creates child apps → child apps deploy workloads → pods run.

# How to Push This Project to GitHub

Your repo: https://github.com/Fariha12t/Serverless-Real-Time-Analytics-Platform

---

## Step-by-Step

### 1. Install Git (if not already)
- **Windows**: https://git-scm.com/download/win  
- **Mac**: `brew install git`  
- **Ubuntu/WSL**: `sudo apt install git`

---

### 2. Configure Git (first time only)
```bash
git config --global user.name "Fariha12t"
git config --global user.email "your-email@example.com"
```

---

### 3. Go into the project folder
```bash
cd Serverless-Real-Time-Analytics-Platform
```

---

### 4. Initialize Git and connect to GitHub
```bash
git init
git remote add origin https://github.com/Fariha12t/Serverless-Real-Time-Analytics-Platform.git
```

---

### 5. Stage and commit all files
```bash
git add .
git commit -m "feat: initial project — serverless real-time analytics platform

- Terraform IaC: API Gateway, Kinesis, Firehose, DynamoDB, Athena, S3
- Lambda functions: ingest, processor (Kinesis trigger), query API
- Real-time dashboard frontend with Chart.js
- CloudWatch alarms and monitoring
- Full README with architecture, cost estimates, and quick start"
```

---

### 6. Push to GitHub
```bash
git branch -M main
git push -u origin main
```

> GitHub will prompt for your username and a **Personal Access Token** (not your password).  
> Create a token at: https://github.com/settings/tokens → "Generate new token (classic)"  
> Tick: `repo` scope → Generate → copy it as your password.

---

### 7. Verify on GitHub
Open https://github.com/Fariha12t/Serverless-Real-Time-Analytics-Platform  
You should see all files including the README rendered on the homepage. ✅

---

## Optional: Add GitHub Actions CI

Create `.github/workflows/terraform-validate.yml` to auto-validate Terraform on every push:

```yaml
name: Terraform Validate
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.8"
      - run: terraform init -backend=false
        working-directory: terraform
      - run: terraform validate
        working-directory: terraform
```

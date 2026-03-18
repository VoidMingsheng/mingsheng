# Upload To GitHub

This folder is prepared for a safe GitHub upload.

## What is included
- Source code for the Telegram schedule agent
- `README.md`
- `NOTE.md`
- `.env.example`
- Railway deployment files

## What is not included
- Your real `.env`
- SQLite data
- Logs
- Telegram, OpenAI, or Railway secrets

## Safe upload steps
Run these commands inside this folder:

```powershell
git init -b main
git config user.name "YOUR_NAME"
git config user.email "YOUR_EMAIL"
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Before pushing
1. Confirm `.env` is not present in this folder
2. Review `.env.example`
3. Review `README.md` and `NOTE.md`
4. Make sure no secrets were pasted into source files

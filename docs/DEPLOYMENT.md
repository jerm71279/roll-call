# Deployment — [[PROJECT_TITLE]]

## Render.com (Static Site)

1. Connect `[[GITHUB_REPO]]` to Render.com
2. Set **Publish Directory** to `./frontend`
3. No build command needed — pure static files
4. Auto-deploys on push to `main`

## Environment Variables (Render Dashboard)

Set these in Render → Environment:

```
[[ENV_VARS]]
```

## Local Preview

```bash
cd frontend && python3 -m http.server 8080
# Open http://localhost:8080
```

## Manual Deploy

```bash
git push origin main
# Render auto-deploys within ~30 seconds
```

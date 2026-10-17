# DEPI House Dashboard

**Public website:** https://omarwolf28.github.io/depi-house-dashboard/

The free GitHub Pages version in `docs/` runs XGBoost predictions directly in the visitor's browser. It includes the original notebook's 11 plots, interactive market analysis, a property map, nearby sales, and model diagnostics. The browser evaluator reproduces the notebook pipeline's imputation, robust scaling, ZIP encoding, sparse feature handling, and all 300 fitted trees. Validation against all 4,323 held-out homes produced exactly the same predictions as the Python model.

GitHub Pages publishes `main` → `/docs`. Visitors need no account or payment card. No server needs to stay running. Map tiles still require an internet connection. Market charts describe all cleaned sales; the original notebook gallery retains its source plots.

The original Python Dash application is retained in the repository root. The instructions below apply only if deploying that Python version on a separate host.

This package hosts the real Python Dash application, original notebook plots, and the notebook's fitted XGBoost model. Training is not performed on the web server.

## Publish on Render

1. Upload the contents of this folder to a GitHub repository, including `artifacts/notebook_models.joblib` and `artifacts/notebook_manifest.json`. This deployment folder deliberately includes the model files that are ignored in the development project.
2. Sign in to Render and choose **New → Blueprint**, then connect that repository. The included `render.yaml` configures the Docker web service.
3. Review the selected plan and deploy. After its health check succeeds, Render provides a public HTTPS address. Share that address with visitors.

The blueprint requests Render's free plan. Confirm the plan available in your account before deploying. Free services can sleep when inactive, so the first visit may take time to load. No custom domain is needed.

The production server listens on Render's assigned `PORT` and uses Gunicorn. `/health` confirms the application loaded its model. Dependencies are pinned to the versions used to train the serialized model. Only the selected model is loaded, keeping memory and package size small; comparison metrics and original plots are retained.

To rebuild this package from the development project, run `python prepare_publish.py`. Refresh the notebook first if the dataset or notebook code changed.

Official instructions: https://render.com/docs/deploy-flask and https://render.com/docs/blueprint-spec.

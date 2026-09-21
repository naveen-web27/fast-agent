# RightConnect Web UI

- `pages/marketplace.html`: marketplace discovery and request workspace.
- `pages/auth.html`: mobile-first role selection, sign-in, and onboarding.
- `assets/`: RightConnect logos and future local images.

The frontend currently uses static HTML for fast product validation. The next conversion should move CSS and JavaScript into `frontend/css/` and `frontend/js/`, then connect each screen to the FastAPI endpoints.
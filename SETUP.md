# EcoSpark Streamlit: setup

## 1. Supabase (database + photo storage)
1. Create a free project at supabase.com.
2. SQL Editor -> paste `schema.sql` -> Run.
3. Project Settings -> API: copy the **Project URL** and the **service_role** key.

## 2. Google sign-in
1. console.cloud.google.com -> create a project -> APIs & Services -> OAuth consent screen (External) -> fill in the app name and your email.
2. Credentials -> Create credentials -> OAuth client ID -> Web application.
3. Authorized redirect URIs (add both):
   - `http://localhost:8501/oauth2callback`
   - `https://YOUR-APP.streamlit.app/oauth2callback`
4. Copy the Client ID and Client secret.
5. Under OAuth consent screen, click **Publish app** so people other than test users can sign in.

## 3. Run locally
```
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then fill it in
streamlit run app.py
```

## 4. Deploy (free)
1. Push this folder to a GitHub repo (the `.gitignore` keeps secrets out).
2. share.streamlit.io -> New app -> pick the repo, main file `app.py`.
3. App settings -> Secrets -> paste your filled-in secrets.
4. Make sure the deployed `redirect_uri` matches the Google setting exactly.

## 5. Check it works
- Sign in with josif.zoev123@gmail.com: you should see "Админ", the **Админ** page, delete buttons and the news form.
- Sign in with another Google account: it can post and comment after accepting the terms, but sees no delete buttons and no news form.
- Change `TERMS_VERSION` in `app.py` whenever you edit the terms; everyone must accept again.

## Before launch
Have a lawyer review the terms (`TERMS_MD` in `app.py`), especially the marketing licence, the sale/transfer clause and the rules about children.

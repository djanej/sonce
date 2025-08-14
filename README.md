Dobrodošli v repozitorij Spletne Strani Pisarne Sonce.

**⚠️ Lastnina in pravice:**
Vse vsebine, koda, dokumentacija in drugi materiali v tem repozitoriju so **last avtorjev/lastnikov repozitorija Sonce**.  
Kopiranje, distribuiranje ali uporaba brez dovoljenja lastnika ni dovoljena.  

© 2025 Sonce. Vse pravice pridržane.

---

Če imate vprašanja glede uporabe ali dovoljenj, nas kontaktirajte.

## ADMIN SETUP (Netlify CMS + GitHub)

Follow these steps to enable login at `/admin` and publish posts to `_posts` rendered at `/blog`.

1) Create a GitHub OAuth App
- Homepage URL: `https://sonce.org`
- Authorization callback URL: `https://sonce.org/admin/auth/github/callback`

Example (CLI-style placeholders):
```bash
# Go to GitHub Settings » Developer settings » OAuth Apps and create a new app
# Name: Sonce CMS
# Homepage URL: https://sonce.org
# Authorization callback URL: https://sonce.org/admin/auth/github/callback
```

2) Deploy an OAuth proxy (recommended)
- Recommended proxy: `netlify-cms-oauth` compatible server
- You can deploy to Vercel or Netlify. One-click deploy hint for Vercel:
```bash
# Deploy a GitHub OAuth proxy (example project)
# Vercel one-liner (replace with your repo or template):
vercel --prod
```
- After deployment, note the public URL of your proxy (e.g., `https://your-proxy.example.com`).

3) Configure the admin config
- Edit `admin/config.yml` and uncomment + set these values:
```yaml
backend:
  name: github
  repo: "djanej/sonce"
  branch: "main"
  auth_endpoint: "https://YOUR_OAUTH_PROXY_URL/auth"
  app_id: "YOUR_GITHUB_OAUTH_CLIENT_ID"
```

4) Test the flow
- Visit `/admin`
- Login with GitHub via the OAuth proxy
- Create a new Post and publish
- Confirm a commit appears in `_posts/` in GitHub
- Visit `/blog` and check the new post is listed

5) Security reminder
- Do NOT commit secrets (client secrets, tokens) to this repo.
- Only the public `app_id` (client ID) and proxy URL belong in `admin/config.yml`. Never commit the client secret.

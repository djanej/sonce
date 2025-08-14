Dobrodošli v repozitorij Spletne Strani Pisarne Sonce.

**⚠️ Lastnina in pravice:**
Vse vsebine, koda, dokumentacija in drugi materiali v tem repozitoriju so **last avtorjev/lastnikov repozitorija Sonce**.  
Kopiranje, distribuiranje ali uporaba brez dovoljenja lastnika ni dovoljena.  

© 2025 Sonce. Vse pravice pridržane.

---

Če imate vprašanja glede uporabe ali dovoljenj, nas kontaktirajte.

---

## ADMIN SETUP

### GitHub OAuth App Setup
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Fill in the following details:
   - Application name: "Your Site Name CMS"
   - Homepage URL: `https://yourdomain.com`
   - Authorization callback URL: `https://yourdomain.com/admin/`
4. Copy the Client ID and Client Secret

### OAuth Proxy Deployment
Deploy an OAuth proxy to handle GitHub authentication:

**Option 1: Vercel (Recommended)**
- Fork [netlify-cms-oauth-provider-node](https://github.com/vencax/netlify-cms-oauth-provider-node)
- Deploy to Vercel
- Update `admin/config.yml` with your proxy URL and GitHub Client ID

**Option 2: Netlify Functions**
- Create a Netlify function for OAuth handling
- Configure environment variables for GitHub OAuth

### Configuration Updates
1. Update `admin/config.yml`:
   - Replace `OWNER/REPO` with your actual GitHub repository path
   - Uncomment and set `auth_endpoint` and `app_id` with your OAuth proxy details
2. Ensure your repository has the correct branch name (default: "main")

### Access Admin Panel
Navigate to `/admin` on your site to access the Netlify CMS interface.

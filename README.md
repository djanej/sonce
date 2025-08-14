Dobrodošli v repozitorij Spletne Strani Pisarne Sonce.

**⚠️ Lastnina in pravice:**
Vse vsebine, koda, dokumentacija in drugi materiali v tem repozitoriju so **last avtorjev/lastnikov repozitorija Sonce**.  
Kopiranje, distribuiranje ali uporaba brez dovoljenja lastnika ni dovoljena.  

© 2025 Sonce. Vse pravice pridržane.

---

Če imate vprašanja glede uporabe ali dovoljenj, nas kontaktirajte.

---

## ADMIN SETUP

### Prerequisites
Before setting up the blog, you need to install Ruby and Jekyll:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ruby-full build-essential
gem install jekyll bundler
```

**macOS:**
```bash
# Install Homebrew first if you haven't
brew install ruby
gem install jekyll bundler
```

**Windows:**
- Download and install Ruby from https://rubyinstaller.org/
- Install Jekyll: `gem install jekyll bundler`

### Initial Setup
1. Install dependencies:
   ```bash
   bundle install
   ```

2. Test locally:
   ```bash
   bundle exec jekyll serve
   ```
   Visit `http://localhost:4000` to see your site

### GitHub OAuth App Setup
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Fill in the following details:
   - Application name: "Sonce CMS"
   - Homepage URL: `https://sonce.org`
   - Authorization callback URL: `https://sonce.org/admin/`
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
   - Replace `OWNER/REPO` with your actual GitHub repository path (e.g., "djanej/sonce.org")
   - Uncomment and set `auth_endpoint` and `app_id` with your OAuth proxy details
2. Ensure your repository has the correct branch name (default: "main")

### Blog Integration
The blog system includes:
- **Jekyll setup**: Complete Jekyll configuration for static site generation
- **Layouts**: Default and post-specific layouts
- **Styling**: Basic CSS for blog appearance
- **Collections**: Posts stored in `_posts/`
- **RSS Feed**: Available at `/feed.xml`
- **Sitemap**: Auto-generated sitemap

### Content Management
- **Create posts**: Use Netlify CMS at `/admin` or create markdown files in `_posts/`
- **Post format**: Use front matter with title, date, description, author, and layout
- **Images**: Store in `assets/uploads/` (automatically managed by CMS)
- **Markdown**: Full markdown support for rich content

### Deployment
1. **Local testing**: `bundle exec jekyll serve`
2. **Build**: `bundle exec jekyll build`
3. **Deploy**: Upload `_site/` folder to your web server

### Access Points
- **Admin Panel**: `/admin` - Content management interface
- **Blog Listing**: `/blog/` - All blog posts
- **Individual Posts**: `/blog/post-title` - Individual post pages
- **RSS Feed**: `/feed.xml` - RSS feed for subscribers

### Troubleshooting
- **Jekyll not working**: Ensure Ruby and Jekyll are properly installed
- **Posts not showing**: Check front matter format and file naming
- **Admin access issues**: Verify OAuth configuration and proxy setup
- **Build errors**: Check Jekyll configuration and dependencies

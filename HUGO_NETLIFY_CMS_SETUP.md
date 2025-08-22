# Hugo + Netlify CMS Setup Guide

## 🎉 Setup Complete!

Your website now has Hugo + Netlify CMS integrated! The news button has been added to your header navigation, and your father can easily manage news posts through the admin interface.

## 📁 What Was Created

### Hugo Structure
- `config.toml` - Hugo configuration with menu setup
- `layouts/` - Hugo templates for news pages
- `content/news/` - News posts directory
- `static/admin/` - Netlify CMS admin interface
- `archetypes/` - Templates for new content
- `netlify.toml` - Netlify deployment configuration

### News System
- News button added to main navigation (both desktop and mobile)
- `/news/` page displays all news posts
- `/admin/` interface for content management
- Sample posts created for testing

## 🚀 How to Get This Working

### Step 1: Deploy to Netlify

1. **Push your changes to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add Hugo + Netlify CMS integration"
   git push origin main
   ```

2. **Connect to Netlify**:
   - Go to [Netlify](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository
   - Build settings should auto-detect (Hugo)
   - Deploy!

### Step 2: Enable Netlify Identity

1. **In your Netlify dashboard**:
   - Go to Site Settings → Identity
   - Click "Enable Identity"
   - Under "Registration preferences", select "Invite only"
   - Under "External providers", enable Google or GitHub (optional)

2. **Enable Git Gateway**:
   - Still in Identity settings
   - Scroll to "Services" → "Git Gateway"
   - Click "Enable Git Gateway"

### Step 3: Invite Your Father

1. **In Netlify Identity**:
   - Go to "Identity" tab in your site dashboard
   - Click "Invite users"
   - Enter your father's email
   - He'll receive an invitation email

### Step 4: Test the Admin Interface

1. **Visit your site's `/admin/` page**
2. **Your father should**:
   - Click the invitation link from email
   - Set up his password
   - Access the admin interface at `yoursite.com/admin/`

## 📝 How to Use the News System

### For Your Father (Content Editor):

1. **Access Admin**: Go to `yoursite.com/admin/`
2. **Login**: Use Netlify Identity credentials
3. **Create News**: 
   - Click "Novice" (News)
   - Click "New Novice"
   - Fill in the form:
     - **Naslov**: Title of the news
     - **Datum objave**: Publication date
     - **Povzetek**: Summary (optional)
     - **Avtor**: Author name (defaults to "Sindikat Sonce Koper")
     - **Objavljeno**: Uncheck to publish (checked = draft)
     - **Ključne besede**: Tags for SEO
     - **Glavna slika**: Featured image (optional)
     - **Vsebina**: Main content in Markdown

4. **Publish**: 
   - Uncheck "Objavljeno" (draft) to publish
   - Click "Publish"
   - Changes will automatically deploy to your site!

### For Visitors:

- Click "Novice" in the main navigation
- Browse all published news
- Click individual articles to read full content
- Mobile-friendly interface

## 🔧 Technical Details

### File Structure
```
/
├── config.toml                 # Hugo config with menu
├── netlify.toml               # Netlify deployment config
├── package.json               # Project metadata
├── content/
│   ├── _index.md             # Homepage content
│   └── news/                 # News posts
│       ├── _index.md         # News section page
│       └── *.md              # Individual news posts
├── layouts/
│   ├── _default/
│   │   ├── baseof.html       # Base template
│   │   ├── home.html         # Homepage template
│   │   ├── list.html         # List pages template
│   │   └── single.html       # Single post template
│   ├── news/
│   │   ├── list.html         # News list template
│   │   └── single.html       # News post template
│   └── partials/
│       └── header.html       # Header with news button
├── static/
│   ├── admin/
│   │   ├── config.yml        # Netlify CMS config
│   │   └── index.html        # Admin interface
│   └── images/
│       └── uploads/          # Media uploads folder
└── public/                   # Generated site (auto-created)
```

### Navigation Updates
- Added "Novice" button to main navigation
- Added "Novice" to mobile menu
- Links point to `/news/` page
- Preserves all existing functionality

## 🛠️ Troubleshooting

### If Admin Interface Doesn't Work:
1. Check Netlify Identity is enabled
2. Verify Git Gateway is enabled
3. Ensure user is invited and confirmed
4. Check browser console for errors

### If News Don't Appear:
1. Ensure posts are not drafts (`draft: false`)
2. Check file is in `content/news/` directory
3. Verify frontmatter is correct
4. Rebuild and deploy

### If Images Don't Upload:
1. Check `static/images/uploads/` directory exists
2. Verify Netlify CMS config paths
3. Ensure proper permissions in Netlify

## 📱 Mobile Compatibility

- Responsive design for all screen sizes
- Mobile-optimized admin interface
- Touch-friendly navigation
- Fast loading with image optimization

## 🔒 Security Features

- Netlify Identity authentication
- Invite-only access to admin
- Git-based content versioning
- Secure media uploads

## 📈 SEO Benefits

- Automatic sitemap generation
- Meta tags for social sharing
- Structured data for news articles
- Fast loading times
- Mobile-first design

---

**Your Hugo + Netlify CMS integration is complete and ready to use!** 🎊

The news system is fully functional and your father can start creating content immediately after the Netlify setup is complete.
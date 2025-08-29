# GitHub Pages Deployment Guide

This project is configured with GitHub Actions to automatically build and deploy to GitHub Pages. Follow these steps to enable it:

1. Push your project to GitHub repository:

```bash
git push origin master
```

2. Go to your GitHub repository page and click on the "Settings" tab.

3. Click on "Pages" in the left navigation menu.

4. In the "Build and deployment" section, find the "Source" option:
   - Select "GitHub Actions" as the source

5. After the first deployment, you can access the online demo page at:
   ```
   https://font.tcg.cards
   ```

## Notes

- Every push to the `master` branch will automatically trigger the build and deployment process
- You can check the deployment progress and status in the "Actions" tab of your repository
- After successful deployment, the online demo page will be automatically updated

## Custom Domain Setup

The project is configured to use the custom domain `font.tcg.cards`. To make this work:

1. Go to your domain registrar and add the following DNS records:
   - Type: A
   - Name: font (or @ if you want to use the apex domain)
   - Value: 185.199.108.153
   - Value: 185.199.109.153
   - Value: 185.199.110.153
   - Value: 185.199.111.153

2. Or if you prefer using a CNAME:
   - Type: CNAME
   - Name: font
   - Value: Sunchy321.github.io

3. In your GitHub repository:
   - Go to Settings > Pages
   - Under "Custom domain", verify that `font.tcg.cards` is set
   - Check "Enforce HTTPS" for secure connections

Note: DNS propagation may take up to 24 hours. During this time, your site might be temporarily unavailable.

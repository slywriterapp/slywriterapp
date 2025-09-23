// Simple update proxy server (runs on your server)
// Fetches from private GitHub, serves to users publicly

const express = require('express')
const axios = require('axios')
const app = express()

const GITHUB_TOKEN = process.env.GITHUB_TOKEN
const REPO_OWNER = 'yourusername'
const REPO_NAME = 'slywriter'

// Proxy endpoint for Squirrel
app.get('/updates/RELEASES', async (req, res) => {
  try {
    // Fetch from private GitHub with token
    const response = await axios.get(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest`,
      {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    )

    // Find RELEASES file in assets
    const releasesAsset = response.data.assets.find(a => a.name === 'RELEASES')
    if (!releasesAsset) {
      return res.status(404).send('RELEASES file not found')
    }

    // Fetch actual RELEASES file content
    const releasesContent = await axios.get(releasesAsset.browser_download_url, {
      headers: { 'Authorization': `token ${GITHUB_TOKEN}` }
    })

    // Serve to Squirrel (no auth needed)
    res.type('text/plain')
    res.send(releasesContent.data)

  } catch (error) {
    console.error('Update check failed:', error)
    res.status(500).send('Update check failed')
  }
})

// Proxy for downloading actual files
app.get('/updates/:filename', async (req, res) => {
  try {
    const { filename } = req.params

    // Get latest release
    const response = await axios.get(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest`,
      {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    )

    // Find requested file
    const asset = response.data.assets.find(a => a.name === filename)
    if (!asset) {
      return res.status(404).send('File not found')
    }

    // Redirect to GitHub (with auth)
    const downloadUrl = asset.url
    const fileStream = await axios.get(downloadUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/octet-stream'
      },
      responseType: 'stream'
    })

    // Pipe to user (no auth needed)
    res.type('application/octet-stream')
    fileStream.data.pipe(res)

  } catch (error) {
    console.error('Download failed:', error)
    res.status(500).send('Download failed')
  }
})

// Analytics bonus
app.post('/updates/track', (req, res) => {
  const { version, userId } = req.body
  console.log(`User ${userId} updated to ${version}`)
  // Save to database, send to analytics, etc.
  res.json({ success: true })
})

app.listen(3000, () => {
  console.log('Update proxy server running on port 3000')
  console.log('Configure Squirrel to use: https://yourdomain.com/updates')
})

// Deploy this to Vercel, Render, or any Node host
// Then in your Electron app:
// "remoteReleases": "https://updates.slywriter.com/updates"
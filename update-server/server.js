const express = require('express')
const axios = require('axios')
const cors = require('cors')
require('dotenv').config()

const app = express()
app.use(cors())
app.use(express.json())

// Configuration
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || 'ghp_YOUR_TOKEN_HERE'
const REPO_OWNER = process.env.REPO_OWNER || 'yourusername'
const REPO_NAME = process.env.REPO_NAME || 'slywriter'
const PORT = process.env.PORT || 3001

// Cache latest release info for 5 minutes to reduce GitHub API calls
let releaseCache = {
  data: null,
  timestamp: 0
}
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'SlyWriter Update Server',
    status: 'running',
    endpoints: {
      'GET /updates/RELEASES': 'Squirrel update check',
      'GET /updates/latest': 'Latest version info',
      'GET /updates/download/:filename': 'Download update files'
    }
  })
})

// Get latest release info from GitHub (with caching)
async function getLatestRelease() {
  // Check cache
  if (releaseCache.data && Date.now() - releaseCache.timestamp < CACHE_DURATION) {
    console.log('Using cached release data')
    return releaseCache.data
  }

  console.log('Fetching fresh release data from GitHub...')
  try {
    const response = await axios.get(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest`,
      {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    )

    // Update cache
    releaseCache = {
      data: response.data,
      timestamp: Date.now()
    }

    return response.data
  } catch (error) {
    console.error('Failed to fetch release:', error.message)
    throw error
  }
}

// Squirrel.Windows update check endpoint
app.get('/updates/RELEASES', async (req, res) => {
  console.log('Update check from:', req.ip)

  try {
    const release = await getLatestRelease()

    // Find RELEASES file in assets
    const releasesAsset = release.assets.find(a => a.name === 'RELEASES')
    if (!releasesAsset) {
      console.log('No RELEASES file found in latest release')
      return res.status(404).send('No updates available')
    }

    // Fetch RELEASES file content from private repo
    const releasesResponse = await axios.get(releasesAsset.url, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/octet-stream'
      }
    })

    // Log update check
    console.log(`Update check successful - Version: ${release.tag_name}`)

    // Send RELEASES file to Squirrel (no auth needed!)
    res.type('text/plain')
    res.send(releasesResponse.data)

  } catch (error) {
    console.error('Update check failed:', error.message)
    res.status(500).send('Update check failed')
  }
})

// Download specific update files
app.get('/updates/download/:filename', async (req, res) => {
  const { filename } = req.params
  console.log(`Download request for: ${filename}`)

  try {
    const release = await getLatestRelease()

    // Find requested file
    const asset = release.assets.find(a => a.name === filename)
    if (!asset) {
      console.log(`File not found: ${filename}`)
      return res.status(404).send('File not found')
    }

    // Stream file from GitHub to client
    const response = await axios.get(asset.url, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/octet-stream'
      },
      responseType: 'stream'
    })

    // Set headers for download
    res.set({
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Content-Length': asset.size
    })

    // Pipe the file to client
    response.data.pipe(res)

    console.log(`Serving file: ${filename} (${asset.size} bytes)`)

  } catch (error) {
    console.error('Download failed:', error.message)
    res.status(500).send('Download failed')
  }
})

// Latest version info endpoint (for manual checks)
app.get('/updates/latest', async (req, res) => {
  try {
    const release = await getLatestRelease()

    res.json({
      version: release.tag_name,
      name: release.name,
      published_at: release.published_at,
      downloads: release.assets.map(a => ({
        name: a.name,
        size: a.size,
        download_count: a.download_count
      }))
    })
  } catch (error) {
    res.status(500).json({ error: 'Failed to get latest version' })
  }
})

// Analytics endpoint (track who's updating)
app.post('/updates/track', (req, res) => {
  const { version, platform, arch, oldVersion } = req.body
  console.log('Update tracked:', { version, platform, arch, oldVersion })

  // Here you could save to database, send to analytics service, etc.
  // For now, just log it

  res.json({ success: true })
})

// Health check for monitoring
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cache: {
      hasData: !!releaseCache.data,
      age: releaseCache.timestamp ? Date.now() - releaseCache.timestamp : null
    }
  })
})

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Update proxy server running on port ${PORT}`)
  console.log(`📦 Proxying updates from: github.com/${REPO_OWNER}/${REPO_NAME}`)
  console.log(`🔑 GitHub token: ${GITHUB_TOKEN ? 'Configured' : 'Missing!'}`)
  console.log('\nEndpoints:')
  console.log(`  - http://localhost:${PORT}/updates/RELEASES (for Squirrel)`)
  console.log(`  - http://localhost:${PORT}/updates/latest (version info)`)
  console.log(`  - http://localhost:${PORT}/health (health check)`)
})
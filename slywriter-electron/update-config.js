/**
 * Update Configuration
 * Switch between GitHub and custom server
 */

const updateConfig = {
  // Option 1: GitHub Releases (Recommended to start)
  github: {
    provider: 'github',
    owner: 'yourusername',
    repo: 'slywriter',
    private: false, // Set true for private repos (needs token)
    releaseType: 'release' // or 'prerelease' for beta
  },

  // Option 2: Your Own Server
  custom: {
    provider: 'generic',
    url: 'https://updates.slywriter.com',
    channel: 'stable', // or 'beta', 'dev'
    useMultipleRangeRequest: false // For resume support
  },

  // Option 3: Hybrid (GitHub + Your Analytics)
  hybrid: {
    provider: 'github',
    owner: 'yourusername',
    repo: 'slywriter',
    // But also ping your server for analytics
    beforeDownload: async (info) => {
      await fetch('https://api.slywriter.com/track-update', {
        method: 'POST',
        body: JSON.stringify({
          version: info.version,
          userId: getUserId(),
          timestamp: Date.now()
        })
      })
    }
  }
}

// Server structure if you go custom:
/*
your-server.com/
  └── updates/
      ├── latest.yml          # Version manifest
      ├── latest-mac.yml      # Mac manifest
      ├── SlyWriter-2.0.0.exe # Windows installer
      ├── SlyWriter-2.0.0.exe.blockmap # Delta info
      ├── SlyWriter-2.0.0.dmg # Mac installer
      └── beta/               # Beta channel
          ├── latest.yml
          └── SlyWriter-2.1.0-beta.exe
*/

module.exports = updateConfig
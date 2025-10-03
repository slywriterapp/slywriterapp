/**
 * Centralized Version Management
 * Single source of truth for app version across all components
 */

// Read version from package.json
const fs = require('fs')
const path = require('path')

let APP_VERSION = '2.1.7' // Fallback

try {
  const packagePath = path.join(__dirname, 'package.json')
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
  APP_VERSION = packageJson.version
} catch (e) {
  console.warn('Could not read version from package.json, using fallback:', APP_VERSION)
}

module.exports = {
  APP_VERSION,
  MINIMUM_SUPPORTED_VERSION: '2.0.0',  // Update this when you need to force users to upgrade

  // Helper to check if a version is outdated
  isVersionOutdated: (version) => {
    const normalize = (v) => v.split('.').map(n => parseInt(n))
    const current = normalize(version)
    const minimum = normalize(module.exports.MINIMUM_SUPPORTED_VERSION)

    for (let i = 0; i < 3; i++) {
      if (current[i] < minimum[i]) return true
      if (current[i] > minimum[i]) return false
    }
    return false
  }
}

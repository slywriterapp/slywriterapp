/**
 * Squirrel.Windows with Private GitHub Repository
 *
 * IMPORTANT: Private repos require authentication for updates
 */

// Option 1: EMBED TOKEN (Not Recommended - Token visible in app)
const embedTokenConfig = {
  squirrelWindows: {
    remoteReleases: `https://your-token@github.com/yourusername/slywriter`,
    // Problem: Token is embedded in the built app (security risk!)
  }
}

// Option 2: PUBLIC RELEASES ONLY (Recommended for Private Repos)
const publicReleasesConfig = {
  // Keep code private, but make releases public
  // Settings > General > Danger Zone > Override repository visibility
  // ✅ "Public releases" checkbox
  squirrelWindows: {
    remoteReleases: `https://github.com/yourusername/slywriter/releases/latest/download`,
    // Works without authentication!
  }
}

// Option 3: PROXY SERVER (Most Secure)
const proxyServerConfig = {
  squirrelWindows: {
    remoteReleases: `https://updates.slywriter.com/check`,
    // Your server fetches from private GitHub with server-side token
  }
}

// Option 4: USE PUBLIC REPO FOR RELEASES (Best Practice)
const separateReposConfig = {
  // Main code: github.com/yourusername/slywriter (private)
  // Releases: github.com/yourusername/slywriter-releases (public)
  squirrelWindows: {
    remoteReleases: `https://github.com/yourusername/slywriter-releases`,
  }
}
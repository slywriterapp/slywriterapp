const builder = require('electron-builder')
const Platform = builder.Platform

/**
 * Build script for creating professional installers
 *
 * This creates BOTH:
 * 1. Traditional NSIS installer (full .exe with everything)
 * 2. Squirrel installer (like Discord - with delta updates)
 */

async function build() {
  console.log('🚀 Building SlyWriter installers...\n')

  try {
    // Build for Windows with both targets
    const result = await builder.build({
      targets: Platform.WINDOWS.createTarget(['nsis', 'squirrel']),
      config: {
        appId: 'com.slywriter.desktop',
        productName: 'SlyWriter',
        directories: {
          output: 'dist',
          buildResources: 'build'
        },
        win: {
          target: [
            {
              target: 'nsis',
              arch: ['x64']
            },
            {
              target: 'squirrel',
              arch: ['x64']
            }
          ]
        },
        nsis: {
          oneClick: false,  // Allow user to choose install location
          allowToChangeInstallationDirectory: true,
          createDesktopShortcut: true,
          createStartMenuShortcut: true,
          installerIcon: 'assets/icon.ico',
          installerHeaderIcon: 'assets/icon.ico',
          artifactName: 'SlyWriter-Setup-${version}.exe'
        },
        squirrelWindows: {
          artifactName: 'SlyWriter-${version}-Setup.exe',
          remoteReleases: process.env.GH_TOKEN
            ? `https://github.com/${process.env.GH_OWNER || 'yourusername'}/${process.env.GH_REPO || 'slywriter'}`
            : null
        },
        publish: process.env.GH_TOKEN ? {
          provider: 'github',
          owner: process.env.GH_OWNER || 'yourusername',
          repo: process.env.GH_REPO || 'slywriter'
        } : null
      }
    })

    console.log('\n✅ Build complete!')
    console.log('\n📦 Generated installers:')
    console.log('  1. dist/SlyWriter-Setup-2.0.0.exe (Traditional NSIS installer)')
    console.log('  2. dist/SlyWriter-2.0.0-Setup.exe (Squirrel installer with delta updates)')
    console.log('\n📝 Notes:')
    console.log('  - NSIS: Full installer, choose install location, traditional')
    console.log('  - Squirrel: Like Discord, silent updates, delta patches')
    console.log('\nChoose based on your users:')
    console.log('  - Enterprise/Corporate → NSIS')
    console.log('  - Consumer/Gamers → Squirrel')

    return result
  } catch (error) {
    console.error('❌ Build failed:', error)
    process.exit(1)
  }
}

// Run build
build()
// SlyWriter Desktop v3.0.0
// TODO: Enable signature verification after purchasing code signing certificate
// Temporarily disabled until EV certificate is purchased ($249/year from SSL.com)
// SECURITY: This allows unsigned updates - MUST enable after getting certificate
// Steps: 1) Purchase cert, 2) Sign builds, 3) Remove this line
process.env.ELECTRON_UPDATER_ALLOW_UNSIGNED = 'true'

const { app, BrowserWindow, ipcMain, globalShortcut, Tray, Menu, screen, clipboard, shell, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, exec } = require('child_process')
const http = require('http')
const https = require('https')
const { autoUpdater } = require('electron-updater')

// Read version from package.json or use app.getVersion()
const APP_VERSION = app.getVersion()

// Handle Squirrel events (for installer/updater)
if (require('electron-squirrel-startup')) {
  app.quit()
}

// Try to load axios, fall back to http if not available
let axios
try {
  axios = require('axios')
} catch (e) {
  console.log('Axios not found, will use http module')
}

// Configure auto-updater
autoUpdater.autoDownload = true
autoUpdater.autoInstallOnAppQuit = true

// Wrap console methods to prevent EPIPE errors
const originalLog = console.log
const originalError = console.error
const originalWarn = console.warn

console.log = (...args) => {
  try {
    if (process.stdout && process.stdout.writable) {
      originalLog.apply(console, args)
    }
  } catch (e) {
    // Silently ignore EPIPE and other console errors
  }
}

console.error = (...args) => {
  try {
    if (process.stderr && process.stderr.writable) {
      originalError.apply(console, args)
    }
  } catch (e) {
    // Silently ignore EPIPE and other console errors
  }
}

console.warn = (...args) => {
  try {
    if (process.stderr && process.stderr.writable) {
      originalWarn.apply(console, args)
    }
  } catch (e) {
    // Silently ignore EPIPE and other console errors
  }
}

// Global error handlers to prevent crashes
process.on('uncaughtException', (error) => {
  // Use wrapped console.error
  console.error('Uncaught Exception:', error.message)
  // Don't exit, just log the error
})

process.on('unhandledRejection', (reason, promise) => {
  // Use wrapped console.error
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
  // Don't exit, just log the error
})

// Handle EPIPE errors specifically
process.stdout.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Silently ignore EPIPE errors
    return
  }
  console.error('stdout error:', err)
})

process.stderr.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Silently ignore EPIPE errors
    return
  }
  console.error('stderr error:', err)
})

let mainWindow
let overlayWindow
let overlayIntervalId = null
let tray
let nextServer
let nextPort = 3000
let typingServerProcess = null

// Flag to track if we're quitting for an auto-update installation
let isQuittingForUpdate = false

// Enable live reload for Electron in dev mode
const isDev = process.argv.includes('--dev')

// Import Python setup
let pythonSetup = null
try {
  pythonSetup = require('./setup-python')
  console.log('Python setup module loaded successfully')
} catch (e) {
  console.log('Python setup module not found, will use system Python')
}

// ============== MAC AUTOMATION PERMISSION ONBOARDING ==============
// macOS requires explicit Automation permission for keyboard simulation
// This function triggers the permission dialog and guides the user through setup
// IMPORTANT: This is now called AFTER user sign-in to maximize trust

async function checkMacAutomationPermission() {
  // Only run on macOS
  if (process.platform !== 'darwin') {
    return true
  }

  console.log('[Mac] Checking automation permission...')

  // Check if we've already completed onboarding
  const store = require('electron-store')
  const appStore = new store()
  const onboardingCompleted = appStore.get('macAutomationOnboarded', false)

  if (onboardingCompleted) {
    console.log('[Mac] Automation onboarding already completed')
    return true
  }

  // Show friendly onboarding dialog AFTER user has seen the app
  const result = await dialog.showMessageBox({
    type: 'info',
    title: 'One Quick Step to Enable Typing',
    message: 'SlyWriter needs your permission to type for you',
    detail: `To simulate natural typing, macOS needs you to grant SlyWriter permission to control your keyboard.

This is a standard macOS security feature - you'll see it with any typing automation app. Your data stays private and local.

What happens next:
1. Click "Enable Typing"
2. macOS will show a permission prompt
3. Go to System Settings > Privacy & Security > Automation
4. Check the box next to SlyWriter

This only takes 30 seconds and you'll only need to do it once!`,
    buttons: ['Enable Typing', 'Later'],
    defaultId: 0,
    cancelId: 1,
    noLink: true
  })

  if (result.response === 1) {
    // User clicked Later - don't quit, just skip for now
    console.log('[Mac] User postponed permission setup')
    return true
  }

  // Try to trigger the permission prompt by simulating a keypress
  console.log('[Mac] Attempting to trigger automation permission prompt...')

  try {
    // Use AppleScript to simulate a keypress - this triggers the permission dialog
    const { execSync } = require('child_process')

    // This AppleScript will attempt to type something, triggering the permission dialog
    execSync(`osascript -e 'tell application "System Events" to keystroke ""'`, {
      timeout: 5000
    })

    console.log('[Mac] Keystroke simulation attempted')
  } catch (e) {
    console.log('[Mac] Keystroke simulation failed (expected if permission not granted):', e.message)
  }

  // Wait a moment for the user to see the permission dialog
  await new Promise(resolve => setTimeout(resolve, 500))

  // Show follow-up dialog with clear instructions
  const followUp = await dialog.showMessageBox({
    type: 'info',
    title: 'Enable SlyWriter in System Settings',
    message: 'Almost there! Just enable SlyWriter in your settings.',
    detail: `If you saw a macOS prompt:
• Click "Open System Settings"
• Find SlyWriter in the Automation list
• Check the box to enable it

If no prompt appeared:
1. Open System Settings (click the Apple menu)
2. Go to Privacy & Security > Automation
3. Find SlyWriter and check the box

Once enabled, typing will work automatically!`,
    buttons: ['Done - I Enabled It', 'Open System Settings', 'Skip for Now'],
    defaultId: 0,
    cancelId: 2,
    noLink: true
  })

  if (followUp.response === 2) {
    console.log('[Mac] User skipped permission setup')
    return true
  }

  if (followUp.response === 1) {
    // Open System Preferences to Automation (not Accessibility)
    const { shell } = require('electron')
    shell.openExternal('x-apple.systempreferences:com.apple.preference.security?Privacy_Automation')

    // Wait for user to grant permission
    await dialog.showMessageBox({
      type: 'info',
      title: 'Enable SlyWriter',
      message: 'Check the box next to SlyWriter',
      detail: 'Once you\'ve enabled SlyWriter in the Automation list, click OK.',
      buttons: ['OK'],
      defaultId: 0
    })
  }

  // Mark onboarding as completed (user said they enabled it)
  appStore.set('macAutomationOnboarded', true)

  // Test if permission was actually granted
  try {
    const { execSync } = require('child_process')
    execSync(`osascript -e 'tell application "System Events" to keystroke ""'`, {
      timeout: 5000
    })
    console.log('[Mac] Automation permission appears to be granted!')
    return true
  } catch (e) {
    console.log('[Mac] Automation permission may not be granted yet')

    // Show helpful tip but continue anyway
    await dialog.showMessageBox({
      type: 'info',
      title: 'Typing Permission Not Yet Enabled',
      message: 'You can enable this anytime',
      detail: `If typing doesn't work when you try it:

1. Open System Settings (Apple menu)
2. Privacy & Security > Automation
3. Check the box next to SlyWriter
4. Try typing again - no restart needed!

The app will work for everything else in the meantime.`,
      buttons: ['Got It'],
      defaultId: 0
    })

    return true // Continue anyway
  }
}
// ============== END MAC AUTOMATION PERMISSION ONBOARDING ==============

// Start the typing server (backend_desktop.py - desktop app backend)
async function startTypingServer() {
  console.log('Starting typing server...')

  // Check if app is packaged
  const isPackaged = app.isPackaged

  // Get the path to the typing server
  const typingServerPath = isPackaged
    ? path.join(process.resourcesPath, 'backend_desktop.py')  // Production: resources folder
    : path.join(__dirname, '..', 'backend_desktop.py')  // Development: parent directory

  console.log('📍 Typing server path:', typingServerPath)
  console.log('📁 Current directory:', __dirname)
  console.log('📦 isPackaged:', isPackaged)
  console.log('✅ Backend file exists:', fs.existsSync(typingServerPath))
  sendSplashProgress(`Locating backend: ${path.basename(typingServerPath)}`)

  // Check if the file exists
  if (!fs.existsSync(typingServerPath)) {
    console.error('Backend API file not found at:', typingServerPath)
    console.error('Looking for backend_desktop.py in:', process.resourcesPath)

    // List files in resources directory to debug
    if (isPackaged) {
      const resourcesDir = process.resourcesPath
      console.log('Files in resources directory:')
      try {
        const files = fs.readdirSync(resourcesDir)
        files.forEach(file => console.log('  -', file))
      } catch (e) {
        console.error('Could not read resources directory:', e.message)
      }
    }

    // Show error to user
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.executeJavaScript(`
        console.error('Typing server file not found. Typing features will not work.');
      `)
    }
    return
  }

  // Try to use bundled Python first, then fall back to system Python
  let pythonPath = null
  let serverStarted = false

  // Setup bundled Python if available
  if (pythonSetup) {
    try {
      // Initialize Python paths with writable directory
      pythonSetup.init(app.getPath('userData'))
      console.log('Setting up bundled Python...')
      sendSplashProgress('Setting up Python environment...')

      pythonPath = await pythonSetup.setupPython((message, progress) => {
        console.log(`Setup progress: ${message} (${progress}%)`)
        sendSplashProgress(message)

        // Also log to main window console if it exists
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.executeJavaScript(`
            console.log('📦 ${message}');
          `).catch(() => {})
        }
      })

      console.log('✅ Bundled Python ready at:', pythonPath)
      console.log('📍 Verifying Python executable exists:', fs.existsSync(pythonPath))
      sendSplashProgress('✅ Python environment ready')

      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.log('✅ Python environment ready');
        `).catch(() => {})
      }
    } catch (error) {
      console.error('Failed to setup bundled Python:', error)

      // Create user-friendly error message
      let errorMsg = 'Python setup failed:\n'
      if (error.message.includes('ECONNREFUSED') || error.message.includes('ETIMEDOUT') || error.message.includes('network')) {
        errorMsg += '• Network connection issue\n'
        errorMsg += '• Check your internet connection and try again'
      } else if (error.message.includes('EACCES') || error.message.includes('permission')) {
        errorMsg += '• Permission denied\n'
        errorMsg += '• Try running SlyWriter as Administrator'
      } else if (error.message.includes('ENOSPC') || error.message.includes('space')) {
        errorMsg += '• Insufficient disk space\n'
        errorMsg += '• Free up at least 500MB and retry'
      } else {
        errorMsg += `• ${error.message}\n`
        errorMsg += '\nAttempting to use system Python as fallback...'
      }

      // Show error in splash window
      sendSplashError(errorMsg)

      // Wait 3 seconds to let user see the error before attempting fallback
      await new Promise(resolve => setTimeout(resolve, 3000))
      sendSplashProgress('Attempting system Python fallback...')

      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.error('⚠️ Failed to setup bundled Python: ${errorMsg}');
          console.log('⏳ Will attempt to use system Python as fallback...');
        `).catch(() => {})
      }
      pythonPath = null // Ensure fallback to system Python
    }
  }

  // If bundled Python is available, use it
  console.log('🔍 Checking bundled Python:')
  console.log('   pythonPath:', pythonPath)
  console.log('   exists:', pythonPath ? fs.existsSync(pythonPath) : 'N/A')
  sendSplashProgress(`Checking Python at: ${pythonPath || 'null'}`)

  if (pythonPath && fs.existsSync(pythonPath)) {
    console.log('✅ Using bundled Python to start backend server')
    sendSplashProgress('✅ Found bundled Python, starting server...')
    try {
      sendSplashProgress('Starting backend server...')

      const backendDir = path.dirname(typingServerPath)
      console.log('🐍 Backend directory:', backendDir)
      sendSplashProgress(`Backend dir: ${backendDir}`)

      // Embedded Python ignores PYTHONPATH - use Python -c to add to sys.path
      const pythonCode = `import sys; sys.path.insert(0, r'${backendDir}'); __file__ = r'${typingServerPath}'; exec(open(r'${typingServerPath}').read())`

      console.log('🐍 Running Python with explicit sys.path injection')
      sendSplashProgress('Injecting sys.path for modules...')

      typingServerProcess = spawn(pythonPath, ['-c', pythonCode], {
        cwd: backendDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
        env: {
          ...process.env,
          SLYWRITER_CONFIG_DIR: app.getPath('userData')
        }
      })

      typingServerProcess.stdout.on('data', (data) => {
        console.log(`Typing server: ${data}`)
      })

      typingServerProcess.stderr.on('data', (data) => {
        const message = data.toString()
        console.log(`Typing server stderr: ${message}`)

        // Log errors to splash screen for debugging
        if (message.includes('Error') || message.includes('error') || message.includes('Exception') || message.includes('Traceback')) {
          console.error(`⚠️ Backend error: ${message}`)
          sendSplashProgress(`Backend error: ${message.substring(0, 100)}`)
        }

        // Check if server started successfully
        if (message.includes('Uvicorn running on') || message.includes('8000') || message.includes('Started server')) {
          serverStarted = true
          console.log('Typing server started successfully on port 8000 (bundled Python)')
          sendSplashProgress('✅ Backend server ready!')
          sendSplashComplete()

          // Notify the renderer process that server is ready
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.executeJavaScript(`
              console.log('✅ Typing server started successfully (bundled Python)');
            `).catch(() => {})
          }
        }
      })

      typingServerProcess.on('error', (error) => {
        console.error('Failed to start typing server with bundled Python:', error.message)
        let errorMsg = 'Failed to start backend server:\n'

        // Provide specific guidance based on error type
        if (error.code === 'ENOENT') {
          errorMsg += '• Python executable not found\n'
          errorMsg += '• This may happen if Python setup was interrupted\n\n'
          errorMsg += 'Click "Retry Setup" to download Python again.'
        } else if (error.code === 'EACCES' || error.code === 'EPERM') {
          errorMsg += '• Permission denied\n'
          errorMsg += '• Try running SlyWriter as Administrator\n'
          errorMsg += '• Or check your antivirus settings'
        } else {
          errorMsg += `• ${error.message}\n\n`
          errorMsg += 'Try clicking "Retry Setup" or check the troubleshooting guide.'
        }

        sendSplashError(errorMsg)
      })

      typingServerProcess.on('exit', (code) => {
        console.log(`Typing server exited with code ${code}`)
        typingServerProcess = null
        // If it exits quickly, it probably failed
        if (!serverStarted) {
          console.error('Bundled Python server failed to start - will try system Python')
          sendSplashProgress('Backend failed, trying system Python...')
        }
      })

      // Wait to see if it actually starts before marking as started
      setTimeout(() => {
        if (typingServerProcess && !typingServerProcess.killed) {
          if (!serverStarted) {
            serverStarted = true
            console.log('Bundled Python server confirmed running')
            sendSplashProgress('✅ Backend server ready!')
            sendSplashComplete()
          }
        } else if (!serverStarted) {
          // Bundled Python failed, try system Python fallback
          console.log('Bundled Python failed to start, trying system Python...')
          sendSplashProgress('Trying system Python...')
          trySystemPython()
        }
      }, 3000) // Wait 3 seconds for bundled Python to start

    } catch (error) {
      console.error('Failed to start with bundled Python:', error.message)
      sendSplashProgress('Failed to spawn bundled Python, trying system Python...')
      setTimeout(trySystemPython, 500)
    }
  } else {
    // No bundled Python available, try system Python immediately
    console.log('Bundled Python not available, trying system Python...')
    sendSplashProgress('Trying system Python...')
    trySystemPython()
  }

  // System Python fallback function
  function trySystemPython() {
    if (serverStarted) {
      console.log('Server already started, skipping system Python fallback')
      return
    }

    const pythonCommands = ['python', 'python3', 'py']

    for (const pythonCmd of pythonCommands) {
      if (serverStarted) break

      try {
        const backendDir = path.dirname(typingServerPath)
        // Use Python -c to add to sys.path (works with all Python versions)
        const pythonCode = `import sys; sys.path.insert(0, r'${backendDir}'); __file__ = r'${typingServerPath}'; exec(open(r'${typingServerPath}').read())`

        typingServerProcess = spawn(pythonCmd, ['-c', pythonCode], {
          cwd: backendDir,
          stdio: ['ignore', 'pipe', 'pipe'],
          windowsHide: true,
          env: {
            ...process.env,
            SLYWRITER_CONFIG_DIR: app.getPath('userData')
          }
        })

        typingServerProcess.stdout.on('data', (data) => {
          console.log(`Typing server: ${data}`)
        })

        typingServerProcess.stderr.on('data', (data) => {
          const message = data.toString()
          console.log(`Typing server: ${message}`)
          if (message.includes('Uvicorn running on') || message.includes('8000')) {
            serverStarted = true
            console.log('Typing server started successfully on port 8000 (system Python)')
            sendSplashProgress('✅ Backend ready (system Python)')
            sendSplashComplete()

            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.executeJavaScript(`
                console.log('✅ Typing server started successfully (system Python)');
              `).catch(() => {})
            }
          }
        })

        typingServerProcess.on('error', (error) => {
          console.error(`Failed with ${pythonCmd}:`, error.message)
        })

        typingServerProcess.on('exit', (code) => {
          console.log(`Typing server exited with code ${code}`)
          typingServerProcess = null
        })

        // Give it a moment to see if it starts
        setTimeout(() => {
          if (typingServerProcess && !typingServerProcess.killed && !serverStarted) {
            serverStarted = true
            sendSplashProgress('✅ Backend ready (system Python)')
            sendSplashComplete()
          }
        }, 1000)

      } catch (error) {
        console.error(`Failed to start with ${pythonCmd}:`, error.message)
      }
    }

    // Wait a bit to see if any Python command worked
    setTimeout(() => {
      if (!serverStarted) {
        console.error('Could not start typing server - Python may not be installed or dependencies missing')
        console.error('This is expected on first run. Python will be downloaded automatically.')
        console.error('If this persists, install Python manually from python.org')

        const fallbackError = 'Backend server failed to start.\n\n' +
                             'Possible causes:\n' +
                             '• First time setup - Python is downloading (this is normal)\n' +
                             '• Firewall blocking Python download\n' +
                             '• Internet connection issue\n' +
                             '• Missing dependencies\n\n' +
                             'Next steps:\n' +
                             '1. Click "Retry Setup" to try again\n' +
                             '2. Check your firewall/antivirus settings\n' +
                             '3. See the troubleshooting guide (link in app footer)'
        sendSplashError(fallbackError)

        // Notify user in the renderer
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.executeJavaScript(`
            console.error('⚠️ Typing server is not running');
            console.log('📥 Python environment is being set up. Please wait...');
            console.log('The app will download Python (~20MB) and install dependencies (~50MB).');
            console.log('If this doesn\\'t work automatically, you may need to:');
            console.log('  1. Install Python from https://python.org');
            console.log('  2. Run: pip install fastapi uvicorn keyboard openai python-dotenv');
            console.log('  3. Restart SlyWriter');
          `).catch(() => {})
        }
      }
    }, 3000)
  } // End of trySystemPython

  // Global timeout: If backend hasn't started in 90 seconds, show error
  setTimeout(() => {
    if (!serverStarted) {
      console.error('[Setup] Backend startup timed out after 90 seconds')
      const timeoutError = 'Backend server startup timed out. This may be due to:\n' +
                          '• Slow internet connection (downloading Python/packages)\n' +
                          '• Firewall blocking the download\n' +
                          '• Port 8000 already in use by another application\n\n' +
                          'Please click "Retry Setup" or check your firewall settings.'
      sendSplashError(timeoutError)

      // Kill any lingering process
      if (typingServerProcess && !typingServerProcess.killed) {
        typingServerProcess.kill()
        typingServerProcess = null
      }
    }
  }, 90000) // 90 second timeout
}

// Stop the typing server
function stopTypingServer() {
  if (typingServerProcess) {
    console.log('Stopping typing server...')
    try {
      if (process.platform === 'win32') {
        // Force kill the process tree on Windows
        exec(`taskkill /pid ${typingServerProcess.pid} /T /F`, (err) => {
          if (err) console.log('Error killing typing server:', err)
        })
      } else {
        typingServerProcess.kill('SIGKILL')
      }
    } catch (e) {
      console.log('Error during typing server cleanup:', e)
    }
    typingServerProcess = null
  }
}

// Simple cleanup - no complex killing
function cleanupPreviousInstances() {
  console.log('Starting Electron app...')
  // No cleanup needed - batch file handles it
}

// Removed unused port and waiting functions - keeping it simple

let splashWindow = null

function createSplashScreen() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 600,  // Taller to fit logs
    frame: false,
    transparent: true,
    alwaysOnTop: false,  // NOT always on top - it was annoying
    resizable: false,
    center: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'splash-preload.js')
    }
  })

  splashWindow.loadFile('splash.html')

  // Send app version once window is ready
  splashWindow.webContents.on('did-finish-load', () => {
    splashWindow.webContents.send('app-version', APP_VERSION)
  })

  // Listen for close-splash message from renderer
  ipcMain.once('close-splash', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy()
      splashWindow = null
      // Show main window after splash
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show()
      }
    }
  })

  // Listen for retry-setup message from renderer
  ipcMain.on('retry-setup', async () => {
    console.log('[Setup] Retry requested by user')
    sendSplashProgress('Retrying setup...')

    // Kill existing typing server process if running
    if (typingServerProcess && !typingServerProcess.killed) {
      console.log('[Setup] Killing existing typing server process')
      typingServerProcess.kill()
      typingServerProcess = null
      // Wait a moment for process to fully terminate
      await new Promise(resolve => setTimeout(resolve, 1000))
    }

    // Retry Python setup and backend start
    try {
      await startTypingServer()
    } catch (error) {
      console.error('[Setup] Retry failed:', error)
      const errorMsg = error.message || 'Retry failed. Please check your internet connection and firewall settings.'
      sendSplashError(errorMsg)
    }
  })
}

// Helper function to send progress to splash window
function sendSplashProgress(message) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('setup-progress', message)
  }
}

function sendSplashComplete() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('setup-complete')
  }
}

function sendSplashError(error) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('setup-error', error)
  }
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1500,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    frame: true,
    backgroundColor: '#000000',
    show: false, // Don't show until splash is done
    autoHideMenuBar: true, // Hide menu bar for production (File, Edit, View, etc.)
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true
    },
    icon: path.join(__dirname, 'assets', 'icon.ico'), // SlyWriter logo
    titleBarStyle: process.platform === 'win32' ? 'default' : 'hiddenInset',
    titleBarOverlay: process.platform === 'win32' ? {
      color: '#000000',
      symbolColor: '#ffffff',
      height: 32
    } : undefined,
    show: false
  })

  // Remove menu bar completely for production
  mainWindow.setMenu(null)

  // Handle external links intelligently
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    console.log('[Window] External link clicked:', url)

    // Allow Google OAuth popups to open in Electron (needed for sign-in)
    if (url.includes('accounts.google.com') || url.includes('oauth')) {
      console.log('[Window] Allowing OAuth popup in Electron')
      return {
        action: 'allow',
        overrideBrowserWindowOptions: {
          width: 500,
          height: 600,
          center: true,
          resizable: false,
          webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
          }
        }
      }
    }

    // Open Stripe and other external links in system browser
    if (url.includes('stripe.com') || url.includes('checkout') || url.includes('payment')) {
      console.log('[Window] Opening payment link in system browser')
      require('electron').shell.openExternal(url)
      return { action: 'deny' }
    }

    // Default: open in system browser
    console.log('[Window] Opening external link in system browser')
    require('electron').shell.openExternal(url)
    return { action: 'deny' }
  })

  // Load the Next.js app - check if user is already logged in
  const userConfigPath = path.join(app.getPath('userData'), 'user_config.json')
  const hasUserConfig = fs.existsSync(userConfigPath)

  if (isDev) {
    // Simple: Just wait a bit and load port 3000
    console.log('Loading Next.js from localhost:3000...')
    setTimeout(() => {
      // If user has config, go to app; otherwise show login
      const startUrl = hasUserConfig ? 'http://localhost:3000' : 'http://localhost:3000/login'
      console.log(`Loading ${hasUserConfig ? 'app' : 'login page'}`)
      mainWindow.loadURL(startUrl)
    }, 2000)
  } else {
    // In production, load from deployed UI
    const startUrl = hasUserConfig
      ? 'https://slywriter-ui.onrender.com'
      : 'https://slywriter-ui.onrender.com/login'
    console.log(`Loading ${hasUserConfig ? 'app' : 'login page'}`)
    mainWindow.loadURL(startUrl)
  }

  // DON'T show window automatically - let splash screen control when to show
  // The splash screen will close after setup completes, which triggers showing main window
  mainWindow.once('ready-to-show', () => {
    console.log('[Window] Main window ready (not showing yet - waiting for setup)')
    // Open DevTools in development mode
    if (isDev) {
      mainWindow.webContents.openDevTools()
    }
  })

  // NO automatic timeout - splash screen controls visibility
  // If setup fails, user can click "Close" button on splash to proceed anyway
  
  // Add error handling for failed page loads
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`Failed to load: ${validatedURL}`)
    console.error(`Error: ${errorDescription} (${errorCode})`)
    
    // If it fails to load, try again after a delay
    if (validatedURL.includes('localhost:3000')) {
      console.log('Retrying connection to Next.js server...')
      setTimeout(() => {
        mainWindow.loadURL('http://localhost:3000')
      }, 2000)
    }
  })
  
  // Log when page loads successfully
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page loaded successfully!')

    // Mac fix: Inject script to sync textarea DOM value with React state
    // On Mac, automated typing doesn't trigger React's onChange properly
    if (process.platform === 'darwin') {
      mainWindow.webContents.executeJavaScript(`
        (function() {
          console.log('[SlyWriter Mac Fix] Initializing textarea sync...');

          // Function to dispatch proper React-compatible input event
          function syncTextareaWithReact() {
            const textarea = document.querySelector('textarea[placeholder*="Type here"]');
            if (!textarea) return;

            const currentValue = textarea.value;
            const lastKnownValue = textarea._lastSyncedValue || '';

            // Only dispatch event if value actually changed
            if (currentValue !== lastKnownValue) {
              console.log('[SlyWriter Mac Fix] Syncing textarea value:', currentValue.substring(0, 50) + '...');

              // Store the current value
              textarea._lastSyncedValue = currentValue;

              // Create and dispatch input event (React uses these for controlled inputs)
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
              nativeInputValueSetter.call(textarea, currentValue);

              // Dispatch input event which React listens to
              const inputEvent = new Event('input', { bubbles: true, cancelable: true });
              textarea.dispatchEvent(inputEvent);

              // Also dispatch change event for good measure
              const changeEvent = new Event('change', { bubbles: true, cancelable: true });
              textarea.dispatchEvent(changeEvent);
            }
          }

          // Poll every 500ms to check for value changes
          setInterval(syncTextareaWithReact, 500);

          // Also sync on focus events (when user clicks into textarea)
          document.addEventListener('focusin', (e) => {
            if (e.target && e.target.matches && e.target.matches('textarea[placeholder*="Type here"]')) {
              setTimeout(syncTextareaWithReact, 100);
            }
          });

          console.log('[SlyWriter Mac Fix] Textarea sync initialized!');
        })();
      `).catch(err => console.error('Failed to inject Mac textarea sync:', err));
    }
  })

  // Add keyboard shortcuts for the window
  mainWindow.webContents.on('before-input-event', (event, input) => {
    // Check for F12 key
    if (input.key === 'F12' && input.type === 'keyDown') {
      if (mainWindow.webContents.isDevToolsOpened()) {
        mainWindow.webContents.closeDevTools()
      } else {
        mainWindow.webContents.openDevTools()
      }
      event.preventDefault()
    }
  })
  
  // When window is closed, quit the entire app
  mainWindow.on('closed', () => {
    // Dereference the window object
    mainWindow = null
    // Quit the entire application
    app.quit()
  })
}

function createOverlay() {
  // Get primary display dimensions
  const { width, height } = screen.getPrimaryDisplay().workAreaSize
  
  // Create overlay window with better sizing
  overlayWindow = new BrowserWindow({
    width: 320,
    height: 260,
    x: width - 340,
    y: 20,
    frame: false,
    transparent: true,
    skipTaskbar: true,
    resizable: false,
    movable: false, // Handle movement manually for better control
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    alwaysOnTop: true,
    type: 'toolbar', // Windows: ensures it stays on top globally
    focusable: true, // Need to be focusable for clicks to work properly
    skipTaskbar: true, // Don't show in taskbar
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      backgroundThrottling: false,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false,
    hasShadow: true,
    roundedCorners: true,
    parent: null // Ensure it's not tied to main window
  })

  // Force maximum always-on-top priority (Windows specific)
  // Use different levels to ensure it stays on top globally
  if (process.platform === 'win32') {
    // On Windows, use pop-up-menu level for better global overlay
    overlayWindow.setAlwaysOnTop(true, 'pop-up-menu', 1)
    overlayWindow.setSkipTaskbar(true)
  } else {
    // On other platforms
    overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
  }
  
  // Ensure visible on all workspaces and fullscreen apps
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  
  // Periodically reinforce always-on-top to prevent other windows from covering it
  overlayIntervalId = setInterval(() => {
    if (overlayWindow && !overlayWindow.isDestroyed() && overlayWindow.isVisible()) {
      overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
    }
  }, 1000) // Check every second
  
  // Load overlay HTML
  overlayWindow.loadFile(path.join(__dirname, 'overlay.html'))
  
  // Handle overlay movement
  ipcMain.on('move-overlay', (event, offset) => {
    if (overlayWindow) {
      const [x, y] = overlayWindow.getPosition()
      overlayWindow.setPosition(x + offset.x, y + offset.y)
    }
  })
  
  // Handle overlay hide from overlay window X button
  ipcMain.on('hide-overlay', () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.hide()
    }
  })
  
  // Keep overlay IPC alive with ping-pong
  ipcMain.on('overlay-ping', (event) => {
    event.reply('overlay-pong')
  })
  
  // Handle overlay action buttons
  ipcMain.on('overlay-action', async (event, action) => {
    console.log('Overlay action:', action)
    
    // Blur the overlay window immediately for all actions
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.blur()
    }
    
    // Send the action to the renderer as a global hotkey event
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (action === 'start') {
        // Call the global start handler
        console.log('Overlay triggered start')
        if (global.startTypingHandler) {
          global.startTypingHandler()
        } else {
          console.log('Start handler not ready yet')
          // Send to renderer as fallback
          mainWindow.webContents.send('global-hotkey', 'start')
        }
      } else if (action === 'stop') {
        // Send stop to renderer
        mainWindow.webContents.send('global-hotkey', action)
        mainWindow.webContents.send('overlay-stop')  // Specific event for React listeners
      } else if (action === 'pause') {
        // Send IPC to renderer - let React handle the API call
        // This prevents double-calling the pause endpoint (which would toggle pause → resume)
        console.log('Overlay triggered pause - sending to renderer')
        mainWindow.webContents.send('global-hotkey', 'pause')
        mainWindow.webContents.send('overlay-pause')  // Specific event for React listeners
      } else if (action === 'ai-generate') {
        // Call the global AI generation handler
        console.log('🎯🎯🎯 === OVERLAY AI BUTTON CLICKED === 🎯🎯🎯')
        console.log('🎯 [ELECTRON] Overlay triggered AI generation')
        console.log('🎯 [ELECTRON] Handler exists:', !!global.aiGenerationHandler)
        if (global.aiGenerationHandler) {
          console.log('🎯 [ELECTRON] Calling AI generation handler from overlay...')
          global.aiGenerationHandler(true)  // Pass true to indicate it's from overlay
        } else {
          console.log('AI generation handler not ready yet!')
        }
      } else if (action === 'paste-mode') {
        // Toggle paste mode
        const pasteMode = await mainWindow.webContents.executeJavaScript(`
          (() => {
            const currentMode = localStorage.getItem('slywriter-paste-mode') === 'true';
            const newMode = !currentMode;
            localStorage.setItem('slywriter-paste-mode', newMode);
            return newMode;
          })()
        `).catch(() => false)
        
        // Update overlay with paste mode status
        overlayWindow.webContents.send('update-display', {
          type: 'typing',
          status: pasteMode ? '📋 Paste mode ON' : '⌨️ Typing mode ON',
          progress: null,
          wpm: null,
          charsTyped: null
        })
      }
    }
  })
  
  // Handle overlay status request
  ipcMain.on('overlay-request-status', async (event) => {
    console.log('[MAIN] Overlay requesting current status')
    if (mainWindow && !mainWindow.isDestroyed()) {
      try {
        // Get current typing status from the renderer
        const status = await mainWindow.webContents.executeJavaScript(`
          (() => {
            const statusEl = document.querySelector('.status-text')
            const progressEl = document.querySelector('[role="progressbar"]')
            const wpmEl = document.querySelector('.text-2xl.font-bold.text-white')
            return {
              status: statusEl ? statusEl.textContent : 'Ready to type',
              progress: progressEl ? parseInt(progressEl.getAttribute('aria-valuenow')) : 0,
              wpm: wpmEl ? parseInt(wpmEl.textContent) : 0
            }
          })()
        `)
        
        // Send status to overlay
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          overlayWindow.webContents.send('update-display', {
            type: 'typing',
            status: status.status || 'Ready to type',
            progress: status.progress || 0,
            wpm: status.wpm || 0
          })
        }
      } catch (error) {
        console.error('Failed to get status:', error)
        // Send default status
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          overlayWindow.webContents.send('update-display', {
            type: 'typing',
            status: 'Ready to type',
            progress: 0,
            wpm: 0
          })
        }
      }
    }
  })
  
  // Handle hide-overlay-request from overlay close button  
  ipcMain.on('hide-overlay-request', (event) => {
    console.log('[MAIN] Received hide-overlay-request')
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      console.log('[MAIN] Hiding overlay window...')
      overlayWindow.hide()
      console.log('[MAIN] Overlay hidden, notifying main window...')
      
      // Notify the main window that overlay is now hidden
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('overlay-visibility-changed', false)
        console.log('[MAIN] Main window notified of overlay state change')
      }
    } else {
      console.log('[MAIN] Overlay window not found or destroyed')
    }
  })
  
  // Handle toggle-electron-overlay from sidebar button
  ipcMain.on('toggle-electron-overlay', () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      const isVisible = overlayWindow.isVisible()
      if (isVisible) {
        overlayWindow.hide()
        // Notify main window of state change
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('overlay-visibility-changed', false)
        }
      } else {
        overlayWindow.show()
        overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
        // Ensure window is interactive without stealing focus
        overlayWindow.setIgnoreMouseEvents(false)
        overlayWindow.focus()
        setTimeout(() => overlayWindow.blur(), 50)
        // Notify main window of state change
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('overlay-visibility-changed', true)
        }
      }
    }
  })

  // Send current hotkeys to overlay when it's ready
  overlayWindow.webContents.on('did-finish-load', () => {
    console.log('[MAIN] Overlay loaded successfully')

    // Load saved hotkeys and send to overlay
    try {
      const hotkeyPath = path.join(app.getPath('userData'), 'hotkeys.json')
      if (fs.existsSync(hotkeyPath)) {
        const hotkeys = JSON.parse(fs.readFileSync(hotkeyPath, 'utf8'))
        overlayWindow.webContents.send('update-hotkeys-overlay', hotkeys)
        console.log('[MAIN] Sent hotkeys to overlay:', hotkeys)
      } else {
        // Send default hotkeys
        const defaultHotkeys = {
          start: 'CommandOrControl+Alt+S',
          stop: 'CommandOrControl+Alt+Q',
          pause: 'CommandOrControl+Alt+P',
          overlay: 'CommandOrControl+Alt+O',
          ai_generation: 'CommandOrControl+Shift+G'  // Changed from Alt to Shift to avoid Chrome conflicts
        }
        overlayWindow.webContents.send('update-hotkeys-overlay', defaultHotkeys)
        console.log('[MAIN] Sent default hotkeys to overlay')
      }
    } catch (err) {
      console.error('[MAIN] Error sending hotkeys to overlay:', err)
    }
  })
  
  // Keep overlay hidden by default - user can toggle with Ctrl+Alt+O
  // overlayWindow.once('ready-to-show', () => {
  //   overlayWindow.show()
  // })
}

function createTray() {
  // Use SlyWriter logo for tray icon
  try {
    tray = new Tray(path.join(__dirname, 'assets', 'icon.ico'))
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Toggle Overlay',
      click: () => {
        if (overlayWindow && overlayWindow.isVisible()) {
          overlayWindow.hide()
        } else if (overlayWindow) {
          overlayWindow.show()
          overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
          // Ensure window is interactive without stealing focus
          overlayWindow.setIgnoreMouseEvents(false)
          overlayWindow.focus()
          setTimeout(() => overlayWindow.blur(), 50)
          
          // Send current hotkeys to overlay
          try {
            const hotkeyPath = path.join(app.getPath('userData'), 'hotkeys.json')
            if (fs.existsSync(hotkeyPath)) {
              const hotkeys = JSON.parse(fs.readFileSync(hotkeyPath, 'utf8'))
              overlayWindow.webContents.send('update-hotkeys-overlay', hotkeys)
              console.log('[TRAY] Sent hotkeys to overlay')
            }
          } catch (err) {
            console.error('[TRAY] Error sending hotkeys:', err)
          }
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.webContents.send('navigate', '/settings')
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit()
      }
    }
  ])
  
  tray.setToolTip('SlyWriter - AI Typing Assistant')
  tray.setContextMenu(contextMenu)
  
  // Double click to show window or focus it
  tray.on('double-click', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore()
      }
      mainWindow.focus()
    }
  })
  } catch (error) {
    console.log('Tray icon not found, skipping tray creation')
  }
}

// Auto-updater setup
let updateWindow = null

function createUpdateWindow() {
  if (updateWindow && !updateWindow.isDestroyed()) {
    updateWindow.focus()
    return
  }

  const { screen } = require('electron')
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize

  // Center the window on screen
  const windowWidth = 420
  const windowHeight = 280
  const x = Math.round((screenWidth - windowWidth) / 2)
  const y = Math.round((screenHeight - windowHeight) / 2)

  updateWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    frame: false,
    transparent: true,
    alwaysOnTop: true, // Always on top so user sees it
    resizable: false,
    skipTaskbar: false,
    x: x,
    y: y,
    modal: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  updateWindow.loadFile('update.html')

  updateWindow.on('closed', () => {
    updateWindow = null
  })
}

// ============== LICENSE VERIFICATION SYSTEM ==============

async function verifyLicense() {
  console.log('[License] Verifying license...')

  try {
    // Get stored license key from user config
    const userConfigPath = path.join(app.getPath('userData'), 'user_config.json')
    let licenseKey = null

    if (fs.existsSync(userConfigPath)) {
      try {
        const userConfig = JSON.parse(fs.readFileSync(userConfigPath, 'utf8'))
        licenseKey = userConfig.email || userConfig.license_key
      } catch (e) {
        console.log('[License] Could not read user config:', e.message)
      }
    }

    if (!licenseKey) {
      console.log('[License] No license key found - prompting for login')
      return {
        valid: false,
        error: 'no_license',
        message: 'Please log in to use SlyWriter'
      }
    }

    // Call local backend which will verify with server
    const response = await axios.post('http://localhost:8000/api/license/verify', {
      license_key: licenseKey,
      force: true
    }).catch(err => {
      // If local backend not running yet, wait and retry
      console.log('[License] Backend not ready, waiting...')
      return new Promise((resolve) => {
        setTimeout(async () => {
          resolve(await axios.post('http://localhost:8000/api/license/verify', {
            license_key: licenseKey,
            force: true
          }).catch(e => ({ data: { valid: false, error: 'backend_unavailable' } })))
        }, 2000)
      })
    })

    const licenseData = response.data

    console.log('[License] Verification result:', licenseData.valid ? 'SUCCESS' : 'FAILED')

    if (!licenseData.valid) {
      console.log('[License] Error:', licenseData.error, '-', licenseData.message)
    }

    return licenseData

  } catch (error) {
    console.error('[License] Verification failed:', error.message)
    return {
      valid: false,
      error: 'verification_failed',
      message: 'Could not verify license. Please check your internet connection.'
    }
  }
}

async function handleLicenseError(licenseData) {
  console.log('[License] Handling license error:', licenseData.error)

  // Handle different error types
  if (licenseData.error === 'update_required') {
    // CRITICAL: Force user to update
    const response = await dialog.showMessageBox({
      type: 'warning',
      title: 'Update Required',
      message: licenseData.message || 'Your app version is outdated',
      detail: `Please download the latest version to continue using SlyWriter.\n\nCurrent: ${app.getVersion()}\nRequired: ${licenseData.minimum_version || 'latest'}`,
      buttons: ['Download Update', 'Quit'],
      defaultId: 0,
      cancelId: 1
    })

    if (response.response === 0) {
      // Open download URL
      shell.openExternal(licenseData.update_url || 'https://github.com/slywriterapp/slywriterapp/releases/latest')
    }

    // Quit app - update is required
    app.quit()
    return false
  }

  if (licenseData.error === 'device_limit_reached') {
    // Show device limit dialog
    const deviceList = (licenseData.devices || [])
      .map(d => `• ${d.name} (last seen: ${new Date(d.last_seen).toLocaleDateString()})`)
      .join('\n')

    await dialog.showMessageBox({
      type: 'warning',
      title: 'Device Limit Reached',
      message: licenseData.message || 'Maximum devices reached',
      detail: `Your plan allows ${licenseData.max_devices} device(s). Currently registered:\n\n${deviceList}\n\nPlease deactivate a device from your account settings or upgrade your plan.`,
      buttons: ['OK']
    })

    // TODO: Add device management UI
    app.quit()
    return false
  }

  if (licenseData.error === 'no_license' || licenseData.error === 'user_not_found') {
    // Allow app to continue and show login page
    // The window will load the login page since hasUserConfig will be false
    console.log('[License] No license found - will show login page')
    return true // Let the app continue to create windows and show login
  }

  // Generic error - allow with warning
  console.warn('[License] Generic error, allowing with warning:', licenseData.error)
  return true
}

function setupAutoUpdater() {
  // Configure auto-updater to use GitHub releases (public releases repo)
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'slywriterapp',
    repo: 'slywriter-releases'
  })

  autoUpdater.autoDownload = true
  autoUpdater.autoInstallOnAppQuit = true

  // Check for updates on app start (after splash screen)
  // NOTE: Updates should work regardless of license status
  setTimeout(async () => {
    console.log('[AUTO-UPDATE] ========================================')
    console.log('[AUTO-UPDATE] Initial update check starting...')
    console.log('[AUTO-UPDATE] Timestamp:', new Date().toISOString())
    console.log('[AUTO-UPDATE] Initiating update check...')

    try {
      const result = await autoUpdater.checkForUpdatesAndNotify()
      console.log('[AUTO-UPDATE] Check result:', result)
    } catch (err) {
      console.error('[AUTO-UPDATE] Update check failed:', err)
      console.error('[AUTO-UPDATE] Error details:', {
        message: err.message,
        code: err.code,
        stack: err.stack
      })
    }
    console.log('[AUTO-UPDATE] ========================================')
  }, 3500)

  // Check for updates every 30 minutes
  setInterval(() => {
    autoUpdater.checkForUpdates().catch(err => {
      console.log('Periodic update check failed:', err)
    })
  }, 30 * 60 * 1000)

  // Auto-updater event handlers with ENHANCED DEBUGGING
  autoUpdater.on('checking-for-update', () => {
    console.log('[AUTO-UPDATE] ========================================')
    console.log('[AUTO-UPDATE] Checking for updates...')
    console.log('[AUTO-UPDATE] Current version:', app.getVersion())
    console.log('[AUTO-UPDATE] Feed URL:', autoUpdater.getFeedURL())
    console.log('[AUTO-UPDATE] Platform:', process.platform)
    console.log('[AUTO-UPDATE] Arch:', process.arch)
    console.log('[AUTO-UPDATE] ========================================')

    // Send to main window (for login screen)
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('update-checking')
    }
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('update-checking')
    }
  })

  autoUpdater.on('update-available', (info) => {
    console.log('[AUTO-UPDATE] ========================================')
    console.log('[AUTO-UPDATE] ✅ UPDATE AVAILABLE!')
    console.log('[AUTO-UPDATE] New version:', info.version)
    console.log('[AUTO-UPDATE] Current version:', app.getVersion())
    console.log('[AUTO-UPDATE] Release date:', info.releaseDate)
    console.log('[AUTO-UPDATE] Release notes:', info.releaseNotes)
    console.log('[AUTO-UPDATE] Files:', info.files)
    console.log('[AUTO-UPDATE] ========================================')

    // Send to main window for login screen notification
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('update-available', {
        version: info.version,
        currentVersion: app.getVersion()
      })
    }

    // Create update window
    createUpdateWindow()

    // Send update info to window
    setTimeout(() => {
      if (updateWindow && !updateWindow.isDestroyed()) {
        updateWindow.webContents.send('update-available', info)
      }
    }, 500)

    // Start download automatically
    console.log('[AUTO-UPDATE] Starting download...')
    autoUpdater.downloadUpdate()
  })

  autoUpdater.on('update-not-available', (info) => {
    console.log('[AUTO-UPDATE] ========================================')
    console.log('[AUTO-UPDATE] ℹ️ No updates available')
    console.log('[AUTO-UPDATE] Current version:', app.getVersion())
    console.log('[AUTO-UPDATE] Checked version:', info?.version || 'N/A')
    console.log('[AUTO-UPDATE] ========================================')

    // Send to main window
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('update-not-available', { version: app.getVersion() })
    }
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('update-not-available')
    }
  })

  autoUpdater.on('download-progress', (progressObj) => {
    const logInterval = Math.floor(progressObj.percent / 10) * 10
    if (progressObj.percent >= logInterval && progressObj.percent < logInterval + 2) {
      console.log('[AUTO-UPDATE] Download progress:', {
        percent: progressObj.percent.toFixed(2) + '%',
        transferred: (progressObj.transferred / 1024 / 1024).toFixed(2) + ' MB',
        total: (progressObj.total / 1024 / 1024).toFixed(2) + ' MB',
        bytesPerSecond: (progressObj.bytesPerSecond / 1024).toFixed(2) + ' KB/s'
      })
    }

    // Send progress to update window
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('download-progress', progressObj)
    }
  })

  autoUpdater.on('update-downloaded', (info) => {
    console.log('[AUTO-UPDATE] ========================================')
    console.log('[AUTO-UPDATE] ✅ UPDATE DOWNLOADED SUCCESSFULLY!')
    console.log('[AUTO-UPDATE] Version:', info.version)
    console.log('[AUTO-UPDATE] Files downloaded:', info.files)
    console.log('[AUTO-UPDATE] Auto-installing in 3 seconds...')
    console.log('[AUTO-UPDATE] ========================================')

    // Send to update window
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('update-downloaded', info)
    }

    // Auto quit and install after 3 seconds
    setTimeout(() => {
      console.log('[AUTO-UPDATE] Quitting and installing update now...')
      isQuittingForUpdate = true
      autoUpdater.quitAndInstall(false, true)
    }, 3000)
  })

  autoUpdater.on('error', (error) => {
    console.error('[AUTO-UPDATE] ========================================')
    console.error('[AUTO-UPDATE] ❌ UPDATE ERROR!')
    console.error('[AUTO-UPDATE] Error message:', error.message)
    console.error('[AUTO-UPDATE] Error stack:', error.stack)
    console.error('[AUTO-UPDATE] Current version:', app.getVersion())
    console.error('[AUTO-UPDATE] Feed URL:', autoUpdater.getFeedURL())
    console.error('[AUTO-UPDATE] ========================================')

    // Send error to update window
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('update-error', error.message)
    }
  })
}

// App event handlers
app.whenReady().then(async () => {
  // Simple startup - no cleanup needed
  cleanupPreviousInstances()

  // Show splash screen FIRST
  createSplashScreen()

  // Create windows (but don't show them yet - splash is showing)
  createWindow()
  createOverlay()
  createTray()

  // Start the typing server (with visible progress in splash)
  sendSplashProgress('Initializing...')
  startTypingServer()

  // ============== LICENSE VERIFICATION ON STARTUP ==============
  // Wait for typing server to start (2 seconds)
  await new Promise(resolve => setTimeout(resolve, 2000))

  // Verify license BEFORE showing UI
  console.log('[App] Verifying license before starting...')
  const licenseData = await verifyLicense()

  if (!licenseData.valid) {
    // Handle license error - may quit app
    const canContinue = await handleLicenseError(licenseData)

    if (!canContinue) {
      console.log('[App] License verification failed, exiting...')
      return // Don't continue app startup
    }
  } else {
    console.log('[App] License verified successfully')
    console.log('[App] Plan:', licenseData.user?.plan)
    console.log('[App] Features:', licenseData.features_enabled)

    // Store license data globally for access by other parts of app
    global.licenseData = licenseData
  }
  // ============================================================

  // Initialize auto-updater
  setupAutoUpdater()

  // ============== PERIODIC LICENSE RE-VERIFICATION ==============
  // Re-verify license every 30 minutes while app is running
  setInterval(async () => {
    console.log('[App] Periodic license re-verification...')
    const licenseData = await verifyLicense()

    if (!licenseData.valid) {
      console.warn('[App] License is no longer valid!')
      // Removed annoying popup - just log it
    } else {
      // Update global license data
      global.licenseData = licenseData
      console.log('[App] License re-verified successfully')
    }
  }, 30 * 60 * 1000) // Every 30 minutes
  // ============================================================

  // Store hotkey handlers for reuse globally
  global.startTypingHandler = null
  global.aiGenerationHandler = null
  
  // Function to register hotkeys (can be called to update them)
  function registerHotkeys(hotkeys) {
    console.log('Registering global hotkeys...', hotkeys)
    
    // Unregister all existing hotkeys first
    globalShortcut.unregisterAll()
    
    // Register F12 to toggle DevTools (always active)
    const f12Success = globalShortcut.register('F12', () => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        if (mainWindow.webContents.isDevToolsOpened()) {
          mainWindow.webContents.closeDevTools()
        } else {
          mainWindow.webContents.openDevTools()
        }
      }
    })
    console.log('F12 registered:', f12Success)
    
    // Use provided hotkeys or defaults
    const keys = hotkeys || {
      start: 'CommandOrControl+Alt+S',
      stop: 'CommandOrControl+Alt+Q',
      pause: 'CommandOrControl+Alt+P',
      overlay: 'CommandOrControl+Alt+O',
      ai_generation: 'CommandOrControl+Alt+G'
    }
    
    // Convert hotkey format from web to Electron format
    const convertHotkey = (key) => {
      return key.replace('ctrl', 'CommandOrControl')
                .replace('cmd', 'CommandOrControl')
                .split('+').map(k => {
                  if (k === 'CommandOrControl' || k === 'Alt' || k === 'Shift') return k
                  return k.charAt(0).toUpperCase() + k.slice(1)
                }).join('+')
    }
    
    // Register each hotkey
    if (keys.ai_generation) {
      const key = convertHotkey(keys.ai_generation)
      console.log('Registering AI generation hotkey:', keys.ai_generation, '->', key)
      
      // Store the AI handler globally  
      global.aiGenerationHandler = async (isFromOverlay = false) => {
        console.log('🚀🚀🚀 === AI GENERATION HANDLER CALLED === 🚀🚀🚀')
        console.log('🚀 [ELECTRON] Triggered by:', isFromOverlay ? 'overlay button' : 'hotkey')
        console.log('🚀 [ELECTRON] Main window exists:', !!mainWindow)
        console.log('🚀 [ELECTRON] Main window destroyed:', mainWindow?.isDestroyed())
        
        if (mainWindow && !mainWindow.isDestroyed()) {
          // Save original clipboard to restore later
          const originalClipboard = clipboard.readText()
          console.log('Original clipboard saved:', originalClipboard ? originalClipboard.substring(0, 50) + '...' : 'empty')
          
          // Small delay to ensure the hotkey release is complete
          await new Promise(resolve => setTimeout(resolve, 100))
          
          // Call Python backend to copy highlighted text
          // Use different endpoint based on source
          const copyEndpoint = isFromOverlay ? '/api/copy-highlighted-overlay' : '/api/copy-highlighted'
          console.log('Calling Python backend to copy highlighted text...')
          console.log('Using endpoint:', copyEndpoint)
          let clipboardText = ''
          
          try {
            const copyResponse = await new Promise((resolve, reject) => {
              const req = http.request({
                hostname: '127.0.0.1',
                port: 8000,
                path: copyEndpoint,
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Content-Length': 2
                }
              }, (res) => {
                let data = ''
                res.on('data', chunk => data += chunk)
                res.on('end', () => {
                  if (res.statusCode === 200) {
                    try {
                      resolve(JSON.parse(data))
                    } catch (e) {
                      reject(e)
                    }
                  } else {
                    reject(new Error(`Copy failed: ${res.statusCode}`))
                  }
                })
              })
              req.on('error', reject)
              req.write('{}')
              req.end()
            })
            
            console.log('Copy response:', copyResponse)
            
            // Use the text from the server response (it already has the copied text)
            if (copyResponse && copyResponse.copied && copyResponse.text) {
              clipboardText = copyResponse.text
              console.log('Using text from server response:', clipboardText.substring(0, 100) + '...')
              // Also update the actual clipboard with the copied text
              clipboard.writeText(clipboardText)
            } else {
              console.log('Server did not copy text successfully')
              // Fall back to checking clipboard directly
              await new Promise(resolve => setTimeout(resolve, 300))
              clipboardText = clipboard.readText()
            }
          } catch (error) {
            console.error('Failed to copy highlighted text:', error)
            // Fall back to checking clipboard directly
            await new Promise(resolve => setTimeout(resolve, 300))
            clipboardText = clipboard.readText()
          }
          
          console.log('Final clipboard text:', clipboardText ? clipboardText.substring(0, 100) + '...' : 'empty')
          console.log('Clipboard changed:', clipboardText !== originalClipboard)
          
          // Check if we got NEW text (clipboard changed = we copied highlighted text)
          if (!clipboardText || clipboardText === originalClipboard || clipboardText.trim() === '') {
            console.log('No new text in clipboard after copy attempt')
            console.log('Original:', originalClipboard)
            console.log('Current:', clipboardText)
            
            // Try one more time with longer delay
            console.log('Trying again with longer delay...')
            await new Promise(resolve => setTimeout(resolve, 500))
            const retryClipboard = clipboard.readText()
            
            if (!retryClipboard || retryClipboard === originalClipboard || retryClipboard.trim() === '') {
              console.log('Still no highlighted text after retry')
              
              // Restore original clipboard
              if (originalClipboard) {
                clipboard.writeText(originalClipboard)
              }
              
              mainWindow.webContents.send('global-hotkey-error', '📋 No text highlighted! Please highlight text first.')
              if (overlayWindow && !overlayWindow.isDestroyed()) {
                overlayWindow.webContents.send('update-display', {
                  type: 'typing',
                  status: '❌ No text highlighted!',
                  progress: 0,
                  wpm: 0,
                  charsTyped: 0
                })
              }
              return
            } else {
              // Success on retry!
              console.log('Got text on retry:', retryClipboard.substring(0, 100))
              clipboardText = retryClipboard
            }
          }
          
          // Validate that we didn't accidentally copy an error message
          if (clipboardText.includes('No text highlighted') || clipboardText.includes('📋')) {
            console.log('WARNING: Clipboard contains error message, aborting')
            
            // Restore original clipboard
            if (originalClipboard) {
              clipboard.writeText(originalClipboard)
            }
            
            mainWindow.webContents.send('global-hotkey-error', 'Failed to copy highlighted text')
            if (overlayWindow && !overlayWindow.isDestroyed()) {
              overlayWindow.webContents.send('update-display', {
                type: 'typing',
                status: '❌ Failed to copy text',
                progress: 0,
                wpm: 0,
                charsTyped: 0
              })
            }
            return
          }
          
          
          // Make the AI request from main process to avoid CORS
          try {
            // Update overlay - starting AI generation
            if (overlayWindow && !overlayWindow.isDestroyed()) {
              overlayWindow.webContents.send('update-display', {
                type: 'typing',
                status: '🚀 Starting AI generation...',
                progress: 5,
                wpm: 0,
                charsTyped: 0
              })
            }
            
            // Get settings from renderer - check both AI Hub and AI settings
            const settings = await mainWindow.webContents.executeJavaScript(`
              (() => {
                const aiHubSettings = localStorage.getItem('slywriter-ai-hub-settings');
                const aiSettings = localStorage.getItem('slywriter-ai-settings');
                console.log('[RENDERER] AI Hub Settings:', aiHubSettings);
                console.log('[RENDERER] AI Settings:', aiSettings);
                // Prefer AI Hub settings since that's where review mode is set
                return JSON.parse(aiHubSettings || aiSettings || '{}');
              })()
            `).catch(() => ({}))
            
            const pasteMode = await mainWindow.webContents.executeJavaScript(`
              localStorage.getItem('slywriter-paste-mode') === 'true'
            `).catch(() => false)
            
            const reviewMode = settings.review_mode === true || settings.review_mode === 'true'
            // Check for both humanizer and humanizer_enabled keys (different storage formats)
            const humanizerEnabled = settings.humanizer_enabled === true || settings.humanizer_enabled === 'true' ||
                                     settings.humanizer === true || settings.humanizer === 'true'

            console.log('🚀 [ELECTRON] AI settings:', settings)
            console.log('🚀 [ELECTRON] Paste mode:', pasteMode)
            console.log('🚀 [ELECTRON] Review mode value:', settings.review_mode)
            console.log('🚀 [ELECTRON] Review mode type:', typeof settings.review_mode)
            console.log('🚀 [ELECTRON] Review mode decision:', reviewMode)
            console.log('🚀 [ELECTRON] Humanizer settings.humanizer_enabled:', settings.humanizer_enabled)
            console.log('🚀 [ELECTRON] Humanizer settings.humanizer:', settings.humanizer)
            console.log('🚀 [ELECTRON] Humanizer enabled decision:', humanizerEnabled)

            // Check AI generation and humanizer balances BEFORE making the request
            try {
              const userString = await mainWindow.webContents.executeJavaScript(`
                localStorage.getItem('slywriter-user')
              `).catch(() => null)

              if (userString) {
                const user = JSON.parse(userString)
                const userId = user.id || user.user_id

                if (userId) {
                  console.log('🔍 Checking usage limits for user:', userId)

                  // Fetch limits from server
                  const limitsResponse = await new Promise((resolve, reject) => {
                    const req = https.request({
                      hostname: 'slywriterapp.onrender.com',
                      port: 443,
                      path: `/api/usage/limits?user_id=${userId}`,
                      method: 'GET'
                    }, (res) => {
                      let data = ''
                      res.on('data', chunk => data += chunk)
                      res.on('end', () => {
                        if (res.statusCode === 200) {
                          try {
                            resolve(JSON.parse(data))
                          } catch (e) {
                            reject(e)
                          }
                        } else {
                          reject(new Error(`Failed to fetch limits: ${res.statusCode}`))
                        }
                      })
                    })
                    req.on('error', reject)
                    req.end()
                  })

                  console.log('📊 Usage limits:', limitsResponse)

                  // Check AI generation balance
                  const aiGenRemaining = limitsResponse.ai_gen_remaining
                  const aiGenLimit = limitsResponse.ai_gen_limit

                  if (aiGenLimit !== -1 && aiGenRemaining <= 0) {
                    const plan = user.plan || 'Free'
                    const errorMsg = plan.toLowerCase() === 'free'
                      ? `You've used all ${aiGenLimit} AI generations this week! Upgrade to Pro for unlimited.`
                      : 'AI generation limit reached. Resets Monday!'

                    console.log('❌ AI generation limit reached')
                    mainWindow.webContents.send('global-hotkey-error', errorMsg)
                    mainWindow.webContents.send('show-upgrade-modal')

                    if (overlayWindow && !overlayWindow.isDestroyed()) {
                      overlayWindow.webContents.send('update-display', {
                        type: 'error',
                        status: `❌ ${errorMsg}`,
                        progress: 0
                      })
                    }

                    // Restore original clipboard
                    if (originalClipboard) {
                      clipboard.writeText(originalClipboard)
                    }
                    return
                  }

                  // Check humanizer balance if humanizer is enabled
                  if (humanizerEnabled) {
                    const humanizerRemaining = limitsResponse.humanizer_remaining
                    const humanizerLimit = limitsResponse.humanizer_limit

                    if (humanizerLimit !== -1 && humanizerRemaining <= 0) {
                      const plan = user.plan || 'Free'
                      const errorMsg = plan.toLowerCase() === 'free'
                        ? `You've used all ${humanizerLimit} humanizer uses this week! Upgrade to Pro for unlimited.`
                        : 'Humanizer limit reached. Resets Monday!'

                      console.log('❌ Humanizer limit reached')
                      mainWindow.webContents.send('global-hotkey-error', errorMsg)
                      mainWindow.webContents.send('show-upgrade-modal')

                      if (overlayWindow && !overlayWindow.isDestroyed()) {
                        overlayWindow.webContents.send('update-display', {
                          type: 'error',
                          status: `❌ ${errorMsg}`,
                          progress: 0
                        })
                      }

                      // Restore original clipboard
                      if (originalClipboard) {
                        clipboard.writeText(originalClipboard)
                      }
                      return
                    }
                  }

                  console.log('✅ Balance checks passed, proceeding with AI generation')
                }
              }
            } catch (err) {
              console.log('⚠️ Could not check balances, proceeding anyway:', err.message)
            }

            // Update overlay - loaded settings
            if (overlayWindow && !overlayWindow.isDestroyed()) {
              overlayWindow.webContents.send('update-display', {
                type: 'typing',
                status: '⚙️ Settings loaded, building prompt...',
                progress: 15,
                wpm: 0,
                charsTyped: 0
              })
            }
            
            // Build prompt for AI generation
            const prompt = `Based on this input: "${clipboardText}"\n\n` +
              `Write a ${settings.response_length === 1 ? 'very brief (1-2 sentences)' :
                         settings.response_length === 2 ? 'short (2-4 sentences)' :
                         settings.response_length === 3 ? 'medium (4-8 sentences)' :
                         settings.response_length === 4 ? 'long (8-15 sentences)' :
                         'very detailed (15+ sentences)'} response.\n` +
              `Grade level: ${settings.grade_level || 11}\n` +
              `Tone: ${settings.tone || 'Neutral'}\n` +
              `Generate new content, don't just explain the input.`
            
            console.log('Making AI request to Render server...')
            
            // Update overlay - prompt built
            if (overlayWindow && !overlayWindow.isDestroyed()) {
              overlayWindow.webContents.send('update-display', {
                type: 'typing',
                status: `📝 Prompt ready (${prompt.length} chars)`,
                progress: 25,
                wpm: 0,
                charsTyped: 0
              })
            }
            
            // Use https module for the request
            const requestData = JSON.stringify({
              prompt: prompt,
              settings: settings,
              ai_filler_enabled: settings.ai_filler_enabled || false
            })
            
            const options = {
              hostname: 'slywriterapp.onrender.com',  // Use the correct server hostname
              port: 443,
              path: '/api/ai/generate',
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(requestData)
              }
            }
            
            console.log('AI Request options:', options)
            console.log('AI Request data:', requestData.substring(0, 200))
            
            // Update overlay - connecting to server
            if (overlayWindow && !overlayWindow.isDestroyed()) {
              overlayWindow.webContents.send('update-display', {
                type: 'typing',
                status: '🌐 Connecting to AI server...',
                progress: 35,
                wpm: 0,
                charsTyped: 0
              })
            }
            
            const req = https.request(options, (res) => {
              let responseData = ''
              
              res.on('data', (chunk) => {
                responseData += chunk
                // Update overlay - receiving data (real-time)
                if (overlayWindow && !overlayWindow.isDestroyed()) {
                  overlayWindow.webContents.send('update-display', {
                    type: 'typing',
                    status: `📥 Receiving response... (${responseData.length} bytes)`,
                    progress: 45 + Math.min(30, Math.floor(responseData.length / 100)),
                    wpm: 0,
                    charsTyped: responseData.length
                  })
                }
              })
              
              res.on('end', async () => {
                console.log('AI Response Status:', res.statusCode)
                
                if (res.statusCode === 200) {
                  try {
                    const result = JSON.parse(responseData)
                    const generatedText = result.text || result.response || result.content || 'No response generated'
                    
                    console.log('🎉 [ELECTRON] AI Response parsed successfully!')
                    console.log('🎉 [ELECTRON] Generated text length:', generatedText.length)
                    console.log('🎉 [ELECTRON] First 100 chars:', generatedText.substring(0, 100) + '...')
                    
                    // Apply humanizer if enabled
                    let finalText = generatedText
                    let humanizerSucceeded = false  // Track if humanizer actually worked
                    if (humanizerEnabled) {
                      console.log('Applying humanizer to AI response...')

                      // Update overlay - humanizing
                      if (overlayWindow && !overlayWindow.isDestroyed()) {
                        overlayWindow.webContents.send('update-display', {
                          type: 'typing',
                          status: '🎭 Humanizing text...',
                          progress: 85,
                          wpm: 0,
                          charsTyped: generatedText.length
                        })
                      }

                      // Call humanizer API on Render server
                      const humanizeData = JSON.stringify({
                        text: generatedText
                      })

                      const humanizeOptions = {
                        hostname: 'slywriterapp.onrender.com',
                        port: 443,
                        path: '/api/ai/humanize',
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Content-Length': Buffer.byteLength(humanizeData)
                        }
                      }

                      // Update overlay to show humanizing status
                      if (overlayWindow && !overlayWindow.isDestroyed()) {
                        overlayWindow.webContents.send('update-display', {
                          type: 'typing',
                          status: '🔄 Humanizing text...',
                          progress: 85,
                          wpm: 0,
                          charsTyped: generatedText.length
                        })
                      }

                      await new Promise((resolve, reject) => {
                        const humanizeReq = https.request(humanizeOptions, (res) => {
                          let responseData = ''
                          res.on('data', (chunk) => {
                            responseData += chunk
                          })
                          res.on('end', () => {
                            if (res.statusCode === 200) {
                              try {
                                const parsed = JSON.parse(responseData)
                                // Server returns 'text' or 'humanized' field
                                const humanizedText = parsed.text || parsed.humanized
                                if (humanizedText && humanizedText !== generatedText) {
                                  finalText = humanizedText
                                  humanizerSucceeded = true  // Only mark success if we got different text
                                  console.log('Humanized text successfully via aiundetect.com')
                                } else {
                                  console.log('Humanizer returned same text or empty, not counting as use')
                                }
                              } catch (e) {
                                console.error('Failed to parse humanizer response:', e)
                              }
                            } else {
                              console.error('Humanizer API returned status:', res.statusCode, responseData)
                            }
                            resolve()
                          })
                        })
                        humanizeReq.on('error', (error) => {
                          console.error('Humanizer error:', error)
                          resolve() // Continue with original text
                        })
                        humanizeReq.setTimeout(60000, () => {
                          console.error('Humanizer request timeout')
                          humanizeReq.destroy()
                          resolve()
                        })
                        humanizeReq.write(humanizeData)
                        humanizeReq.end()
                      })
                    }
                    
                    // Update overlay - AI complete with details
                    if (overlayWindow && !overlayWindow.isDestroyed()) {
                      overlayWindow.webContents.send('update-display', {
                        type: 'typing',
                        status: `✨ AI Complete! (${finalText.split(' ').length} words)`,
                        progress: 90,
                        wpm: 0,
                        charsTyped: finalText.length
                      })
                    }
                    
                    // Check if review mode is enabled
                    console.log('🔍 [ELECTRON] About to check review mode...')
                    console.log('🔍 [ELECTRON] Review mode value:', reviewMode)
                    console.log('🔍 [ELECTRON] Type of review mode:', typeof reviewMode)
                    console.log('🔍 [ELECTRON] Final text available:', !!finalText)
                    console.log('🔍 [ELECTRON] Main window available:', !!mainWindow && !mainWindow.isDestroyed())
                    
                    if (reviewMode) {
                      console.log('✅✅✅ [ELECTRON] REVIEW MODE IS ENABLED! Sending to renderer...')
                      // Focus the main window to show review
                      if (mainWindow && !mainWindow.isDestroyed()) {
                        console.log('✅ [ELECTRON] Showing and focusing main window')
                        mainWindow.show()
                        mainWindow.focus()
                        
                        // Small delay to ensure window is focused before sending message
                        setTimeout(() => {
                          console.log('✅ [ELECTRON] Sending show-ai-review IPC message to renderer')
                          console.log('✅ [ELECTRON] Text being sent:', finalText.substring(0, 100) + '...')
                          // Send to renderer for review
                          mainWindow.webContents.send('show-ai-review', {
                            text: finalText,
                            originalText: clipboardText,  // Pass original text for learning topic
                            originalLength: clipboardText.length,
                            generatedLength: finalText.length,
                            humanized: humanizerEnabled,
                            learningMode: settings.learning_mode || false
                          })
                          console.log('✅✅✅ [ELECTRON] IPC MESSAGE SENT TO RENDERER!')
                          console.log('✅ [ELECTRON] Message contained text of length:', finalText.length)
                        }, 100)
                      }
                      
                      if (overlayWindow && !overlayWindow.isDestroyed()) {
                        overlayWindow.webContents.send('update-display', {
                          type: 'typing',
                          status: '👁️ Review mode - Check main window',
                          progress: 100,
                          wpm: 0,
                          charsTyped: finalText.length
                        })
                      }
                      
                    } else if (pasteMode) {
                      // Copy to clipboard
                      clipboard.writeText(finalText)
                      mainWindow.webContents.send('global-hotkey-success', '⚡ AI response copied to clipboard!')
                      
                    } else {
                      // Update overlay - preparing to type
                      if (overlayWindow && !overlayWindow.isDestroyed()) {
                        overlayWindow.webContents.send('update-display', {
                          type: 'typing',
                          status: '⌨️ Starting typing automation...',
                          progress: 0,  // Start at 0 since typing will handle progress
                          wpm: 0,
                          charsTyped: 0
                        })
                      }
                      
                      // Get profile AND custom_wpm for AI-generated typing
                      let aiTypingProfile = 'Medium'
                      let aiTypingWpm = null

                      try {
                        // MIGRATION: Clean up localStorage before reading
                        console.error('🔥🔥🔥 [ELECTRON MIGRATION] BEFORE READING LOCALSTORAGE 🔥🔥🔥')

                        const profileAndWpm = await mainWindow.webContents.executeJavaScript(`
                          (() => {
                            let profile = localStorage.getItem('slywriter-selected-profile') || 'Medium'
                            let customWpm = localStorage.getItem('slywriter-custom-wpm')

                            console.error('🔥 [MIGRATION] BEFORE: profile =', profile, ', customWpm =', customWpm)

                            // MIGRATION: If profile is NOT Custom but custom WPM exists, clear it
                            if (profile !== 'Custom' && customWpm) {
                              console.error('🔥🔥🔥 [MIGRATION] MISMATCH DETECTED! 🔥🔥🔥')
                              console.error('🔥 Profile:', profile, '| Custom WPM:', customWpm)
                              console.error('🔥 CLEARING custom WPM from localStorage')
                              localStorage.removeItem('slywriter-custom-wpm')
                              customWpm = null
                            }

                            // MIGRATION: If profile is Custom but no custom WPM, force to Medium
                            if (profile === 'Custom' && !customWpm) {
                              console.error('🔥🔥🔥 [MIGRATION] ORPHAN Custom PROFILE! 🔥🔥🔥')
                              console.error('🔥 FORCING profile to Medium')
                              localStorage.setItem('slywriter-selected-profile', 'Medium')
                              profile = 'Medium'
                            }

                            console.error('🔥 [MIGRATION] AFTER: profile =', profile, ', customWpm =', customWpm)

                            return {
                              profile: profile,
                              customWpm: customWpm ? parseInt(customWpm) : null
                            }
                          })()
                        `)

                        aiTypingProfile = profileAndWpm.profile
                        aiTypingWpm = profileAndWpm.customWpm

                        console.error('🔥🔥🔥 [ELECTRON MIGRATION] FINAL VALUES 🔥🔥🔥')
                        console.error('🔥 Profile:', aiTypingProfile, '| Custom WPM:', aiTypingWpm)
                      } catch (err) {
                        console.log('Error getting AI typing settings, using defaults:', err.message)
                      }

                      console.log('🔥 [AI-GEN] Starting typing with profile:', aiTypingProfile, 'custom_wpm:', aiTypingWpm)

                      // Start typing
                      const typingData = JSON.stringify({
                        text: finalText,
                        profile: aiTypingProfile,
                        custom_wpm: aiTypingWpm,  // Include custom WPM
                        preview_mode: false
                      })
                      
                      const typingOptions = {
                        hostname: '127.0.0.1',
                        port: 8000,
                        path: '/api/typing/start',
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Content-Length': Buffer.byteLength(typingData)
                        }
                      }
                      
                      const typingReq = http.request(typingOptions, async (typingRes) => {
                        if (typingRes.statusCode === 200) {
                          mainWindow.webContents.send('global-hotkey-success', '✨ AI generated and typing started!')

                          // Track AI generation and typing usage
                          try {
                            const wordCount = finalText.split(/\s+/).filter(w => w.length > 0).length
                            console.log('📊 [AI-GEN] Tracking usage:', wordCount, 'words, humanizer:', humanizerEnabled)

                            await mainWindow.webContents.executeJavaScript(`
                              (async () => {
                                try {
                                  // Try user_data first (current key), then auth_state (legacy)
                                  const userData = localStorage.getItem('user_data');
                                  const authState = localStorage.getItem('auth_state');
                                  const dataStr = userData || authState;

                                  if (dataStr) {
                                    const data = JSON.parse(dataStr);
                                    // Extract userId from different possible locations
                                    const userId = data.email?.replace('@', '_').replace(/\\./g, '_') ||
                                                   data.user?.email?.replace('@', '_').replace(/\\./g, '_') ||
                                                   data.user?.id ||
                                                   data.user?.uid;
                                    if (userId) {
                                      const API_URL = '${isDev ? 'http://localhost:5000' : 'https://slywriterapp.onrender.com'}';

                                      // Track AI generation
                                      await fetch(API_URL + '/api/usage/track-ai-gen?user_id=' + userId, {
                                        method: 'POST'
                                      });
                                      console.log('📊 AI generation tracked for user:', userId);

                                      // Track typing words
                                      await fetch(API_URL + '/api/usage/track?user_id=' + userId + '&words=${wordCount}', {
                                        method: 'POST'
                                      });
                                      console.log('📊 Typing tracked:', ${wordCount}, 'words');

                                      // Track humanizer only if it actually succeeded
                                      ${humanizerEnabled ? `
                                      if (${humanizerSucceeded}) {
                                        await fetch(API_URL + '/api/usage/track-humanizer?user_id=' + userId, {
                                          method: 'POST'
                                        });
                                        console.log('📊 Humanizer tracked');
                                      } else {
                                        console.log('📊 Humanizer not tracked (failed or returned same text)');
                                      }
                                      ` : ''}
                                    }
                                  }
                                } catch (err) {
                                  console.error('Failed to track AI usage:', err);
                                }
                              })()
                            `).catch(err => console.log('AI usage tracking error:', err.message))
                          } catch (trackErr) {
                            console.log('Could not track AI usage:', trackErr.message)
                          }
                        } else {
                          mainWindow.webContents.send('global-hotkey-error', 'Failed to start typing')
                        }
                      })
                      
                      typingReq.on('error', (error) => {
                        console.error('Typing error:', error)
                        mainWindow.webContents.send('global-hotkey-error', 'Failed to start typing')
                      })
                      
                      typingReq.write(typingData)
                      typingReq.end()
                    }
                  } catch (parseError) {
                    console.error('Failed to parse AI response:', parseError)
                    mainWindow.webContents.send('global-hotkey-error', 'Invalid AI response')
                  }
                } else {
                  console.error('AI error response:', responseData)
                  const errorMessage = res.statusCode === 404 ? 'Endpoint not found' :
                                      res.statusCode === 500 ? 'Server error' :
                                      res.statusCode === 429 ? 'Rate limited' :
                                      `Status ${res.statusCode}`
                  
                  mainWindow.webContents.send('global-hotkey-error', `AI service error: ${errorMessage}`)
                  
                  // Update overlay - detailed error
                  if (overlayWindow && !overlayWindow.isDestroyed()) {
                    overlayWindow.webContents.send('update-display', {
                      type: 'typing',
                      status: `❌ AI Error: ${errorMessage}`,
                      progress: 0,
                      wpm: 0,
                      charsTyped: 0
                    })
                  }
                }
              })
            })
            
            req.on('error', (error) => {
              console.error('AI Request Error:', error.message)
              mainWindow.webContents.send('global-hotkey-error', `AI connection error: ${error.message}`)
            })
            
            req.write(requestData)
            req.end()
            
          } catch (error) {
            console.error('Error in AI generation:', error)
            mainWindow.webContents.send('global-hotkey-error', 'Failed to process AI request')
          } finally {
            // Restore original clipboard after a delay
            setTimeout(() => {
              if (originalClipboard) {
                console.log('Restoring original clipboard...')
                clipboard.writeText(originalClipboard)
              }
            }, 1000)
          }
        }
      }
      
      // Register the hotkey with the handler
      const success = globalShortcut.register(key, () => {
        console.log('🔥🔥🔥 [ELECTRON] AI GENERATION HOTKEY PRESSED! Key:', key)
        global.aiGenerationHandler(false)
      })
      console.log(`🔥 [ELECTRON] AI Generation hotkey (${key}) registered:`, success)
      if (!success) console.error(`Failed to register ${key} - may be in use by another app`)
    }
    
    if (keys.start) {
      const key = convertHotkey(keys.start)
      
      // Store the handler for reuse globally
      global.startTypingHandler = async () => {
        console.log('Global hotkey triggered: Start typing')
        console.log('Window focused?', mainWindow.isFocused())
        
        if (mainWindow && !mainWindow.isDestroyed()) {
          try {
            // Get text from Type Here box or clipboard
            let text = ''
            
            // Try to get text from Type Here box
            try {
              text = await mainWindow.webContents.executeJavaScript(`
                (() => {
                  console.log('Looking for Type Here input...');
                  // Try multiple selectors for the textarea
                  const selectors = [
                    'textarea[placeholder*="Type or paste"]',
                    'textarea[placeholder*="Type here"]',
                    '#typing-input',
                    'textarea.typing-input',
                    '[data-testid="typing-input"]',
                    '.typing-content textarea',
                    'textarea'  // Last resort - any textarea
                  ];
                  
                  for (const selector of selectors) {
                    const inputs = document.querySelectorAll(selector);
                    for (const input of inputs) {
                      // Check if this looks like our typing input
                      if (input && input.placeholder && 
                          (input.placeholder.toLowerCase().includes('type') || 
                           input.placeholder.toLowerCase().includes('paste'))) {
                        const value = input.value?.trim();
                        if (value) {
                          console.log('Found input with selector', selector, 'value:', value.substring(0, 50));
                          return value;
                        }
                      }
                    }
                  }
                  
                  console.log('No Type Here input with text found');
                  return '';
                })()
              `)
              console.log('Type Here text:', text ? text.substring(0, 50) + '...' : 'empty')
            } catch (err) {
              console.log('Error getting Type Here text:', err.message)
            }
            
            // If no text from Type Here, use clipboard
            if (!text) {
              text = clipboard.readText()
              console.log('Using clipboard text:', text ? text.substring(0, 50) + '...' : 'empty')
            }
            
            if (!text) {
              console.log('No text found in Type Here or clipboard')
              mainWindow.webContents.send('global-hotkey-error', 'No text in Type Here box or clipboard!')
              return
            }
            
            // Get profile AND custom_wpm from localStorage
            let profile = 'Medium'
            let customWpm = null

            try {
              profile = await mainWindow.webContents.executeJavaScript(`
                localStorage.getItem('slywriter-selected-profile') || 'Medium'
              `)

              // Defensive: trim whitespace and ensure consistent casing
              profile = (profile || 'Medium').trim()

              // Also get custom WPM setting
              const savedWpm = await mainWindow.webContents.executeJavaScript(`
                localStorage.getItem('slywriter-custom-wpm')
              `)

              if (savedWpm && savedWpm.trim() && !isNaN(parseInt(savedWpm))) {
                customWpm = parseInt(savedWpm)
                console.log('🔥 [HOTKEY] Retrieved custom WPM from localStorage:', customWpm)
              } else {
                // If no custom WPM, calculate from profile (matching app logic)
                const wpmMap = {
                  'Slow': 40,
                  'Medium': 70,
                  'Fast': 100,
                  'Lightning': 250,
                  'Custom': 85,
                  'Essay': 45
                }
                customWpm = wpmMap[profile] || 70
                console.log('🔥 [HOTKEY] No custom WPM in localStorage, using profile WPM:', customWpm, 'for profile:', profile)
                console.log('🔥 [HOTKEY] Available profiles in wpmMap:', Object.keys(wpmMap))
                console.log('🔥 [HOTKEY] Profile match found:', profile in wpmMap)
              }
            } catch (err) {
              console.log('Error getting profile/WPM, using default:', err.message)
              customWpm = 70  // Default fallback
            }

            // Check word balance BEFORE making the request
            try {
              const userString = await mainWindow.webContents.executeJavaScript(`
                localStorage.getItem('slywriter-user')
              `).catch(() => null)

              if (userString) {
                const user = JSON.parse(userString)
                const userId = user.id || user.user_id

                if (userId) {
                  console.log('🔍 Checking word balance for user:', userId)

                  // Fetch limits from server
                  const limitsResponse = await new Promise((resolve, reject) => {
                    const req = https.request({
                      hostname: 'slywriterapp.onrender.com',
                      port: 443,
                      path: `/api/usage/limits?user_id=${userId}`,
                      method: 'GET'
                    }, (res) => {
                      let data = ''
                      res.on('data', chunk => data += chunk)
                      res.on('end', () => {
                        if (res.statusCode === 200) {
                          try {
                            resolve(JSON.parse(data))
                          } catch (e) {
                            reject(e)
                          }
                        } else {
                          reject(new Error(`Failed to fetch limits: ${res.statusCode}`))
                        }
                      })
                    })
                    req.on('error', reject)
                    req.end()
                  })

                  console.log('📊 Usage limits:', limitsResponse)

                  // Check word balance
                  const wordsRemaining = limitsResponse.words_remaining
                  const wordsLimit = limitsResponse.words_limit

                  if (wordsLimit !== -1 && wordsRemaining <= 0) {
                    const errorMsg = 'Daily word limit reached. Upgrade to premium for unlimited typing.'

                    console.log('❌ Word limit reached')
                    mainWindow.webContents.send('global-hotkey-error', errorMsg)
                    mainWindow.webContents.send('show-upgrade-modal')

                    if (overlayWindow && !overlayWindow.isDestroyed()) {
                      overlayWindow.webContents.send('update-display', {
                        type: 'error',
                        status: `❌ ${errorMsg}`,
                        progress: 0
                      })
                    }
                    return
                  }

                  console.log('✅ Word balance check passed, proceeding with typing')
                }
              }
            } catch (err) {
              console.log('⚠️ Could not check word balance, proceeding anyway:', err.message)
            }

            console.log('🔥 [HOTKEY] Making API call with profile:', profile, 'custom_wpm:', customWpm, 'text length:', text.length)

            // Make API call using Node's http module (more reliable than axios in main process)
            const data = JSON.stringify({
              text: text,
              profile: profile,
              custom_wpm: customWpm,  // Include custom WPM
              preview_mode: false
            })
            
            // Use 127.0.0.1 for better compatibility (avoids IPv6 issues)
            const options = {
              hostname: '127.0.0.1',  // Force IPv4 - works on all systems
              port: 8000,
              path: '/api/typing/start',
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
              }
            }
            
            console.log('API Request:', options)
            
            const req = http.request(options, (res) => {
              let responseData = ''
              
              res.on('data', (chunk) => {
                responseData += chunk
                // Update overlay - receiving data (real-time)
                if (overlayWindow && !overlayWindow.isDestroyed()) {
                  overlayWindow.webContents.send('update-display', {
                    type: 'typing',
                    status: `📥 Receiving response... (${responseData.length} bytes)`,
                    progress: 45 + Math.min(30, Math.floor(responseData.length / 100)),
                    wpm: 0,
                    charsTyped: responseData.length
                  })
                }
              })
              
              res.on('end', async () => {
                console.log('API Response Status:', res.statusCode)
                console.log('API Response Data:', responseData)

                if (res.statusCode === 200) {
                  mainWindow.webContents.send('global-hotkey-success', 'Typing started!')

                  // Track usage for hotkey typing
                  try {
                    const wordCount = text.split(/\s+/).filter(w => w.length > 0).length
                    console.log('📊 [HOTKEY] Tracking usage:', wordCount, 'words')

                    // Call React's trackTypingUsage through window context
                    await mainWindow.webContents.executeJavaScript(`
                      (async () => {
                        try {
                          // Try user_data first (current key), then auth_state (legacy)
                          const userData = localStorage.getItem('user_data');
                          const authState = localStorage.getItem('auth_state');
                          const dataStr = userData || authState;

                          if (dataStr) {
                            const data = JSON.parse(dataStr);
                            // Extract userId from different possible locations
                            const userId = data.email?.replace('@', '_').replace(/\\./g, '_') ||
                                           data.user?.email?.replace('@', '_').replace(/\\./g, '_') ||
                                           data.user?.id ||
                                           data.user?.uid;
                            if (userId) {
                              const API_URL = '${isDev ? 'http://localhost:5000' : 'https://slywriterapp.onrender.com'}';
                              await fetch(API_URL + '/api/usage/track?user_id=' + userId + '&words=${wordCount}', {
                                method: 'POST'
                              });
                              console.log('📊 Usage tracked:', ${wordCount}, 'words for user:', userId);
                            }
                          }
                        } catch (err) {
                          console.error('Failed to track usage:', err);
                        }
                      })()
                    `).catch(err => console.log('Usage tracking error:', err.message))
                  } catch (trackErr) {
                    console.log('Could not track usage:', trackErr.message)
                  }
                } else {
                  mainWindow.webContents.send('global-hotkey-error', `API Error: ${res.statusCode}`)
                }
              })
            })
            
            req.on('error', (error) => {
              console.error('API Request Error:', error.message)
              mainWindow.webContents.send('global-hotkey-error', `Connection error: ${error.message}`)
            })
            
            req.write(data)
            req.end()
            
          } catch (error) {
            console.error('Error in start hotkey handler:', error)
            mainWindow.webContents.send('global-hotkey-error', `Error: ${error.message}`)
          }
        }
      }
      
      // Register the hotkey with the handler
      const success = globalShortcut.register(key, global.startTypingHandler)
      console.log(`Start hotkey (${key}) registered:`, success)
      if (!success) console.error(`Failed to register ${key} - may be in use by another app`)
    }
    
    if (keys.stop) {
      const key = convertHotkey(keys.stop)
      const success = globalShortcut.register(key, () => {
        console.log('Global hotkey triggered: Stop typing')
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('global-hotkey', 'stop')
        }
        
        // Update overlay - stopped
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          overlayWindow.webContents.send('update-display', {
            type: 'typing',
            status: 'Stopped',
            progress: 0,
            wpm: 0,
            charsTyped: 0
          })
        }
      })
      console.log(`Stop hotkey (${key}) registered:`, success)
      if (!success) console.error(`Failed to register ${key} - may be in use by another app`)
    }
    
    if (keys.pause) {
      const key = convertHotkey(keys.pause)
      const success = globalShortcut.register(key, () => {
        console.log('Global hotkey triggered: Pause/Resume typing')
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('global-hotkey', 'pause')
        }
        
        // Update overlay - paused (toggle handled by typing status updates)
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          overlayWindow.webContents.send('update-display', {
            type: 'typing',
            status: 'Paused',
            progress: null, // Keep current progress
            wpm: 0,
            charsTyped: null // Keep current chars
          })
        }
      })
      console.log(`Pause hotkey (${key}) registered:`, success)
      if (!success) console.error(`Failed to register ${key} - may be in use by another app`)
    }
    
    if (keys.overlay) {
      const key = convertHotkey(keys.overlay)
      const success = globalShortcut.register(key, () => {
        console.log('[MAIN] Global hotkey triggered: Toggle Electron overlay')
        // Toggle the Electron overlay that shows everywhere
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          const isVisible = overlayWindow.isVisible()
          console.log('[MAIN] Overlay current visibility:', isVisible)
          
          if (isVisible) {
            console.log('[MAIN] Hiding overlay via hotkey...')
            overlayWindow.hide()
            console.log('[MAIN] Overlay hidden')
            // Notify main window
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('overlay-visibility-changed', false)
              console.log('[MAIN] Notified main window: overlay hidden')
            }
          } else {
            console.log('[MAIN] Showing overlay via hotkey...')
            overlayWindow.show()
            overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
            // Ensure window is interactive without stealing focus
            overlayWindow.setIgnoreMouseEvents(false)
            overlayWindow.focus()
            setTimeout(() => overlayWindow.blur(), 50)
            
            // Send current hotkeys to overlay
            const currentKeys = {
              start: keys.start || 'CommandOrControl+Alt+S',
              stop: keys.stop || 'CommandOrControl+Alt+Q',
              pause: keys.pause || 'CommandOrControl+Alt+P',
              overlay: keys.overlay || 'CommandOrControl+Alt+O',
              ai_generation: keys.ai_generation || 'CommandOrControl+Shift+G'
            }
            overlayWindow.webContents.send('update-hotkeys-overlay', currentKeys)
            console.log('[MAIN] Overlay shown and hotkeys sent')
            // Notify main window
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('overlay-visibility-changed', true)
              console.log('[MAIN] Notified main window: overlay shown')
            }
          }
        } else {
          console.log('[MAIN] Overlay window not available')
        }
      })
      console.log(`[MAIN] Overlay hotkey (${key}) registered:`, success)
      if (!success) console.error(`[MAIN] Failed to register ${key} - may be in use by another app`)
    }
  }
  
  // Load saved hotkeys from a file if they exist
  let savedHotkeys = null
  try {
    const hotkeyPath = path.join(app.getPath('userData'), 'hotkeys.json')
    if (fs.existsSync(hotkeyPath)) {
      savedHotkeys = JSON.parse(fs.readFileSync(hotkeyPath, 'utf8'))
      console.log('Loaded saved hotkeys:', savedHotkeys)
    }
  } catch (err) {
    console.log('No saved hotkeys found, using defaults')
  }
  
  // Register hotkeys (saved or defaults)
  registerHotkeys(savedHotkeys)
  
  // IPC handler for approved AI text from review
  ipcMain.on('ai-review-approved', async (event, { text, pasteMode }) => {
    console.log('[MAIN] AI review approved, mode:', pasteMode ? 'paste' : 'type')
    
    if (pasteMode) {
      clipboard.writeText(text)
    } else {
      // Start typing
      const typingData = JSON.stringify({
        text: text,
        profile: 'Medium',
        preview_mode: false
      })
      
      const typingOptions = {
        hostname: '127.0.0.1',
        port: 8000,
        path: '/api/typing/start',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(typingData)
        }
      }
      
      const typingReq = http.request(typingOptions, (typingRes) => {
        if (typingRes.statusCode === 200) {
          console.log('[MAIN] Typing started from review')
        } else {
          console.error('[MAIN] Failed to start typing:', typingRes.statusCode)
        }
      })
      
      typingReq.on('error', (error) => {
        console.error('[MAIN] Typing error:', error)
      })
      
      typingReq.write(typingData)
      typingReq.end()
    }
  })
  
  // Listen for hotkey updates from renderer
  ipcMain.on('update-hotkeys', (event, hotkeys) => {
    console.log('Updating hotkeys:', hotkeys)
    registerHotkeys(hotkeys)
    
    // Send updated hotkeys to overlay
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.webContents.send('update-hotkeys-overlay', hotkeys)
      console.log('[MAIN] Sent updated hotkeys to overlay')
    }
    
    // Save hotkeys to file
    try {
      const hotkeyPath = path.join(app.getPath('userData'), 'hotkeys.json')
      fs.writeFileSync(hotkeyPath, JSON.stringify(hotkeys, null, 2))
      console.log('Saved hotkeys to:', hotkeyPath)
    } catch (err) {
      console.error('Failed to save hotkeys:', err)
    }
  })
  
  // Don't start Next.js - batch file handles it
  // No need for any Next.js startup code here
})

app.on('window-all-closed', () => {
  // Always quit the app when all windows are closed, even on macOS
  app.quit()
})

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked and no windows exist
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('before-quit', () => {
  // Clear overlay interval
  if (overlayIntervalId) {
    clearInterval(overlayIntervalId)
    overlayIntervalId = null
  }

  // Close splash window if it exists
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.destroy()
    splashWindow = null
  }

  // Close overlay window if it exists
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.destroy()
    overlayWindow = null
  }

  // Destroy tray if it exists
  if (tray && !tray.isDestroyed()) {
    tray.destroy()
    tray = null
  }
})

app.on('will-quit', (event) => {
  // If quitting for auto-update, skip blocking cleanup and let electron-updater handle it
  if (isQuittingForUpdate) {
    console.log('[AUTO-UPDATE] Quitting for update installation - skipping blocking cleanup')
    // Still do quick cleanup but don't block
    globalShortcut.unregisterAll()
    stopTypingServer()
    return // Let the quit proceed immediately
  }

  // Prevent quit until cleanup is done
  event.preventDefault()

  console.log('Cleaning up all processes...')

  // Unregister all shortcuts
  globalShortcut.unregisterAll()

  // Stop the typing server
  stopTypingServer()

  // Kill Next.js server if running
  if (nextServer) {
    try {
      // Try to kill the process tree to ensure all child processes are terminated
      if (process.platform === 'win32') {
        exec(`taskkill /pid ${nextServer.pid} /T /F`, (err) => {
          // Ignore errors
        })
      } else {
        nextServer.kill('SIGKILL')
      }
    } catch (e) {
      // Ignore errors during shutdown
    }
  }

  // Force kill any remaining SlyWriter-related processes on Windows
  if (process.platform === 'win32') {
    // Kill any remaining python processes that might be running SlyWriter scripts
    exec('taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *SlyWriter*" 2>nul', () => {
      // Give processes a moment to terminate, then exit
      setTimeout(() => {
        app.exit(0)
      }, 500)
    })
  } else {
    // On non-Windows, just exit normally
    setTimeout(() => {
      app.exit(0)
    }, 500)
  }
})

// IPC handlers for communication with renderer

// Handle typing status updates for Electron overlay
ipcMain.on('typing-status', (event, data) => {
  console.log('[MAIN] Received typing-status from renderer:', data)
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    console.log('[MAIN] Forwarding to overlay window as update-display')
    overlayWindow.webContents.send('update-display', data)
  } else {
    console.log('[MAIN] Overlay window is null or destroyed, cannot forward')
  }
})

ipcMain.handle('get-clipboard', async () => {
  const { clipboard } = require('electron')
  return clipboard.readText()
})

// Save user config (called from website after login)
ipcMain.handle('save-user-config', async (event, userConfig) => {
  try {
    const userConfigPath = path.join(app.getPath('userData'), 'user_config.json')
    console.log('[Config] Saving user config to:', userConfigPath)

    // Ensure directory exists
    const configDir = path.dirname(userConfigPath)
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true })
    }

    // Save config
    fs.writeFileSync(userConfigPath, JSON.stringify(userConfig, null, 2))
    console.log('[Config] User config saved successfully')

    // Verify license with the new config
    const licenseData = await verifyLicense()

    return {
      success: true,
      licenseValid: licenseData.valid,
      plan: licenseData.user?.plan
    }
  } catch (error) {
    console.error('[Config] Failed to save user config:', error)
    return { success: false, error: error.message }
  }
})

// Get user config
ipcMain.handle('get-user-config', async () => {
  try {
    const userConfigPath = path.join(app.getPath('userData'), 'user_config.json')
    if (fs.existsSync(userConfigPath)) {
      const config = JSON.parse(fs.readFileSync(userConfigPath, 'utf8'))
      return { success: true, config }
    }
    return { success: false, error: 'No config found' }
  } catch (error) {
    console.error('[Config] Failed to get user config:', error)
    return { success: false, error: error.message }
  }
})

// Auto-updater IPC handlers
ipcMain.handle('check-for-updates', async () => {
  return await autoUpdater.checkForUpdates()
})

ipcMain.handle('get-app-version', async () => {
  return app.getVersion()
})

// Update window IPC handlers
ipcMain.on('check-for-updates', () => {
  autoUpdater.checkForUpdates()
})

ipcMain.on('install-update', () => {
  isQuittingForUpdate = true
  autoUpdater.quitAndInstall()
})

ipcMain.on('install-update-later', () => {
  if (updateWindow && !updateWindow.isDestroyed()) {
    updateWindow.close()
  }
})

ipcMain.on('close-update-window', () => {
  if (updateWindow && !updateWindow.isDestroyed()) {
    updateWindow.close()
  }
})

ipcMain.on('get-current-version', (event) => {
  event.reply('current-version', app.getVersion())
})

// Open external URLs in the default browser
ipcMain.handle('open-external', async (event, url) => {
  console.log('Opening external URL:', url)
  shell.openExternal(url)
  return { success: true }
})

// Hotkey recording handlers
let recordingHotkey = false
let recordedKeys = []

ipcMain.handle('start-recording-hotkey', async () => {
  console.log('Starting hotkey recording...')
  recordingHotkey = true
  recordedKeys = []

  // Temporarily unregister all hotkeys to avoid conflicts
  globalShortcut.unregisterAll()

  return { recording: true }
})

ipcMain.handle('stop-recording-hotkey', async () => {
  console.log('Stopping hotkey recording')
  recordingHotkey = false

  // Re-register previous hotkeys
  try {
    const hotkeyPath = path.join(app.getPath('userData'), 'hotkeys.json')
    if (fs.existsSync(hotkeyPath)) {
      const hotkeys = JSON.parse(fs.readFileSync(hotkeyPath, 'utf8'))
      registerHotkeys(hotkeys)
    }
  } catch (err) {
    console.error('Failed to re-register hotkeys:', err)
  }

  return { recording: false }
})

ipcMain.handle('capture-hotkey', async () => {
  console.log('Waiting for hotkey capture...')

  return new Promise((resolve) => {
    // Try common modifier combinations
    const modifiers = ['CommandOrControl', 'Alt', 'Shift']
    const keys = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                  'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
                  'Space', 'Tab', 'Enter', 'Escape', 'Backspace', 'Delete',
                  'Up', 'Down', 'Left', 'Right', 'Home', 'End', 'PageUp', 'PageDown']

    let capturedHotkey = null
    const registeredAccelerators = []

    // Function to test and register combinations
    const tryRegisterCombination = (combo) => {
      if (!recordingHotkey) return false

      try {
        const registered = globalShortcut.register(combo, () => {
          if (recordingHotkey && !capturedHotkey) {
            capturedHotkey = combo
            console.log('Captured hotkey:', combo)

            // Unregister all test accelerators
            registeredAccelerators.forEach(acc => {
              try {
                globalShortcut.unregister(acc)
              } catch (e) {
                // Ignore
              }
            })

            resolve({ success: true, hotkey: combo })
          }
        })

        if (registered) {
          registeredAccelerators.push(combo)
        }

        return registered
      } catch (e) {
        return false
      }
    }

    // Try single keys first
    keys.forEach(key => {
      tryRegisterCombination(key)
    })

    // Try with single modifiers
    modifiers.forEach(mod => {
      keys.forEach(key => {
        tryRegisterCombination(`${mod}+${key}`)
      })
    })

    // Try with two modifiers
    tryRegisterCombination('CommandOrControl+Shift+A')
    tryRegisterCombination('CommandOrControl+Shift+B')
    tryRegisterCombination('CommandOrControl+Shift+C')
    tryRegisterCombination('CommandOrControl+Alt+A')
    tryRegisterCombination('CommandOrControl+Alt+B')
    tryRegisterCombination('Alt+Shift+A')
    tryRegisterCombination('Alt+Shift+B')

    // Timeout after 10 seconds
    setTimeout(() => {
      if (!capturedHotkey) {
        // Unregister all test accelerators
        registeredAccelerators.forEach(acc => {
          try {
            globalShortcut.unregister(acc)
          } catch (e) {
            // Ignore
          }
        })

        resolve({ success: false, error: 'Timeout - no hotkey captured' })
      }
    }, 10000)
  })
})

// Focus window when AI text is ready
ipcMain.handle('focus-window', async () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show()
    mainWindow.focus()
    // Restore if minimized
    if (mainWindow.isMinimized()) {
      mainWindow.restore()
    }
    // Bring to front
    mainWindow.setAlwaysOnTop(true)
    setTimeout(() => {
      mainWindow.setAlwaysOnTop(false)
    }, 100)
  }
  return true
})

ipcMain.handle('set-clipboard', async (event, text) => {
  const { clipboard } = require('electron')
  clipboard.writeText(text)
  return true
})

ipcMain.handle('update-overlay', async (event, data) => {
  if (overlayWindow) {
    overlayWindow.webContents.send('update-display', data)
    // Ensure it stays on top when updating
    overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
  }
})

ipcMain.handle('show-overlay', async () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.show()
    overlayWindow.setAlwaysOnTop(true, process.platform === 'win32' ? 'pop-up-menu' : 'screen-saver', 1)
    // Notify the main window that overlay is now visible
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('overlay-visibility-changed', true)
    }
  }
  return true
})

ipcMain.handle('hide-overlay', async () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide()
    // Notify the main window that overlay is now hidden
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('overlay-visibility-changed', false)
    }
  }
  return true  // Return true to confirm action completed
})

// Authentication handlers
ipcMain.handle('check-auth', async () => {
  try {
    // Check if user has valid token stored
    const tokenPath = path.join(app.getPath('userData'), 'auth.json')
    if (fs.existsSync(tokenPath)) {
      const authData = JSON.parse(fs.readFileSync(tokenPath, 'utf8'))
      if (authData.token) {
        // Trust the local token - don't verify with server on every check
        // This prevents redirect loops when server is slow
        console.log('Auth token found in Electron storage')
        return { authenticated: true, user: authData }

        /* Server verification disabled to prevent redirect loops
        // Verify token with server
        const serverUrl = isDev ? 'http://localhost:5000' : 'https://slywriterapp.onrender.com'

        if (axios) {
          try {
            const response = await axios.post(`${serverUrl}/auth/verify-token`, {}, {
              headers: {
                'Authorization': `Bearer ${authData.token}`
              }
            })

            if (response.data.success) {
              return { authenticated: true, user: response.data }
            }
          } catch (err) {
            console.error('Token verification failed:', err.message)
          }
        }
        */
      }
    }
    return { authenticated: false }
  } catch (err) {
    console.error('Auth check error:', err)
    return { authenticated: false }
  }
})

ipcMain.handle('save-auth', async (event, authData) => {
  try {
    const tokenPath = path.join(app.getPath('userData'), 'auth.json')
    fs.writeFileSync(tokenPath, JSON.stringify(authData), 'utf8')
    return { success: true }
  } catch (err) {
    console.error('Save auth error:', err)
    return { success: false, error: err.message }
  }
})

ipcMain.handle('clear-auth', async () => {
  try {
    const tokenPath = path.join(app.getPath('userData'), 'auth.json')
    if (fs.existsSync(tokenPath)) {
      fs.unlinkSync(tokenPath)
    }
    // Navigate to login page
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.loadURL(isDev ? 'http://localhost:3000/login' : 'https://slywriter-ui.onrender.com/login')
    }
    return { success: true }
  } catch (err) {
    console.error('Clear auth error:', err)
    return { success: false, error: err.message }
  }
})

ipcMain.handle('navigate-to-app', async () => {
  try {
    // ============== MAC AUTOMATION PERMISSION CHECK (AFTER LOGIN) ==============
    // Check/request Mac automation permission AFTER user has signed in
    // This is when users trust the app more, having seen it looks legit
    if (process.platform === 'darwin') {
      console.log('[App] User logged in - checking Mac automation permission...')
      await checkMacAutomationPermission()
    }
    // ==========================================================================

    // Navigate to main app after successful login
    if (mainWindow && !mainWindow.isDestroyed()) {
      // Navigate to the root page, not login
      const targetUrl = 'http://localhost:3000'
      console.log('Navigating to main app:', targetUrl)
      // Use webContents to navigate instead of loadURL
      mainWindow.webContents.executeJavaScript(`
        window.location.href = '/';
      `)
    }
    return { success: true }
  } catch (err) {
    console.error('Navigation error:', err)
    return { success: false, error: err.message }
  }
})
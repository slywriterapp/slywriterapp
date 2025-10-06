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
autoUpdater.autoDownload = false
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
let tray
let nextServer
let nextPort = 3000
let typingServerProcess = null

// Remove the isQuitting flag since we're not using it anymore

// Enable live reload for Electron in dev mode
const isDev = process.argv.includes('--dev')

// Import Python setup
let setupPython, PYTHON_EXE, PYTHON_DIR
try {
  const pythonSetup = require('./setup-python')
  setupPython = pythonSetup.setupPython
  PYTHON_EXE = pythonSetup.PYTHON_EXE
  PYTHON_DIR = pythonSetup.PYTHON_DIR
} catch (e) {
  console.log('Python setup module not found, will use system Python')
}

// Start the typing server (backend_api.py)
async function startTypingServer() {
  console.log('Starting typing server...')

  // Check if app is packaged
  const isPackaged = app.isPackaged

  // Get the path to the typing server
  const typingServerPath = isPackaged
    ? path.join(process.resourcesPath, 'backend_api.py')  // Production: resources folder
    : path.join(__dirname, '..', 'backend_api.py')  // Development: parent directory

  console.log('Typing server path:', typingServerPath)
  console.log('Current directory:', __dirname)
  console.log('isPackaged:', isPackaged)

  // Check if the file exists
  if (!fs.existsSync(typingServerPath)) {
    console.error('Backend API file not found at:', typingServerPath)
    console.error('Looking for backend_api.py in:', process.resourcesPath)

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
  if (setupPython) {
    try {
      console.log('Setting up bundled Python...')
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.log('🔧 Setting up Python environment... This may take a moment on first run.');
        `)
      }
      pythonPath = await setupPython((message, progress) => {
        console.log(`Setup progress: ${message} (${progress}%)`)
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.executeJavaScript(`
            console.log('📦 ${message}');
          `)
        }
      })
      console.log('Bundled Python ready at:', pythonPath)
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.log('✅ Python environment ready');
        `)
      }
    } catch (error) {
      console.error('Failed to setup bundled Python:', error)
      const errorMsg = error.message.replace(/'/g, "\\'")
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.error('⚠️ Failed to setup bundled Python: ${errorMsg}');
          console.log('⏳ Will attempt to use system Python as fallback...');
        `)
      }
      pythonPath = null // Ensure fallback to system Python
    }
  }

  // If bundled Python is available, use it
  if (pythonPath && fs.existsSync(pythonPath)) {
    try {
      typingServerProcess = spawn(pythonPath, [typingServerPath], {
        cwd: path.dirname(typingServerPath),
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
        // Check if server started successfully
        if (message.includes('Uvicorn running on') || message.includes('8000') || message.includes('Started server')) {
          serverStarted = true
          console.log('Typing server started successfully on port 8000 (bundled Python)')
          // Notify the renderer process that server is ready
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.executeJavaScript(`
              console.log('✅ Typing server started successfully (bundled Python)');
            `)
          }
        }
      })

      typingServerProcess.on('error', (error) => {
        console.error('Failed to start typing server with bundled Python:', error.message)
      })

      typingServerProcess.on('exit', (code) => {
        console.log(`Typing server exited with code ${code}`)
        typingServerProcess = null
        // If it exits quickly, it probably failed
        if (!serverStarted) {
          console.error('Bundled Python server failed to start - will try system Python')
        }
      })

      // Wait to see if it actually starts before marking as started
      setTimeout(() => {
        if (typingServerProcess && !typingServerProcess.killed) {
          serverStarted = true
          console.log('Bundled Python server confirmed running')
        }
      }, 2000)

    } catch (error) {
      console.error('Failed to start with bundled Python:', error.message)
    }
  }

  // If bundled Python didn't work, try system Python as fallback
  if (!serverStarted) {
    console.log('Bundled Python not available, trying system Python...')
    const pythonCommands = ['python', 'python3', 'py']

    for (const pythonCmd of pythonCommands) {
      if (serverStarted) break

      try {
        typingServerProcess = spawn(pythonCmd, [typingServerPath], {
          cwd: path.dirname(typingServerPath),
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
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.executeJavaScript(`
                console.log('✅ Typing server started successfully (system Python)');
              `)
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
          if (typingServerProcess && !typingServerProcess.killed) {
            serverStarted = true
          }
        }, 1000)

      } catch (error) {
        console.error(`Failed to start with ${pythonCmd}:`, error.message)
      }
    }
  }

  // Wait a bit to see if any Python command worked
  setTimeout(() => {
    if (!serverStarted) {
      console.error('Could not start typing server - Python may not be installed or dependencies missing')
      console.error('This is expected on first run. Python will be downloaded automatically.')
      console.error('If this persists, install Python manually from python.org')

      // Notify user in the renderer
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.executeJavaScript(`
          console.error('⚠️ Typing server is not running');
          console.log('📥 Python environment is being set up. This may take a few minutes on first run.');
          console.log('The app will download Python (~20MB) and install dependencies (~50MB).');
          console.log('If this doesn\\'t work automatically, you may need to:');
          console.log('  1. Install Python from https://python.org');
          console.log('  2. Run: pip install fastapi uvicorn keyboard openai python-dotenv');
          console.log('  3. Restart SlyWriter');
        `)
      }
    }
  }, 3000)
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
    height: 350,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    center: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'splash-preload.js')
    }
  })

  splashWindow.loadFile('splash.html')

  // Destroy splash window after 3 seconds
  setTimeout(() => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy()
      splashWindow = null
      // Show main window after splash
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show()
      }
    }
  }, 3000)
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
    titleBarStyle: 'hiddenInset',
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

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    // Open DevTools in development mode or when needed
    if (isDev) {
      mainWindow.webContents.openDevTools()
    }
  })

  // Fallback: show window after 5 seconds even if page hasn't loaded
  // This prevents the app from being invisible if the server is slow/down
  setTimeout(() => {
    if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isVisible()) {
      console.log('[Window] Showing window after timeout (page may not have loaded)')
      mainWindow.show()
    }
  }, 5000)
  
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
  setInterval(() => {
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
      } else if (action === 'stop' || action === 'pause') {
        // Send stop/pause to renderer
        mainWindow.webContents.send('global-hotkey', action)
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

  updateWindow = new BrowserWindow({
    width: 500,
    height: 350,
    frame: false,
    transparent: true,
    alwaysOnTop: false, // NOT always on top - less intrusive
    resizable: false,
    skipTaskbar: false, // Show in taskbar so users can find it
    x: screenWidth - 520, // Position bottom-right with margin
    y: screenHeight - 370,
    modal: false, // NOT modal - don't block main window
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  updateWindow.loadFile('update.html')

  updateWindow.on('closed', () => {
    updateWindow = null
  })

  // Close update window when clicking outside (lose focus)
  updateWindow.on('blur', () => {
    // Don't auto-close, let user close manually or it will close on install
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

  autoUpdater.autoDownload = false
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
    console.log('[AUTO-UPDATE] Ready to install on restart')
    console.log('[AUTO-UPDATE] ========================================')

    // Send to update window
    if (updateWindow && !updateWindow.isDestroyed()) {
      updateWindow.webContents.send('update-downloaded', info)
    }
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

  // Start the typing server
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

  // Show splash screen first
  createSplashScreen()

  createWindow()
  createOverlay()
  createTray()

  // Initialize auto-updater
  setupAutoUpdater()

  // ============== PERIODIC LICENSE RE-VERIFICATION ==============
  // Re-verify license every 30 minutes while app is running
  setInterval(async () => {
    console.log('[App] Periodic license re-verification...')
    const licenseData = await verifyLicense()

    if (!licenseData.valid) {
      console.warn('[App] License is no longer valid!')

      // Show warning dialog but don't quit immediately (grace period)
      await dialog.showMessageBox({
        type: 'warning',
        title: 'License Verification Failed',
        message: 'Your license could not be verified',
        detail: 'Please check your internet connection. The app will continue working for the next 24 hours.',
        buttons: ['OK']
      })
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
            const humanizerEnabled = settings.humanizer || false
            
            console.log('🚀 [ELECTRON] AI settings:', settings)
            console.log('🚀 [ELECTRON] Paste mode:', pasteMode)
            console.log('🚀 [ELECTRON] Review mode value:', settings.review_mode)
            console.log('🚀 [ELECTRON] Review mode type:', typeof settings.review_mode)
            console.log('🚀 [ELECTRON] Review mode decision:', reviewMode)
            console.log('🚀 [ELECTRON] Humanizer enabled:', humanizerEnabled)
            
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
                      
                      // Call humanizer API
                      const humanizeData = JSON.stringify({
                        text: generatedText,
                        settings: settings
                      })
                      
                      const humanizeOptions = {
                        hostname: '127.0.0.1',
                        port: 8000,
                        path: '/api/humanizer/process',
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Content-Length': Buffer.byteLength(humanizeData)
                        }
                      }
                      
                      await new Promise((resolve, reject) => {
                        const humanizeReq = http.request(humanizeOptions, (res) => {
                          let responseData = ''
                          res.on('data', (chunk) => {
                            responseData += chunk
                          })
                          res.on('end', () => {
                            if (res.statusCode === 200) {
                              try {
                                const parsed = JSON.parse(responseData)
                                finalText = parsed.text || generatedText
                                console.log('Humanized text successfully')
                              } catch (e) {
                                console.error('Failed to parse humanizer response:', e)
                              }
                            }
                            resolve()
                          })
                        })
                        humanizeReq.on('error', (error) => {
                          console.error('Humanizer error:', error)
                          resolve() // Continue with original text
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
                      
                      // Start typing
                      const typingData = JSON.stringify({
                        text: finalText,
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
                          mainWindow.webContents.send('global-hotkey-success', '✨ AI generated and typing started!')
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
            
            // Get profile from localStorage
            let profile = 'Medium'
            try {
              profile = await mainWindow.webContents.executeJavaScript(`
                localStorage.getItem('slywriter-selected-profile') || 'Medium'
              `)
            } catch (err) {
              console.log('Error getting profile, using default:', err.message)
            }
            
            console.log('Making API call with profile:', profile, 'text length:', text.length)
            
            // Make API call using Node's http module (more reliable than axios in main process)
            const data = JSON.stringify({
              text: text,
              profile: profile,
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
              
              res.on('end', () => {
                console.log('API Response Status:', res.statusCode)
                console.log('API Response Data:', responseData)
                
                if (res.statusCode === 200) {
                  mainWindow.webContents.send('global-hotkey-success', 'Typing started!')
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
  // Close overlay window if it exists
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.destroy()
  }
  
  // Destroy tray if it exists
  if (tray && !tray.isDestroyed()) {
    tray.destroy()
  }
})

app.on('will-quit', (event) => {
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
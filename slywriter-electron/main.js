const { app, BrowserWindow, ipcMain, globalShortcut, Tray, Menu, screen, clipboard, shell, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, exec } = require('child_process')
const http = require('http')
const https = require('https')
const { autoUpdater } = require('electron-updater')

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

// Remove the isQuitting flag since we're not using it anymore

// Enable live reload for Electron in dev mode
const isDev = process.argv.includes('--dev')

// Simple cleanup - no complex killing
function cleanupPreviousInstances() {
  console.log('Starting Electron app...')
  // No cleanup needed - batch file handles it
}

// Removed unused port and waiting functions - keeping it simple

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1500,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    frame: true,
    backgroundColor: '#000000',
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

  // Load the Next.js app - always start with login page
  if (isDev) {
    // Simple: Just wait a bit and load port 3000
    console.log('Loading Next.js from localhost:3000...')
    setTimeout(() => {
      // Always load login page first to ensure authentication
      mainWindow.loadURL('http://localhost:3000/login')
    }, 2000)
  } else {
    // In production, try local first then fallback to simple HTML
    mainWindow.loadURL('http://localhost:3000/login').catch(() => {
      // If local server isn't running, show a simple message
      mainWindow.loadURL('data:text/html,<h1>Please start the SlyWriter UI server</h1>')
    })
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    // Open DevTools in development mode or when needed
    if (isDev) {
      mainWindow.webContents.openDevTools()
    }
  })
  
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
      webSecurity: true
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
  
  // Handle typing status updates for Electron overlay
  ipcMain.on('typing-status', (event, data) => {
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.webContents.send('update-display', data)
    }
  })
  
  // Send current hotkeys to overlay when it's ready
  overlayWindow.webContents.on('did-finish-load', () => {
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
function setupAutoUpdater() {
  // Configure auto-updater
  autoUpdater.setFeedURL({
    provider: 'generic',
    url: 'https://slywriter-update-server.onrender.com/updates'
  })

  // Check for updates immediately and then every 30 minutes
  autoUpdater.checkForUpdates()
  setInterval(() => {
    autoUpdater.checkForUpdates()
  }, 30 * 60 * 1000) // 30 minutes

  // Auto-updater event handlers
  autoUpdater.on('checking-for-update', () => {
    console.log('Checking for updates...')
  })

  autoUpdater.on('update-available', (info) => {
    console.log('Update available:', info.version)

    // Show dialog to user
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version (${info.version}) is available!`,
      detail: 'Would you like to download it now? The update will be installed when you restart the app.',
      buttons: ['Download Now', 'Later'],
      defaultId: 0,
      cancelId: 1
    }).then(result => {
      if (result.response === 0) {
        autoUpdater.downloadUpdate()

        // Show download progress in tray or main window
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('update-downloading', info)
        }
      }
    })
  })

  autoUpdater.on('update-not-available', () => {
    console.log('No updates available')
  })

  autoUpdater.on('download-progress', (progressObj) => {
    console.log(`Download progress: ${progressObj.percent}%`)

    // Send progress to renderer
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('update-progress', progressObj)
    }
  })

  autoUpdater.on('update-downloaded', (info) => {
    console.log('Update downloaded:', info.version)

    // Notify user that update is ready
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: 'Update has been downloaded!',
      detail: 'The application will be updated after restart. Would you like to restart now?',
      buttons: ['Restart Now', 'Later'],
      defaultId: 0,
      cancelId: 1
    }).then(result => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall()
      }
    })
  })

  autoUpdater.on('error', (error) => {
    console.error('Update error:', error)

    // Only show error in development
    if (process.env.NODE_ENV === 'development') {
      dialog.showErrorBox('Update Error', error.toString())
    }
  })
}

// App event handlers
app.whenReady().then(() => {
  // Simple startup - no cleanup needed
  cleanupPreviousInstances()

  createWindow()
  createOverlay()
  createTray()

  // Initialize auto-updater
  setupAutoUpdater()
  
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

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll()
  
  // Kill all spawned processes
  console.log('Cleaning up all processes...')
  
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
  
  // Simple cleanup - user will manage Node.js manually
})

// IPC handlers for communication with renderer
ipcMain.handle('get-clipboard', async () => {
  const { clipboard } = require('electron')
  return clipboard.readText()
})

// Auto-updater IPC handlers
ipcMain.handle('check-for-updates', async () => {
  return await autoUpdater.checkForUpdates()
})

ipcMain.handle('get-app-version', async () => {
  return app.getVersion()
})

// Open external URLs in the default browser
ipcMain.handle('open-external', async (event, url) => {
  console.log('Opening external URL:', url)
  shell.openExternal(url)
  return { success: true }
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
      mainWindow.loadURL(isDev ? 'http://localhost:3000/login' : 'http://localhost:3000/login')
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
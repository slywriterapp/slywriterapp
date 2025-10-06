const { contextBridge, ipcRenderer } = require('electron')

// Expose a simple API to close the splash screen if needed
contextBridge.exposeInMainWorld('electronAPI', {
  closeSplash: () => ipcRenderer.send('close-splash'),
  onSetupProgress: (callback) => ipcRenderer.on('setup-progress', (event, message) => callback(message)),
  onSetupComplete: (callback) => ipcRenderer.on('setup-complete', () => callback()),
  onSetupError: (callback) => ipcRenderer.on('setup-error', (event, error) => callback(error))
})
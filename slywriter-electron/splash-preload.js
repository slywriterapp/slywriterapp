const { contextBridge, ipcRenderer } = require('electron')

// Expose a simple API to close the splash screen if needed
contextBridge.exposeInMainWorld('electronAPI', {
  closeSplash: () => ipcRenderer.send('close-splash')
})
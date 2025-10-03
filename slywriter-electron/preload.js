const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: {
    on: (channel, func) => {
      const validChannels = ['global-hotkey', 'navigate', 'update-display', 'toggle-overlay', 'global-hotkey-success', 'global-hotkey-error', 'global-hotkey-with-text', 'overlay-command', 'overlay-visibility-changed', 'update-hotkeys-overlay', 'show-ai-review']
      if (validChannels.includes(channel)) {
        // Deliberately strip event as it includes `sender`
        ipcRenderer.on(channel, (event, ...args) => func(...args))
      }
    },
    removeListener: (channel, func) => {
      const validChannels = ['global-hotkey', 'navigate', 'update-display', 'toggle-overlay', 'show-ai-review', 'overlay-visibility-changed']
      if (validChannels.includes(channel)) {
        ipcRenderer.removeListener(channel, func)
      }
    },
    send: (channel, ...args) => {
      const validChannels = ['move-overlay', 'hide-overlay', 'hide-overlay-request', 'update-hotkeys', 'typing-status', 'toggle-electron-overlay', 'overlay-action']
      if (validChannels.includes(channel)) {
        ipcRenderer.send(channel, ...args)
      }
    },
    invoke: (channel, ...args) => {
      const validChannels = ['hide-overlay', 'show-overlay', 'toggle-overlay', 'set-clipboard', 'get-clipboard', 'focus-window', 'check-auth', 'save-auth', 'clear-auth', 'navigate-to-app', 'save-user-config', 'get-user-config']
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args)
      }
    }
  }
})
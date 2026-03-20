const { contextBridge, ipcRenderer } = require('electron')

// En caso de que necesitemos una API de Electron en el frontend
contextBridge.exposeInMainWorld('electronAPI', {
    window: {
        close: () => ipcRenderer.send('window:close'),
        minimize: () => ipcRenderer.send('window:minimize'),
        toggleMaximize: () => ipcRenderer.send('window:toggleMaximize')
    },
    isElectron: true
})

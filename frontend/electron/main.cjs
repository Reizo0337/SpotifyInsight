const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

const isDev = !app.isPackaged

function createWindow() {
    const win = new BrowserWindow({
        width: 1920,
        height: 1080,
        frame: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            contextIsolation: true,
            nodeIntegration: false
        }
    })

    ipcMain.on('window:close', () => win.close())
    ipcMain.on('window:minimize', () => win.minimize())
    ipcMain.on('window:toggleMaximize', () => {
        if (win.isMaximized()) win.unmaximize()
        else win.maximize()
    })

    win.setMenu(null);
    win.maximize();

    // Load the built files from dist (native)
    win.loadFile(path.join(__dirname, '../dist/index.html'))
}

app.whenReady().then(() => {
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
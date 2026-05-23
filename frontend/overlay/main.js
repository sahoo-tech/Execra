/**
 * frontend/overlay/main.js
 *
 * Electron main process for the Execra guidance overlay.
 *
 * Creates a frameless, always-on-top, semi-transparent BrowserWindow that
 * floats over the user's screen and displays real-time guidance from the
 * Execra backend via WebSocket.
 *
 * Security:
 *  - contextIsolation: true  — renderer cannot access Node APIs directly
 *  - nodeIntegration: false  — renderer is sandboxed
 *  - preload script exposes only the safe window.execra API via contextBridge
 *
 * IPC channels:
 *  - 'overlay-minimize'  — shrinks the window to collapsed state
 *  - 'overlay-restore'   — restores the window to full height
 *  - 'overlay-close'     — quits the application
 */

const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const OVERLAY_WIDTH  = 380;
const OVERLAY_HEIGHT = 520;
const OVERLAY_MIN_HEIGHT = 56;   // collapsed (title bar only)
const MARGIN = 20;               // distance from screen edge

let mainWindow = null;

// ---------------------------------------------------------------------------
// Window factory
// ---------------------------------------------------------------------------

function createOverlayWindow() {
  const { width: screenWidth, height: screenHeight } =
    screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width:  OVERLAY_WIDTH,
    height: OVERLAY_HEIGHT,
    x: screenWidth  - OVERLAY_WIDTH  - MARGIN,
    y: screenHeight - OVERLAY_HEIGHT - MARGIN,

    // Appearance
    frame:       false,
    transparent: true,
    hasShadow:   true,
    vibrancy:    'dark',          // macOS frosted-glass effect (ignored elsewhere)
    visualEffectState: 'active',

    // Behaviour
    alwaysOnTop:         true,
    skipTaskbar:         false,
    resizable:           false,
    minimizable:         false,   // custom minimize via IPC
    fullscreenable:      false,
    movable:             true,

    // Security
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration:  false,
      sandbox:          true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Keep the overlay on top of other always-on-top windows too
  mainWindow.setAlwaysOnTop(true, 'screen-saver');

  // Dev tools in dev mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  mainWindow.on('closed', () => { mainWindow = null; });
}

// ---------------------------------------------------------------------------
// IPC handlers
// ---------------------------------------------------------------------------

ipcMain.on('overlay-minimize', () => {
  if (!mainWindow) return;
  mainWindow.setSize(OVERLAY_WIDTH, OVERLAY_MIN_HEIGHT, true);
});

ipcMain.on('overlay-restore', () => {
  if (!mainWindow) return;
  mainWindow.setSize(OVERLAY_WIDTH, OVERLAY_HEIGHT, true);
});

ipcMain.on('overlay-close', () => {
  app.quit();
});

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(() => {
  createOverlayWindow();

  // macOS: re-create window when dock icon is clicked and no windows are open
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createOverlayWindow();
  });
});

app.on('window-all-closed', () => {
  // On macOS apps typically stay alive — quit unconditionally here
  // since the overlay is meant to be explicitly closed.
  app.quit();
});

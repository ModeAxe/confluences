const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const BackgroundSegmentationService = require('./backgroundSegmentation');

let mainWindow;
let segmentationService;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    title: 'Confluences - Body Segmentation App'
  });

  // Load the app
  mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Start background segmentation service
  startBackgroundSegmentation();
}

async function startBackgroundSegmentation() {
  try {
    segmentationService = new BackgroundSegmentationService();
    await segmentationService.initialize();
    
    // Watch the captures folder for new images
    const capturesDir = path.join(__dirname, 'Confluences', 'captures');
    segmentationService.startWatching(capturesDir);
    console.log('🎯 Background segmentation service started');
  } catch (error) {
    console.error('❌ Failed to start background segmentation service:', error);
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  // Stop background service before quitting
  if (segmentationService) {
    segmentationService.stop();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Ensure output directories exist
function ensureOutputDirectories() {
  const dirs = ['output/captures', 'Confluences/captures'];
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

app.whenReady().then(ensureOutputDirectories);

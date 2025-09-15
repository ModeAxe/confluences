const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs-extra');
const chokidar = require('chokidar');
const tf = require('@tensorflow/tfjs-node');
const bodyPix = require('@tensorflow-models/body-pix');

class BodyPixWatcher {
  constructor() {
    this.watchDir = '';
    this.outputDir = '';
    this.model = null;
    this.processingQueue = [];
    this.processedFiles = new Set();
    this.isProcessing = false;
    this.watcher = null;
  }

  async initialize() {
    console.log('🤖 Loading BodyPix model...');
    try {
      this.model = await bodyPix.load({
        architecture: 'MobileNetV1',
        outputStride: 16,
        multiplier: 0.75,
        quantBytes: 2
      });
      console.log('✅ BodyPix model loaded successfully');
      console.log('Available methods:', Object.getOwnPropertyNames(this.model));
      console.log('Model prototype methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this.model)));
    } catch (error) {
      console.error('❌ Failed to load BodyPix model:', error);
      throw error;
    }
  }

  startWatching(watchDir, outputDir) {
    // Resolve paths to absolute paths
    this.watchDir = path.resolve(watchDir);
    this.outputDir = path.resolve(outputDir);
    
    // Stop existing watcher if any
    if (this.watcher) {
      this.watcher.close();
    }
    
    // Create output directories
    this.createOutputDirectories();
    
    // Check if watch directory exists
    if (!fs.existsSync(this.watchDir)) {
      throw new Error(`Watch directory does not exist: ${this.watchDir}`);
    }
    
    console.log(`👀 Starting to watch directory: ${this.watchDir}`);
    
    // Start watching
    this.watcher = chokidar.watch(this.watchDir, {
      ignored: /(^|[\/\\])\../, // ignore dotfiles
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 1000, // Wait 1 second after file stops changing
        pollInterval: 100
      }
    });

    this.watcher.on('add', (filePath) => {
      console.log(`📁 File detected: ${filePath}`);
      if (this.isImageFile(filePath) && !this.processedFiles.has(filePath)) {
        console.log(`📸 New image detected: ${path.basename(filePath)}`);
        this.addToQueue(filePath);
      } else if (!this.isImageFile(filePath)) {
        console.log(`⏭️  Skipping non-image file: ${path.basename(filePath)}`);
      } else {
        console.log(`⏭️  Already processed: ${path.basename(filePath)}`);
      }
    });

    this.watcher.on('error', (error) => {
      console.error('❌ Watcher error:', error);
    });

    this.watcher.on('ready', () => {
      console.log(`✅ Watcher ready, monitoring: ${this.watchDir}`);
    });
  }

  createOutputDirectories() {
    const bodyParts = ['head', 'left_arm', 'right_arm', 'torso', 'left_leg', 'right_leg'];
    
    bodyParts.forEach(part => {
      const dir = path.join(this.outputDir, part);
      fs.ensureDirSync(dir);
    });
    
    console.log('📁 Created output directories');
  }

  isImageFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'].includes(ext);
  }

  addToQueue(filePath) {
    this.processingQueue.push(filePath);
    this.processQueue();
  }

  async processQueue() {
    if (this.isProcessing || this.processingQueue.length === 0) {
      return;
    }

    this.isProcessing = true;
    
    while (this.processingQueue.length > 0) {
      const filePath = this.processingQueue.shift();
      
      if (this.processedFiles.has(filePath)) {
        continue; // Skip if already processed
      }

      try {
        await this.processImage(filePath);
        this.processedFiles.add(filePath);
        console.log(`✅ Processed: ${path.basename(filePath)}`);
      } catch (error) {
        console.error(`❌ Error processing ${path.basename(filePath)}:`, error);
      }
    }

    this.isProcessing = false;
  }

  async processImage(imagePath) {
    console.log(`🔄 Processing: ${path.basename(imagePath)}`);
    
    // Read image and convert to the format BodyPix expects
    const imageBuffer = fs.readFileSync(imagePath);
    const decodedImage = tf.node.decodeImage(imageBuffer, 3); // Force 3 channels (RGB)
    
    console.log('Decoded image shape:', decodedImage.shape);
    
    // BodyPix expects [height, width, channels] format
    // If the image is [width, height, channels], we need to transpose it
    let image = decodedImage;
    if (decodedImage.shape[0] > decodedImage.shape[1]) {
      // Image is [width, height, channels], transpose to [height, width, channels]
      image = tf.transpose(decodedImage, [1, 0, 2]);
      console.log('Transposed image shape:', image.shape);
    }
    
    // Check if image might be rotated (landscape vs portrait)
    const [height, width] = image.shape;
    console.log(`Image dimensions: ${width}x${height} (width x height)`);
    
    if (width > height) {
      console.log('Image appears to be landscape orientation');
    } else {
      console.log('Image appears to be portrait orientation');
    }
    
    // Try rotating the image if it might be upside down or sideways
    // BodyPix expects the person to be upright
    let rotatedImage = image;
    const aspectRatio = width / height;
    console.log(`Aspect ratio: ${aspectRatio.toFixed(2)}`);
    
    // If aspect ratio suggests the image might be rotated, try different orientations
    if (aspectRatio < 0.8) { // Very tall image, might be rotated
      console.log('Image is very tall, trying 90-degree rotation');
      // Rotate 90 degrees clockwise: transpose and flip
      rotatedImage = tf.transpose(image, [1, 0, 2]);
      rotatedImage = tf.reverse(rotatedImage, [1]);
    } else if (aspectRatio > 1.5) { // Very wide image, might be rotated
      console.log('Image is very wide, trying 90-degree rotation');
      // Rotate 90 degrees counter-clockwise: transpose and flip
      rotatedImage = tf.transpose(image, [1, 0, 2]);
      rotatedImage = tf.reverse(rotatedImage, [0]);
    }
    
    // Use the rotated image if we rotated it
    if (rotatedImage !== image) {
      console.log('Using rotated image for segmentation');
      image.dispose(); // Dispose original
      image = rotatedImage;
    }
    
    // Run body part segmentation using the original BodyPix API
    if (!this.model) {
      throw new Error('Model not loaded');
    }
    
    console.log('Model methods:', Object.getOwnPropertyNames(this.model));
    console.log('Model prototype methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this.model)));
    
    let segmentation;
    if (typeof this.model.segmentPersonParts === 'function') {
      segmentation = await this.model.segmentPersonParts(image);
    } else if (typeof this.model.estimatePartSegmentation === 'function') {
      segmentation = await this.model.estimatePartSegmentation(image);
    } else {
      throw new Error('No part segmentation method found on model');
    }
    
    // Extract body parts
    const bodyParts = this.extractBodyParts(segmentation);
    
    // Save results
    await this.saveBodyParts(imagePath, bodyParts);
    
    // Cleanup
    decodedImage.dispose();
    if (image !== decodedImage) {
      image.dispose(); // Dispose transposed/rotated tensor if it was created
    }
    // Only dispose if segmentation has a data property
    if (segmentation.data && typeof segmentation.data.dispose === 'function') {
      segmentation.data.dispose();
    }
  }

  extractBodyParts(segmentation) {
    const bodyParts = {};
    
    console.log('Segmentation result keys:', Object.keys(segmentation));
    console.log('Segmentation result:', segmentation);
    
    // BodyPix part segmentation returns data with part IDs
    if (segmentation.data) {
      const partMask = tf.tensor3d(segmentation.data, [1, segmentation.height, segmentation.width]);
      
      console.log('Part mask shape:', partMask.shape);
      console.log('Part mask data sample:', segmentation.data.slice(0, 100));
      
    // First, let's see what part IDs are actually in the data
    const uniqueValues = [...new Set(segmentation.data)];
    console.log('Unique part IDs in segmentation:', uniqueValues);
    
    // Official BodyPix part ID mappings (from TensorFlow.js documentation)
    const partGroups = {
      'head': [0, 1], // Left Face: 0, Right Face: 1
      'left_arm': [2, 3, 6, 7, 10], // Left Upper Arm Front: 2, Back: 3, Left Lower Arm Front: 6, Back: 7, Left Hand: 10
      'right_arm': [4, 5, 8, 9, 11], // Right Upper Arm Front: 4, Back: 5, Right Lower Arm Front: 8, Back: 9, Right Hand: 11
      'torso': [12, 13], // Torso Front: 12, Torso Back: 13
      'left_leg': [14, 15, 18, 19, 22], // Left Upper Leg Front: 14, Back: 15, Left Lower Leg Front: 18, Back: 19, Left Foot: 22
      'right_leg': [16, 17, 20, 21, 23] // Right Upper Leg Front: 16, Back: 17, Right Lower Leg Front: 20, Back: 21, Right Foot: 23
    };
    
    // Let's also check what parts are actually detected
    for (const [groupName, groupPartIds] of Object.entries(partGroups)) {
      const foundParts = groupPartIds.filter(partId => uniqueValues.includes(partId));
      console.log(`${groupName} parts found:`, foundParts);
    }

      for (const [groupName, groupPartIds] of Object.entries(partGroups)) {
        let groupMask = tf.zerosLike(partMask).cast('bool');
        
        groupPartIds.forEach(partId => {
          const partMaskForId = tf.equal(partMask, partId);
          groupMask = tf.logicalOr(groupMask, partMaskForId);
        });

        bodyParts[groupName] = groupMask;
      }
    } else {
      console.error('No segmentation data available');
      return {};
    }

    return bodyParts;
  }

  async saveBodyParts(imagePath, bodyParts) {
    const baseName = path.basename(imagePath, path.extname(imagePath));
    
    // Load the original image for cutout
    const imageBuffer = fs.readFileSync(imagePath);
    let originalImage = tf.node.decodeImage(imageBuffer, 3);
    
    // Flip image vertically in-place to correct orientation
    const tempImage = tf.reverse(originalImage, [0]);
    originalImage.dispose(); // Clean up the original
    originalImage = tempImage; // Replace with flipped version
    
    // Check if original image needs transposition to match segmentation dimensions
    const [origHeight, origWidth, origChannels] = originalImage.shape;
    console.log(`Original image shape: [${origHeight}, ${origWidth}, ${origChannels}]`);
    
    for (const [partName, mask] of Object.entries(bodyParts)) {
      // Remove batch dimension from mask
      const squeezedMask = tf.squeeze(mask, [0]); // Remove batch dimension: [1,H,W] -> [H,W]
      const [maskHeight, maskWidth] = squeezedMask.shape;
      console.log(`Mask shape for ${partName}: [${maskHeight}, ${maskWidth}]`);
      
      // Check if we need to transpose the original image to match mask dimensions
      let processedImage = originalImage;
      if (origHeight === maskWidth && origWidth === maskHeight) {
        console.log(`Transposing original image to match mask dimensions`);
        processedImage = tf.transpose(originalImage, [1, 0, 2]);
      }
      //flip image vertically and horizontally
      processedImage = tf.reverse(processedImage, [0]);
      processedImage = tf.reverse(processedImage, [1]);
      
      // Create cutout by applying mask to original image
      const mask3D = tf.expandDims(squeezedMask, 2); // Add channel dimension: [H,W] -> [H,W,1]
      const mask3DRepeated = tf.tile(mask3D, [1, 1, 3]); // Repeat for RGB: [H,W,1] -> [H,W,3]
      const cutoutImage = tf.mul(processedImage, mask3DRepeated);
      
      // Convert to PNG
      const cutoutBuffer = await tf.node.encodePng(cutoutImage);
      
      // Save to appropriate folder
      const outputPath = path.join(this.outputDir, partName, `${partName}_${baseName}.png`);
      fs.writeFileSync(outputPath, cutoutBuffer);
      
      // Cleanup
      mask.dispose();
      if (processedImage !== originalImage) {
        processedImage.dispose();
      }
      squeezedMask.dispose();
      mask3D.dispose();
      mask3DRepeated.dispose();
      cutoutImage.dispose();
    }
    
    // Cleanup original image
    originalImage.dispose();
  }

  stop() {
    if (this.watcher) {
      this.watcher.close();
    }
  }
}

// Electron main process
let mainWindow;
let bodyPixWatcher;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');
  
  // Initialize BodyPix watcher
  bodyPixWatcher = new BodyPixWatcher();
  bodyPixWatcher.initialize().then(() => {
    console.log('🚀 BodyPix Watcher ready');
  }).catch(error => {
    console.error('Failed to initialize:', error);
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (bodyPixWatcher) {
    bodyPixWatcher.stop();
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

// IPC handlers
ipcMain.handle('start-watching', async (event, watchDir, outputDir) => {
  try {
    bodyPixWatcher.startWatching(watchDir, outputDir);
    return { success: true };
  } catch (error) {
    console.error('Start watching error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-watching', async () => {
  try {
    bodyPixWatcher.stop();
    return { success: true };
  } catch (error) {
    console.error('Stop watching error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('test-directory', async (event, watchDir) => {
  try {
    const exists = fs.existsSync(watchDir);
    const isDir = exists ? fs.statSync(watchDir).isDirectory() : false;
    const files = exists && isDir ? fs.readdirSync(watchDir) : [];
    const imageFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'].includes(ext);
    });
    
    return { 
      success: true, 
      exists, 
      isDirectory: isDir, 
      totalFiles: files.length,
      imageFiles: imageFiles.length,
      sampleFiles: files.slice(0, 5)
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

const path = require('path');
const fs = require('fs-extra');
const chokidar = require('chokidar');
const tf = require('@tensorflow/tfjs-node');
const bodyPix = require('@tensorflow-models/body-pix');

class BackgroundSegmentationService {
  constructor() {
    this.model = null;
    this.isProcessing = false;
    this.watcher = null;
    this.processedFiles = new Set();
    this.processingQueue = [];
  }

  async initialize() {
    console.log('🤖 Loading BodyPix model for background processing...');
    try {
      this.model = await bodyPix.load({
        architecture: 'MobileNetV1',
        outputStride: 16,
        multiplier: 0.75,
        quantBytes: 2
      });
      console.log('✅ Background segmentation service ready');
    } catch (error) {
      console.error('❌ Failed to load BodyPix model:', error);
      throw error;
    }
  }

  startWatching(capturesDir) {
    const outputDir = path.join(capturesDir, '..', 'output');
    
    // Create output directories
    this.createOutputDirectories(outputDir);
    
    console.log(`👀 Background service watching: ${capturesDir}`);
    console.log(`📁 Output directory: ${outputDir}`);
    
    // Start watching captures folder
    this.watcher = chokidar.watch(capturesDir, {
      ignored: /(^|[\/\\])\../,
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 1000,
        pollInterval: 100
      }
    });

    this.watcher.on('add', (filePath) => {
      if (this.isImageFile(filePath) && !this.processedFiles.has(filePath)) {
        console.log(`📸 New captured image detected: ${path.basename(filePath)}`);
        this.addToQueue(filePath, outputDir);
      }
    });

    this.watcher.on('error', (error) => {
      console.error('❌ Background watcher error:', error);
    });

    this.watcher.on('ready', () => {
      console.log(`✅ Background segmentation service monitoring: ${capturesDir}`);
    });
  }

  addToQueue(filePath, outputDir) {
    this.processingQueue.push({ filePath, outputDir });
    this.processQueue();
  }

  async processQueue() {
    if (this.isProcessing || this.processingQueue.length === 0) {
      return;
    }

    this.isProcessing = true;
    
    while (this.processingQueue.length > 0) {
      const { filePath, outputDir } = this.processingQueue.shift();
      
      if (this.processedFiles.has(filePath)) {
        continue;
      }

      try {
        await this.processImage(filePath, outputDir);
        this.processedFiles.add(filePath);
        console.log(`✅ Background processed: ${path.basename(filePath)}`);
      } catch (error) {
        console.error(`❌ Background error processing ${path.basename(filePath)}:`, error);
      }
    }

    this.isProcessing = false;
  }

  async processImage(imagePath, outputDir) {
    console.log(`🔄 Background processing: ${path.basename(imagePath)}`);
    
    // Read image and convert to the format BodyPix expects
    const imageBuffer = fs.readFileSync(imagePath);
    const decodedImage = tf.node.decodeImage(imageBuffer, 3);
    
    // BodyPix expects [height, width, channels] format
    let image = decodedImage;
    if (decodedImage.shape[0] > decodedImage.shape[1]) {
      image = tf.transpose(decodedImage, [1, 0, 2]);
    }
    
    // Check if image might be rotated
    const [height, width] = image.shape;
    let rotatedImage = image;
    const aspectRatio = width / height;
    
    if (aspectRatio < 0.8) {
      rotatedImage = tf.transpose(image, [1, 0, 2]);
      rotatedImage = tf.reverse(rotatedImage, [1]);
    } else if (aspectRatio > 1.5) {
      rotatedImage = tf.transpose(image, [1, 0, 2]);
      rotatedImage = tf.reverse(rotatedImage, [0]);
    }
    
    if (rotatedImage !== image) {
      image.dispose();
      image = rotatedImage;
    }
    
    // Run body part segmentation
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
    await this.saveBodyParts(imagePath, bodyParts, outputDir);
    
    // Cleanup
    decodedImage.dispose();
    if (image !== decodedImage) {
      image.dispose();
    }
    if (segmentation.data && typeof segmentation.data.dispose === 'function') {
      segmentation.data.dispose();
    }
  }

  extractBodyParts(segmentation) {
    const bodyParts = {};
    
    if (segmentation.data) {
      const partMask = tf.tensor3d(segmentation.data, [1, segmentation.height, segmentation.width]);
      
      // Official BodyPix part ID mappings
      const partGroups = {
        'head': [0, 1], // Left Face: 0, Right Face: 1
        'left_arm': [2, 3, 6, 7, 10], // Left Upper Arm Front: 2, Back: 3, Left Lower Arm Front: 6, Back: 7, Left Hand: 10
        'right_arm': [4, 5, 8, 9, 11], // Right Upper Arm Front: 4, Back: 5, Right Lower Arm Front: 8, Back: 9, Right Hand: 11
        'torso': [12, 13], // Torso Front: 12, Torso Back: 13
        'left_leg': [14, 15, 18, 19, 22], // Left Upper Leg Front: 14, Back: 15, Left Lower Leg Front: 18, Back: 19, Left Foot: 22
        'right_leg': [16, 17, 20, 21, 23] // Right Upper Leg Front: 16, Back: 17, Right Lower Leg Front: 20, Back: 21, Right Foot: 23
      };

      for (const [groupName, groupPartIds] of Object.entries(partGroups)) {
        let groupMask = tf.zerosLike(partMask).cast('bool');
        
        groupPartIds.forEach(partId => {
          const partMaskForId = tf.equal(partMask, partId);
          groupMask = tf.logicalOr(groupMask, partMaskForId);
        });

        bodyParts[groupName] = groupMask;
      }
    }

    return bodyParts;
  }

  async saveBodyParts(imagePath, bodyParts, outputDir) {
    const baseName = path.basename(imagePath, path.extname(imagePath));
    
    // Load the original image for cutout
    const imageBuffer = fs.readFileSync(imagePath);
    let originalImage = tf.node.decodeImage(imageBuffer, 3);
    
    // Flip image vertically to correct orientation
    const tempImage = tf.reverse(originalImage, [0]);
    originalImage.dispose();
    originalImage = tempImage;
    
    const [origHeight, origWidth, origChannels] = originalImage.shape;
    
    for (const [partName, mask] of Object.entries(bodyParts)) {
      // Remove batch dimension from mask
      const squeezedMask = tf.squeeze(mask, [0]);
      const [maskHeight, maskWidth] = squeezedMask.shape;
      
      // Check if we need to transpose the original image to match mask dimensions
      let processedImage = originalImage;
      if (origHeight === maskWidth && origWidth === maskHeight) {
        processedImage = tf.transpose(originalImage, [1, 0, 2]);
      }
      
      // Flip image vertically and horizontally
      processedImage = tf.reverse(processedImage, [0]);
      processedImage = tf.reverse(processedImage, [1]);
      
      // Create cutout by applying mask to original image
      const mask3D = tf.expandDims(squeezedMask, 2);
      const mask3DRepeated = tf.tile(mask3D, [1, 1, 3]);
      const cutoutImage = tf.mul(processedImage, mask3DRepeated);
      
      // Convert to PNG
      const cutoutBuffer = await tf.node.encodePng(cutoutImage);
      
      // Save to appropriate folder
      const outputPath = path.join(outputDir, partName, `${partName}_${baseName}.png`);
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

  createOutputDirectories(outputDir) {
    const bodyParts = ['head', 'left_arm', 'right_arm', 'torso', 'left_leg', 'right_leg'];
    
    bodyParts.forEach(part => {
      const dir = path.join(outputDir, part);
      fs.ensureDirSync(dir);
    });
    
    console.log('📁 Created background output directories');
  }

  isImageFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'].includes(ext);
  }

  stop() {
    if (this.watcher) {
      this.watcher.close();
    }
    console.log('🛑 Background segmentation service stopped');
  }
}

module.exports = BackgroundSegmentationService;

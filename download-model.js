const https = require('https');
const fs = require('fs');
const path = require('path');

const modelBaseUrl = 'https://storage.googleapis.com/tfjs-models/savedmodel/bodypix/mobilenet/quant2/075/';
const detectionModelDir = './models/detection';
const segmentationModelDir = './models/segmentation';

// Create output directories
[detectionModelDir, segmentationModelDir].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

function downloadFile(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(filepath);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log(`✅ Downloaded: ${path.basename(filepath)}`);
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(filepath, () => {});
      reject(err);
    });
  });
}

async function downloadModelFiles(targetDir) {
  try {
    console.log(`📥 Downloading model to ${targetDir}...`);
    
    // Download model.json first
    const modelJsonUrl = modelBaseUrl + 'model-stride16.json';
    await downloadFile(modelJsonUrl, path.join(targetDir, 'model.json'));
    
    // Read model.json to get weight file names
    const modelJson = JSON.parse(fs.readFileSync(path.join(targetDir, 'model.json'), 'utf8'));
    const weightFiles = modelJson.weightsManifest[0].paths;
    
    console.log(`📦 Found ${weightFiles.length} weight files to download`);
    
    // Download each weight file
    for (const weightFile of weightFiles) {
      const weightUrl = modelBaseUrl + weightFile;
      const weightPath = path.join(targetDir, weightFile);
      
      // Create subdirectory if needed
      const weightDir = path.dirname(weightPath);
      if (!fs.existsSync(weightDir)) {
        fs.mkdirSync(weightDir, { recursive: true });
      }
      
      await downloadFile(weightUrl, weightPath);
    }
    
    console.log(`🎉 Model download complete for ${targetDir}`);
  } catch (error) {
    console.error(`❌ Error downloading model to ${targetDir}:`, error);
    throw error;
  }
}

async function downloadBothModels() {
  try {
    console.log('🚀 Starting model download for offline use...');
    await downloadModelFiles(detectionModelDir);
    await downloadModelFiles(segmentationModelDir);
    console.log('🎉 All models downloaded! App can now run completely offline.');
  } catch (error) {
    console.error('❌ Model download failed:', error);
    process.exit(1);
  }
}

downloadBothModels();

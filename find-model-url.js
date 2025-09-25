// Simple script to find the actual BodyPix model URL
const tf = require('@tensorflow/tfjs-node');
const bodyPix = require('@tensorflow-models/body-pix');

// Override fetch to log URLs
const originalFetch = global.fetch;
global.fetch = function(url, options) {
  console.log('🌐 Fetching:', url);
  return originalFetch(url, options);
};

async function findModelUrl() {
  try {
    console.log('🔍 Loading BodyPix model to find actual URL...');
    const model = await bodyPix.load({
      architecture: 'MobileNetV1',
      outputStride: 16,
      multiplier: 0.75,
      quantBytes: 2
    });
    console.log('✅ Model loaded successfully');
    console.log('📋 Model object:', model);
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

findModelUrl();

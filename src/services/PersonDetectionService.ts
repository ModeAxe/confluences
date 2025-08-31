import * as tf from '@tensorflow/tfjs';
import * as bodyPix from '@tensorflow-models/body-pix';

let model: bodyPix.BodyPix | null = null;
let isModelLoading = false;

// Initialize the BodyPix model
async function loadModel(): Promise<bodyPix.BodyPix | null> {
  if (model) return model;
  
  if (isModelLoading) {
    // Wait for the model to finish loading
    while (isModelLoading) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return model;
  }

  const maxRetries = 3;
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      isModelLoading = true;
      console.log(`Loading BodyPix model... (attempt ${attempt}/${maxRetries})`);
      console.log('TensorFlow.js version:', tf.version);
      console.log('BodyPix available:', !!bodyPix);
      
      // Load the model with appropriate configuration and timeout
      const modelPromise = bodyPix.load({
        architecture: 'MobileNetV1',
        outputStride: 16,
        multiplier: 0.75,
        quantBytes: 2
      });
      
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Model loading timeout after 30 seconds')), 30000);
      });
      
      const result = await Promise.race([modelPromise, timeoutPromise]);
      model = result;
      
      console.log('BodyPix model loaded successfully');
      console.log('Model object:', model);
      isModelLoading = false;
      return model;
      
         } catch (error) {
       const errorObj = error as Error;
       lastError = errorObj;
       console.error(`Error loading BodyPix model (attempt ${attempt}/${maxRetries}):`, error);
       console.error('Error details:', {
         name: errorObj.name,
         message: errorObj.message,
         stack: errorObj.stack
       });
       
       if (attempt < maxRetries) {
         console.log(`Retrying in 2 seconds...`);
         await new Promise(resolve => setTimeout(resolve, 2000));
       }
     } finally {
      isModelLoading = false;
    }
  }
  
  console.error(`Failed to load BodyPix model after ${maxRetries} attempts. Last error:`, lastError);
  return null;
}

// Detect if a person is present in the video frame
export async function detectPerson(video: HTMLVideoElement): Promise<boolean | null> {
  try {
    if (!video.videoWidth || !video.videoHeight) {
      return false;
    }

    const model = await loadModel();
    
    if (!model) {
      console.error('BodyPix model failed to load');
      return null; // Return null to indicate model loading failure
    }
    
    // Create a temporary canvas to get the video frame
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return false;

    console.log('📹 Video dimensions:', {
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      clientWidth: video.clientWidth,
      clientHeight: video.clientHeight
    });

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw the current video frame
    ctx.drawImage(video, 0, 0);
    
    // Run segmentation on the frame
    const segmentation = await model.segmentPerson(canvas, {
      flipHorizontal: false,
      internalResolution: 'medium',
      segmentationThreshold: 0.7
    });

    console.log('🔍 Segmentation result:', {
      width: segmentation.width,
      height: segmentation.height,
      dataLength: segmentation.data.length,
      allPoses: segmentation.allPoses?.length || 0
    });

    // Check if any person poses were detected (for debugging only)
    if (segmentation.allPoses && segmentation.allPoses.length > 0) {
      console.log(`Poses detected: ${segmentation.allPoses.length} - but this doesn't guarantee full body`);
    }

                // Alternative: check if there are enough person pixels AND they're distributed properly
      const personPixels = segmentation.data.filter(pixel => pixel > 0);
      const totalPixels = segmentation.data.length;
      const personRatio = personPixels.length / totalPixels;
      
      console.log(`Detection check: ${personPixels.length}/${totalPixels} pixels (${(personRatio * 100).toFixed(1)}%)`);
      
            // SIMPLIFIED: Just detect if there are enough person pixels
      // Let's start with a very basic threshold to see if detection works at all
      if (personRatio > 0.01) { // Just 1% - very lenient to test
        console.log(`✅ Person detected: ${(personRatio * 100).toFixed(1)}% > 1%`);
        
        // For now, just return true if we see any reasonable amount of person
        // We can make this more sophisticated once basic detection works
        if (personRatio > 0.05) { // 5% = probably a full body
          console.log(`✅ Likely full body: ${(personRatio * 100).toFixed(1)}% > 5%`);
          return true;
        } else {
          console.log(`⚠️ Person detected but small: ${(personRatio * 100).toFixed(1)}% (1-5%)`);
          return false;
        }
      } else {
        console.log(`❌ No person detected: ${(personRatio * 100).toFixed(1)}% < 1%`);
        return false;
      }

  } catch (error) {
    console.error('Error detecting person:', error);
    return null; // Return null for any errors
  }
}

// Clean up resources
export function cleanup() {
  if (model) {
    // TensorFlow.js models are automatically cleaned up when the page unloads
    model = null;
  }
}

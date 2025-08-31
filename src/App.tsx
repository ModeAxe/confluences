import React, { useState } from 'react';
import CameraPreview from './components/CameraPreview';
import './App.css';

function App() {
  const [capturedImage, setCapturedImage] = useState<ImageData | null>(null);

  const handleCapture = (imageData: ImageData) => {
    setCapturedImage(imageData);
    // Save the image immediately and return to camera
    saveImage(imageData);
    setCapturedImage(null);
  };

  const saveImage = (imageData: ImageData) => {
    try {
      // Create a canvas to convert ImageData to blob
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = imageData.width;
      canvas.height = imageData.height;
      ctx.putImageData(imageData, 0, 0);

      // Convert to blob and save
      canvas.toBlob((blob) => {
        if (blob) {
          const timestamp = new Date().toISOString()
            .replace(/[:.]/g, '-')
            .replace('T', '_')
            .replace('Z', '');
          
          const filename = `capture_${timestamp}.png`;
          
          // Use Electron's ipcRenderer to save the file
          if (window.require) {
            const fs = window.require('fs');
            const path = window.require('path');
            
            // Ensure output directory exists
            const outputDir = 'output/captures';
            if (!fs.existsSync(outputDir)) {
              fs.mkdirSync(outputDir, { recursive: true });
            }
            
            // Convert blob to buffer and save
            blob.arrayBuffer().then(arrayBuffer => {
              const buffer = Buffer.from(arrayBuffer);
              const filePath = path.join(outputDir, filename);
              fs.writeFileSync(filePath, buffer);
              console.log(`Image saved to: ${filePath}`);
            });
          }
        }
      }, 'image/png');
    } catch (error) {
      console.error('Error saving image:', error);
    }
  };

  return (
    <div className="App">
      <CameraPreview onCapture={handleCapture} />
    </div>
  );
}

export default App;

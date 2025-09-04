import React, { useState } from 'react';
import CameraPreview from './components/CameraPreview';
import './App.css';

function App() {
  const [capturedImage, setCapturedImage] = useState<ImageData | null>(null);

  const handleCapture = (imageData: ImageData) => {
    setCapturedImage(imageData);
    saveImageToSyncFolder(imageData);
    setCapturedImage(null);
  };

  const saveImageToSyncFolder = (imageData: ImageData) => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = imageData.width;
      canvas.height = imageData.height;
      ctx.putImageData(imageData, 0, 0);

      canvas.toBlob((blob) => {
        if (blob && window.require) {
          const fs = window.require('fs');
          const path = window.require('path');
          
          const timestamp = new Date().toISOString()
            .replace(/[:.]/g, '-')
            .replace('T', '_')
            .replace('Z', '');
          
          const filename = `capture_${timestamp}.png`;
          const syncDir = 'Confluences/captures';
          
          if (!fs.existsSync(syncDir)) {
            fs.mkdirSync(syncDir, { recursive: true });
          }
          
          blob.arrayBuffer().then(arrayBuffer => {
            const buffer = Buffer.from(arrayBuffer);
            const filePath = path.join(syncDir, filename);
            fs.writeFileSync(filePath, buffer);
            console.log(`📸 Image saved to sync folder: ${filePath}`);
          });
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

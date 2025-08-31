# Confluences - Smart Photo Capture Art Installation

An Electron + React desktop application that automatically captures photos when a person is detected using TensorFlow.js BodyPix, then saves the full photos to disk.

## Features

- **Live Webcam Preview**: Real-time camera feed with mirrored display
- **Automatic Person Detection**: Uses TensorFlow.js BodyPix to detect when a person is in frame
- **Auto-Capture**: Automatically captures photos after 3 seconds of person detection
- **Simple Photo Saving**: Saves full photos as PNG files with timestamps
- **Organized File Structure**: Automatically creates output folder and saves photos
- **Timestamp-based Naming**: Unique filenames based on capture time

## Project Structure

```
confluences/
├── main.js                 # Electron main process
├── src/
│   ├── index.html         # Main HTML template
│   ├── index.tsx          # React entry point
│   ├── App.tsx            # Main React component
│   ├── App.css            # Main styles
│   └── components/
│       └── CameraPreview.tsx      # Webcam logic & capture
├── output/                # Generated output folder
│   └── captures/          # Captured photos
├── package.json           # Dependencies & scripts
├── tsconfig.json          # TypeScript configuration
└── webpack.config.js      # Webpack bundling config
```

## Prerequisites

- Node.js 16+ 
- npm or yarn
- Webcam access permissions

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd confluences
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Install Electron dependencies**
   ```bash
   npm run install:electron
   ```

## Development

1. **Start development mode**
   ```bash
   npm run dev
   ```
   This will start both the Electron app and webpack in watch mode.

2. **Build for production**
   ```bash
   npm run build
   npm start
   ```

## Usage

1. **Launch the app**: The app will automatically request camera permissions
2. **Position yourself**: Stand in front of the camera so your full body is visible
3. **Wait for detection**: The app will show "Person Detected" when you're in frame
4. **Auto-capture**: After 2 seconds of detection, the app automatically captures a frame
5. **Processing**: Watch the segmentation progress as body parts are extracted
6. **Results**: Segmented body parts are saved to the `output/` folder

## Manual Controls

- **Capture Manually**: Click the "Capture Manually" button to take a photo immediately
- **Camera Controls**: Start/stop the camera as needed
- **Status Indicator**: Shows current detection status and timing

## Output Files

Each captured photo is saved as:
- `output/captures/capture_YYYY-MM-DD_HH-MM-SS-sssZ.png`

## Technical Details

- **TensorFlow.js**: Used for BodyPix model loading and inference
- **BodyPix Architecture**: MobileNetV1 for fast person detection
- **Canvas Processing**: HTML5 Canvas API for image capture and saving
- **File System**: Node.js fs module for disk operations
- **Simple PNG Output**: Full photos saved for artistic applications

## Performance Notes

- **Model Loading**: BodyPix model is loaded once and cached
- **Detection Speed**: MobileNetV1 optimized for real-time person detection
- **Memory Management**: Automatic cleanup of TensorFlow.js resources
- **Simple Processing**: No complex segmentation, just photo capture

## Troubleshooting

### Camera Access Issues
- Ensure camera permissions are granted
- Check if camera is being used by other applications
- Restart the app if permissions are denied

### Segmentation Errors
- Ensure good lighting conditions
- Position yourself clearly in frame
- Check console for detailed error messages

### Performance Issues
- Close other applications using GPU resources
- Ensure adequate RAM (4GB+ recommended)
- Consider reducing video resolution in CameraPreview.tsx

## Extending the App

### Adding New Body Parts
1. Modify `partGroups` in `SegmentationService.ts`
2. Add corresponding output directory logic in `FileSaverService.ts`
3. Update UI components as needed

### Custom Segmentation Models
1. Import alternative TensorFlow.js models
2. Modify segmentation logic in `SegmentationService.ts`
3. Update type definitions and interfaces

### UI Customization
- Modify CSS in `App.css` and component files
- Add new React components as needed
- Customize the processing overlay animations

## License

MIT License - see LICENSE file for details

## Contributing

This is an art installation project. For contributions or modifications, please contact the project maintainers.

---

**Confluences** - Exploring the intersection of technology and human form through digital art.

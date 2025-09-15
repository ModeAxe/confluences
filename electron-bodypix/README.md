# BodyPix Watcher

A simple Electron app that watches a folder for new images and segments them into body parts using TensorFlow.js BodyPix.

## Features

- ✅ **Real BodyPix**: Uses the actual TensorFlow.js BodyPix model
- ✅ **Folder Watching**: Monitors a directory for new images
- ✅ **Queue System**: Processes images in order, no duplicates
- ✅ **Body Part Segmentation**: Extracts 6 body part categories
- ✅ **Organized Output**: Saves parts to separate folders
- ✅ **Simple UI**: Clean, easy-to-use interface

## Body Parts Detected

- **head** - Head and face
- **left_arm** - Left arm and hand
- **right_arm** - Right arm and hand  
- **torso** - Torso (front and back)
- **left_leg** - Left leg and foot
- **right_leg** - Right leg and foot

## Installation

1. **Install dependencies**:
   ```bash
   cd electron-bodypix
   npm install
   ```

2. **Run the app**:
   ```bash
   npm start
   ```

## Usage

1. **Set directories**:
   - **Watch Directory**: Folder to monitor for new images
   - **Output Directory**: Where to save segmented body parts

2. **Click "Start Watching"**

3. **Drop images** into the watch directory

4. **Check output** - body parts will be saved to organized folders

## Output Structure

```
output/
└── bodypix_segmentation/
    ├── head/
    │   ├── head_image1.png
    │   └── head_image2.png
    ├── left_arm/
    │   ├── left_arm_image1.png
    │   └── left_arm_image2.png
    ├── right_arm/
    ├── torso/
    ├── left_leg/
    └── right_leg/
```

## Supported Image Formats

- PNG
- JPG/JPEG
- BMP
- TIFF
- WebP

## How It Works

1. **Watches** the specified folder using `chokidar`
2. **Detects** new image files
3. **Loads** BodyPix model (downloads automatically on first run)
4. **Segments** each image into body parts
5. **Saves** each body part to its respective folder
6. **Tracks** processed files to avoid duplicates

## Technical Details

- **Framework**: Electron
- **ML Model**: TensorFlow.js BodyPix
- **File Watching**: Chokidar
- **Image Processing**: TensorFlow.js
- **Queue System**: Prevents duplicate processing

## Troubleshooting

- **Model Loading**: First run may take time to download the BodyPix model
- **Memory**: Large images may require more RAM
- **Performance**: Processing speed depends on image size and system specs

## Development

```bash
# Run in development mode
npm run dev

# Build for production
npm run build
```

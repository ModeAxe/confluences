# Offline Setup

To run the app completely offline:

## 1. Download Models (Run Once When Online)

```bash
npm run download-model
```

This downloads the BodyPix model files to:
- `./models/detection/` - for frontend person detection
- `./models/segmentation/` - for background image processing

## 2. Build and Run

```bash
npm run build:dev
npm start
```

## How It Works

- **Detection Service**: Uses local model from `./models/detection/model.json`
- **Segmentation Service**: Uses local model from `./models/segmentation/model.json`
- **Fallback**: If local models don't exist, services will try to load from internet

## Model Files

Each model directory contains:
- `model.json` - Model architecture definition
- `group1-shard1of1.bin` - Model weights
- `group1-shard2of1.bin` - Additional weights
- etc.

Total size: ~4-5MB per model (8-10MB total)

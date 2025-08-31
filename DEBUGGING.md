# Debugging Guide for Confluences App

## Common Issues and Solutions

### 1. "No Person Detected" Issue

**Symptoms:**
- Camera works but always shows "No Person Detected"
- AI model status shows "Loading AI model..." indefinitely

**Possible Causes:**
- BodyPix model failed to load
- TensorFlow.js initialization issues
- Memory constraints
- Browser compatibility issues

**Solutions:**
1. **Check Console Logs:**
   - Open DevTools (Cmd+Option+I on Mac)
   - Look for errors in Console tab
   - Check for "Loading BodyPix model..." messages

2. **Verify Model Loading:**
   - The app should show "AI model ready" when loaded
   - If stuck on "Loading AI model...", there's a model loading issue

3. **Memory Issues:**
   - Close other browser tabs/applications
   - Restart the Electron app
   - Check available RAM (4GB+ recommended)

### 2. "Cannot read properties of null (reading 'segmentPersonParts')" Error

**Symptoms:**
- Manual capture fails with this error
- Segmentation processing crashes

**Cause:**
- BodyPix model is null/undefined
- Model loading failed silently

**Solutions:**
1. **Check Model Status:**
   - Look at the status indicator in the app
   - Should show "AI model ready" before capturing

2. **Restart the App:**
   - Close the app completely
   - Run `npm start` again
   - Wait for "AI model ready" status

3. **Check Dependencies:**
   - Ensure all packages are installed: `npm install`
   - Verify TensorFlow.js version compatibility

### 3. Performance Issues

**Symptoms:**
- Slow detection
- High CPU usage
- Laggy camera feed

**Solutions:**
1. **Reduce Detection Frequency:**
   - Detection loop now runs every 100ms instead of every frame
   - This reduces CPU usage significantly

2. **Lower Resolution:**
   - Modify `CameraPreview.tsx` to use lower video resolution
   - Change `width: { ideal: 1280 }` to `width: { ideal: 640 }`

3. **Use Lighter Model:**
   - PersonDetectionService uses MobileNetV1 (faster)
   - SegmentationService uses ResNet50 (higher quality)

## Debugging Steps

### Step 1: Check Console Logs
1. Start the app: `npm start`
2. Open DevTools (Cmd+Option+I)
3. Look for these messages:
   - ✅ "Loading BodyPix model..."
   - ✅ "BodyPix model loaded successfully"
   - ✅ "AI model ready"
   - ❌ Any error messages

### Step 2: Verify Model Loading
1. Wait for "AI model ready" status
2. If stuck on "Loading AI model...", check console for errors
3. Try restarting the app

### Step 3: Test Person Detection
1. Position yourself clearly in front of camera
2. Ensure good lighting
3. Wait for "Person Detected" status
4. Check if detection time increases

### Step 4: Test Manual Capture
1. Only try manual capture after "AI model ready"
2. Check console for any errors during capture
3. Verify segmentation progress

## Technical Details

### Model Loading Process
1. **PersonDetectionService**: Loads MobileNetV1 model for detection
2. **SegmentationService**: Loads ResNet50 model for detailed segmentation
3. Models are cached after first load
4. Error handling returns null instead of throwing

### Detection Loop
- Runs every 100ms (reduced from every frame)
- Checks for person presence using BodyPix
- Updates UI status indicators
- Triggers auto-capture after 2 seconds

### Error Handling
- Model loading failures are caught and logged
- UI shows appropriate status messages
- App continues to function even if detection fails

## Common Console Messages

**Success:**
```
Loading BodyPix model...
BodyPix model loaded successfully
AI model ready
Running part segmentation...
Segmentation complete, extracting parts...
Extracted X body parts
```

**Errors:**
```
Error loading BodyPix model: [error details]
BodyPix model failed to load
AI model error - check console
```

## Still Having Issues?

1. **Check Node.js version**: Ensure you have Node.js 16+
2. **Clear npm cache**: `npm cache clean --force`
3. **Reinstall dependencies**: `rm -rf node_modules && npm install`
4. **Check Electron version**: Ensure compatibility with your OS
5. **Verify camera permissions**: Camera access must be granted

## Performance Optimization

- **Detection frequency**: 100ms intervals (configurable)
- **Video resolution**: 1280x720 (can be reduced)
- **Model architecture**: MobileNetV1 for detection, ResNet50 for segmentation
- **Memory management**: Automatic cleanup of TensorFlow.js resources

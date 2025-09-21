import React, { useRef, useEffect, useState, useCallback } from 'react';
import { detectPerson } from '../services/PersonDetectionService';

interface CameraPreviewProps {
  onCapture: (imageData: ImageData) => void;
}

const CameraPreview: React.FC<CameraPreviewProps> = ({ onCapture }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number>();
  const thankYouMessageDuration = 8000;
  
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [personDetected, setPersonDetected] = useState(false);
  const [detectionTime, setDetectionTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [modelStatus, setModelStatus] = useState('Loading AI model...');
  const [isModelReady, setIsModelReady] = useState(false);
  const [captureMessage, setCaptureMessage] = useState('');
  const [showThankYouMessage, setShowThankYouMessage] = useState(false);
  
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      console.log('Available cameras:', videoDevices);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 720 },
          height: { ideal: 1280 },
            deviceId: { exact: videoDevices[0].deviceId }
        }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsCameraActive(true);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Unable to access camera. Please check permissions.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  }, []);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || isProcessing) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the current video frame to canvas
    canvas.style.transform = 'scaleX(-1)'; // Mirror the canvas like the video

    // Draw the current video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Get image data for processing
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    setIsProcessing(true);
    setCaptureMessage('Photo captured! Saving...');
    
    // Call the capture handler
    onCapture(imageData);
    
    // Flash duration (2 seconds)
    setTimeout(() => {
      setIsProcessing(false); // End flash, show thank you message
      setShowThankYouMessage(true);
      setCaptureMessage('');
    }, 2000);
    
    // Thank you message duration (after flash)
    setTimeout(() => {
      setShowThankYouMessage(false);
      setPersonDetected(false); // Reset detection state
      setDetectionTime(0); // Reset countdown
    }, thankYouMessageDuration);
  }, [onCapture, isProcessing]);

      // Separate detection and countdown logic
    useEffect(() => {
      if (!isCameraActive || !videoRef.current || isProcessing || showThankYouMessage) return;

    const detectLoop = async () => {
      if (!videoRef.current || showThankYouMessage) return;

      try {
        const detected = await detectPerson(videoRef.current);
        
        if (detected === null) {
          setModelStatus('AI model failed to load');
          setIsModelReady(false);
          setPersonDetected(false);
          return;
        }
        
        setModelStatus('AI model ready');
        setIsModelReady(true);
        
        // Only update person detection state, don't touch countdown here
        setPersonDetected(detected);
        
      } catch (error) {
        console.error('Detection error:', error);
        setModelStatus('AI model error - check console');
        setIsModelReady(false);
      }

      // Run detection every 500ms
      setTimeout(() => {
        animationFrameRef.current = requestAnimationFrame(detectLoop);
      }, 500);
    };

    detectLoop();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isCameraActive, showThankYouMessage]);

  // Separate countdown effect
  useEffect(() => {
    if (!personDetected || isProcessing || showThankYouMessage) {
      // Clear countdown if no person, processing, or showing thank you message
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
        countdownIntervalRef.current = null;
      }
      setDetectionTime(0);
      return;
    }

    // Start countdown when person detected
    console.log('Starting 5-second countdown...');
    setDetectionTime(0);
    
    countdownIntervalRef.current = setInterval(() => {
      setDetectionTime(prev => {
        const newTime = prev + 1;
        console.log(`Countdown: ${newTime}/5 seconds`);
        
        if (newTime >= 5) {
          console.log('5 seconds reached - capturing!');
          captureFrame();
          return 0;
        }
        
        return newTime;
      });
    }, 1000);

    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    };
  }, [personDetected, isProcessing, captureFrame]);

  // Start camera on mount
  useEffect(() => {
    startCamera();

    return () => {
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  const handleManualCapture = () => {
    if (!isProcessing) {
      captureFrame();
    }
  };

  return (
    <>
      {/* Thank you message overlay - outside camera container for full screen coverage */}
      {showThankYouMessage && (
        <div className="thank-you-message">
          <div className="thank-you-text">
            Presence Captured.<br />
            Thank you for your contribution.
          </div>
        </div>
      )}
      
      <div className="camera-container">
        <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="video-preview"
        // Removed mirroring - might interfere with detection
        onLoadedMetadata={() => {
          if (videoRef.current) {
            console.log('🎥 Video metadata loaded:', {
              videoWidth: videoRef.current.videoWidth,
              videoHeight: videoRef.current.videoHeight,
              clientWidth: videoRef.current.clientWidth,
              clientHeight: videoRef.current.clientHeight
            });
          }
        }}
              />
        
        {/* White flash overlay on capture */}
        {isProcessing && <div className="capture-flash" />}
        
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      
      <div className="status-indicator">
        <div className={`person-status ${personDetected ? 'person-detected' : 'no-person'}`}>
          {personDetected 
            ? `Full Body Detected (${detectionTime}/5s)` 
            : 'No Full Body Detected'
          }
        </div>
        <div className="detection-debug">
          Detection: {personDetected ? '✅ Full Body' : '❌ Partial/None'}
        </div>
        <div className="model-status">
          {modelStatus}
        </div>
        {personDetected && detectionTime > 0 && detectionTime < 5 && (
          <div className="countdown-message">
            <div className="countdown-text">
              Capturing in {5 - detectionTime} seconds...
            </div>
            <div className="countdown-progress">
              <div 
                className="countdown-progress-fill" 
                style={{ width: `${(detectionTime / 5) * 100}%` }}
              />
            </div>
          </div>
        )}
        {captureMessage && (
          <div className="capture-message">
            {captureMessage}
          </div>
        )}
      </div>

      <div className="controls">
        <button 
          onClick={handleManualCapture}
          disabled={isProcessing || !isCameraActive || !isModelReady}
        >
          {isProcessing ? 'Processing...' : 'Capture Manually'}
        </button>
        
        <button 
          onClick={isCameraActive ? stopCamera : startCamera}
        >
          {isCameraActive ? 'Stop Camera' : 'Start Camera'}
        </button>
        
        {modelStatus.includes('failed') && (
          <button 
            onClick={() => window.location.reload()}
            className="reload-button"
          >
            Reload App
          </button>
        )}
      </div>
    </div>
    </>
  );
};

export default CameraPreview;

"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Image as ImageIcon, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

interface ImageUploadProps {
  onImageUpload: (file: File, preview: string) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export function ImageUpload({
  onImageUpload,
  onAnalyze,
  isAnalyzing,
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [showCamera, setShowCamera] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          setPreview(result);
          setFileName(file.name);
          onImageUpload(file, result);
        };
        reader.readAsDataURL(file);
      }
    },
    [onImageUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
    },
    maxFiles: 1,
    multiple: false,
  });

  const clearImage = () => {
    setPreview(null);
    setFileName("");
  };

  const onCaptureChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        setPreview(result);
        setFileName(file.name);
        onImageUpload(file, result);
      };
      reader.readAsDataURL(file);
      e.target.value = "";
    }
  };

  const stopCamera = () => {
    const v = videoRef.current;
    const stream = v && (v as any).srcObject;
    if (stream && stream.getTracks) {
      stream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
    }
    if (v) {
      (v as any).srcObject = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    if (!showCamera) {
      stopCamera();
      return;
    }
    let mounted = true;
    const start = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          cameraInputRef.current?.click();
          setShowCamera(false);
          return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        });
        if (!mounted) return;
        if (videoRef.current) {
          (videoRef.current as any).srcObject = stream;
          await videoRef.current.play();
          setCameraActive(true);
        }
      } catch {
        cameraInputRef.current?.click();
        setShowCamera(false);
      }
    };
    start();
    return () => {
      mounted = false;
      stopCamera();
    };
  }, [showCamera]);

  const capturePhoto = () => {
    const v = videoRef.current;
    if (!v || !cameraActive) return;
    const w = v.videoWidth || 640;
    const h = v.videoHeight || 480;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, w, h);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], `capture-${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          setPreview(result);
          setFileName(file.name);
          onImageUpload(file, result);
          setShowCamera(false);
          stopCamera();
        };
        reader.readAsDataURL(file);
      },
      "image/jpeg",
      0.95
    );
  };

  const openCamera = () => {
    if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function") {
      setShowCamera(true);
    } else {
      cameraInputRef.current?.click();
    }
  };

  return (
    <section id="upload" className="py-20 bg-muted/30">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Upload Your Image
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload a dermoscopic skin image for analysis. Our AI model will
            classify it into one of seven categories.
          </p>
        </div>

        <Card className="border-2 border-dashed border-border hover:border-primary/50 transition-colors">
          <CardContent className="p-0">
            {!preview ? (
              <div
                {...getRootProps()}
                className={`p-12 cursor-pointer transition-all ${
                  isDragActive ? "bg-primary/5" : "bg-transparent"
                }`}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center justify-center text-center">
                  <div
                    className={`w-20 h-20 rounded-2xl flex items-center justify-center mb-6 transition-all ${
                      isDragActive
                        ? "bg-primary text-primary-foreground scale-110"
                        : "bg-primary/10 text-primary"
                    }`}
                  >
                    <Upload className="w-10 h-10" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {isDragActive
                      ? "Drop your image here"
                      : "Drag & drop your image"}
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    or click to browse from your computer
                  </p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <ImageIcon className="w-4 h-4" />
                    <span>Supported formats: JPG, PNG</span>
                  </div>
                  <div className="mt-6">
                    <input
                      ref={cameraInputRef}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                      onChange={onCaptureChange}
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={(e) => {
                        e.stopPropagation();
                        openCamera();
                      }}
                    >
                      Take Photo
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6">
                <div className="relative">
                  <div className="aspect-video relative rounded-xl overflow-hidden bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={preview}
                      alt="Uploaded dermoscopic image"
                      className="w-full h-full object-contain"
                    />

                    {/* High-tech scanning overlay */}
                    {isAnalyzing && (
                      <div className="absolute inset-0 pointer-events-none">
                        {/* subtle grid */}
                        <div className="absolute inset-0 opacity-40 mix-blend-overlay [background-image:linear-gradient(to_right,rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:24px_24px]" />
                        {/* vignette */}
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/10 to-background/40" />
                        {/* rotating ring */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="h-44 w-44 rounded-full border border-primary/30 shadow-[0_0_40px_rgba(59,130,246,0.25)] animate-spin [animation-duration:3s]" />
                          <div className="absolute h-28 w-28 rounded-full border border-accent/40 animate-spin [animation-duration:1.8s] [animation-direction:reverse]" />
                        </div>
                        {/* scanning laser line */}
                        <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent blur-[0.5px] animate-[scan_1.6s_ease-in-out_infinite]" />
                        {/* glow */}
                        <div className="absolute inset-0 shadow-[inset_0_0_0_1px_rgba(59,130,246,0.25)]" />
                        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs text-primary-foreground/90">
                          <span className="px-2 py-1 rounded-md bg-primary/60 backdrop-blur-md border border-primary/30">
                            Analyzing Skin Lesion with AI...
                          </span>
                          <span className="px-2 py-1 rounded-md bg-foreground/40 backdrop-blur-md border border-border/40 text-background">
                            Neural scan
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={clearImage}
                    className="absolute top-3 right-3 p-2 rounded-full bg-foreground/80 text-background hover:bg-foreground transition-colors"
                    aria-label="Remove image"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <ImageIcon className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate max-w-[150px] sm:max-w-[200px]">
                        {fileName}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Ready for analysis
                      </p>
                    </div>
                  </div>
                  <Button onClick={onAnalyze} disabled={isAnalyzing} className="w-full sm:w-auto">
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      "Analyze Image"
                    )}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={showCamera} onOpenChange={setShowCamera}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Capture Photo</DialogTitle>
          </DialogHeader>
          <div className="w-full">
            <div className="relative w-full overflow-hidden rounded-md bg-black">
              <video
                ref={videoRef}
                className="w-full h-full"
                playsInline
                muted
                autoPlay
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setShowCamera(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={capturePhoto} disabled={!cameraActive}>
              Capture
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}

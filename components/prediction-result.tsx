"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, Info } from "lucide-react";

export interface PredictionData {
  predictedClass: string;
  confidence: number;
  probabilities: {
    class: string;
    label: string;
    probability: number;
    description: string;
  }[];
  gradcam: null | {
    overlayDataUrl: string;
    heatmapDataUrl: string;
  };
  originalImageB64?: string;
  gradcamHeatmapB64?: string | null;
}

interface PredictionResultProps {
  prediction: PredictionData | null;
  imagePreview: string | null;
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return "bg-green-500";
  if (confidence >= 0.5) return "bg-yellow-500";
  return "bg-red-500";
};

const getConfidenceLabel = (confidence: number) => {
  if (confidence >= 0.8) return { label: "High Confidence", icon: CheckCircle2 };
  if (confidence >= 0.5) return { label: "Medium Confidence", icon: Info };
  return { label: "Low Confidence", icon: AlertTriangle };
};

export function PredictionResult({
  prediction,
  imagePreview,
}: PredictionResultProps) {
  if (!prediction) return null;

  const isUnknown = (prediction.predictedClass || "").toLowerCase() === "unknown";
  const confidenceInfo = isUnknown
    ? { label: "Not Applicable", icon: Info }
    : getConfidenceLabel(prediction.confidence);
  const ConfidenceIcon = confidenceInfo.icon;

  return (
    <section className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Analysis Results
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            AI-powered classification and visualization of your dermoscopic image
          </p>
        </div>

        {/* Main Result Row: Original, GradCAM, and Summary */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* 1. Original Image */}
          <Card className="overflow-hidden border border-border/50 shadow-sm">
            <CardHeader className="p-3 border-b bg-muted/30">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-center">
                1. Original Image
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="aspect-square relative group">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={prediction.originalImageB64 ? `data:image/png;base64,${prediction.originalImageB64}` : (imagePreview || "")}
                  alt="Original dermoscopic image"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
            </CardContent>
          </Card>

          {/* 2. GradCAM Heatmap */}
          <Card className="overflow-hidden border border-border/50 shadow-sm">
            <CardHeader className="p-3 border-b bg-muted/30">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-center">
                2. GradCAM Heatmap
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="aspect-square relative group">
                {prediction.gradcamHeatmapB64 ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={`data:image/png;base64,${prediction.gradcamHeatmapB64}`}
                    alt="GradCAM attention map"
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-[10px] text-muted-foreground p-4 text-center">
                    GradCAM unavailable
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 3. Classification Summary */}
          <Card className="flex flex-col border border-border/50 shadow-sm">
            <CardHeader className="p-3 border-b bg-muted/30">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-center">
                3. Classification Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 flex-1 flex flex-col justify-center space-y-6">
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-medium text-muted-foreground uppercase">
                    Prediction
                  </span>
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1 text-[10px] px-1.5 py-0"
                  >
                    <ConfidenceIcon className="w-2.5 h-2.5" />
                    {confidenceInfo.label}
                  </Badge>
                </div>
                <p className="text-2xl font-black text-foreground uppercase tracking-tight leading-none">
                  {prediction.predictedClass}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold text-foreground uppercase tracking-wider">
                    Confidence
                  </span>
                  <span className="text-xs font-black text-foreground tabular-nums">
                    {isUnknown ? "N/A" : `${(prediction.confidence * 100).toFixed(1)}%`}
                  </span>
                </div>
                {!isUnknown && (
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ease-out ${getConfidenceColor(
                        prediction.confidence
                      )}`}
                      style={{ width: `${prediction.confidence * 100}%` }}
                    />
                  </div>
                )}
              </div>
              
              <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3 text-center">
                {
                  prediction.probabilities.find(
                    (p) => p.class === prediction.predictedClass
                  )?.description
                }
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Probability Distribution */}
          <Card className="border border-border/50 shadow-sm">
            <CardHeader className="p-4 border-b bg-muted/30">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Class Probability Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                {prediction.probabilities
                  .sort((a, b) => b.probability - a.probability)
                  .map((item, index) => (
                    <div key={item.class} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold ${
                              index === 0
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {index + 1}
                          </span>
                          <div>
                            <p className="font-bold text-foreground uppercase text-xs tracking-wider">
                              {item.class}
                            </p>
                            <p className="text-[10px] text-muted-foreground">
                              {item.label}
                            </p>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-foreground tabular-nums">
                          {(item.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-muted overflow-hidden ml-10">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            index === 0 ? "bg-primary" : "bg-muted-foreground/30"
                          }`}
                          style={{
                            width: `${item.probability * 100}%`,
                            transitionDelay: `${index * 100}ms`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

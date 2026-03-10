"use client";

import { useState, useCallback } from "react";
import { Navbar } from "@/components/navbar";
import { HeroSection } from "@/components/hero-section";
import { ImageUpload } from "@/components/image-upload";
import { PredictionResult, type PredictionData } from "@/components/prediction-result";
import { ModelExplanation } from "@/components/model-explanation";
import { ResearchSection } from "@/components/research-section";
import { Footer } from "@/components/footer";

const CLASS_META: Record<
  string,
  { label: string; description: string }
> = {
  akiec: {
    label: "Actinic Keratoses",
    description:
      "Actinic keratoses (solar keratoses) and intraepithelial carcinoma (Bowen's disease).",
  },
  bcc: {
    label: "Basal Cell Carcinoma",
    description:
      "A common type of skin cancer that begins in the basal cells.",
  },
  bkl: {
    label: "Benign Keratosis",
    description:
      "Seborrheic keratoses, solar lentigo, and lichen planus-like keratoses.",
  },
  df: {
    label: "Dermatofibroma",
    description:
      "A common benign skin growth, usually appearing on the legs.",
  },
  mel: {
    label: "Melanoma",
    description:
      "The most serious type of skin cancer, developing in melanocytes.",
  },
  nv: {
    label: "Melanocytic Nevi",
    description:
      "Common benign skin lesions (moles) caused by melanocyte proliferation.",
  },
  vasc: {
    label: "Vascular Lesions",
    description:
      "Angiomas, angiokeratomas, pyogenic granulomas and hemorrhage.",
  },
};

type PredictApiResponse = {
  prediction: string;
  confidence: number;
  probabilities?: Record<string, number>;
  original_image: string;
  gradcam_heatmap: string | null;
  cam_pred_index?: number | null;
};

export interface MappedPredictionData extends PredictionData {
  originalImageB64?: string;
  gradcamHeatmapB64?: string | null;
}

export default function Home() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [prediction, setPrediction] = useState<MappedPredictionData | null>(null);

  const handleImageUpload = useCallback((_file: File, preview: string) => {
    setImagePreview(preview);
    setImageFile(_file);
    setPrediction(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!imageFile) return;
    setIsAnalyzing(true);
    try {
      const form = new FormData();
      form.set("file", imageFile, imageFile.name);

      const res = await fetch("/api/predict", {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || err?.error || "Prediction failed");
      }
      const data = (await res.json()) as PredictApiResponse;

      const probs = data.probabilities ?? {};
      let probArray = Object.entries(probs).map(([cls, p]) => ({
        class: cls,
        label: CLASS_META[cls]?.label ?? cls,
        description: CLASS_META[cls]?.description ?? "",
        probability: p,
      }));

      let predictedClass = data.prediction;
      let confidence = data.confidence;

      if (data.cam_pred_index === 8) {
        predictedClass = "Unknown";
        confidence = 0;
        probArray = [
          {
            class: "Unknown",
            label: "Unknown",
            description: "",
            probability: 1,
          },
        ];
      }

      const mapped: MappedPredictionData = {
        predictedClass,
        confidence,
        probabilities: probArray,
        gradcam: null,
        originalImageB64: data.original_image,
        gradcamHeatmapB64: data.gradcam_heatmap,
      };
      setPrediction(mapped);
    } catch (e: unknown) {
      console.error(e);
      setPrediction(null);
      alert(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setIsAnalyzing(false);
    }
  }, [imageFile]);

  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <ImageUpload
        onImageUpload={handleImageUpload}
        onAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
      />
      {prediction && (
        <PredictionResult prediction={prediction} imagePreview={imagePreview} />
      )}
      <ModelExplanation />
      <ResearchSection />
      <Footer />
    </main>
  );
}

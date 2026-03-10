"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
  Brain,
  Layers,
  Focus,
  Sparkles,
  ArrowRight,
  Target,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Deep Metric Learning",
    description:
      "Learns discriminative representations by comparing skin lesions in a learned embedding space.",
  },
  {
    icon: Target,
    title: "Focal Loss Optimization",
    description:
      "Uses focal loss to handle class imbalance by focusing the model on hard-to-classify skin lesions, improving detection of rare cancer types.",
  },
  {
    icon: Layers,
    title: "Relational Learning",
    description:
      "Captures relationships between different lesion types for improved classification accuracy.",
  },
  {
    icon: Focus,
    title: "Lesion-Aware Learning",
    description:
      "Focuses attention on clinically relevant features within dermoscopic images.",
  },
  {
    icon: Sparkles,
    title: "Attention Drift Regularization",
    description:
      "Prevents model attention from drifting away from important diagnostic regions.",
  },
];

const classInfo = [
  { code: "akiec", name: "Actinic Keratoses / Bowen's Disease", color: "bg-chart-1" },
  { code: "bcc", name: "Basal Cell Carcinoma", color: "bg-chart-2" },
  { code: "bkl", name: "Benign Keratosis", color: "bg-chart-3" },
  { code: "df", name: "Dermatofibroma", color: "bg-chart-4" },
  { code: "mel", name: "Melanoma", color: "bg-chart-5" },
  { code: "nv", name: "Melanocytic Nevi", color: "bg-chart-6" },
  { code: "vasc", name: "Vascular Lesions", color: "bg-chart-7" },
];

export function ModelExplanation() {
  return (
    <section id="about" className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Brain className="w-4 h-4" />
            <span>Model Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Advanced DeepVision
          </h2>
          <p className="mt-6 text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            This system uses a deep metric learning framework that integrates
            relational learning, lesion-aware learning, and attention drift
            regularization to analyze dermoscopic skin images.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
            >
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  <feature.icon className="w-6 h-6 text-primary group-hover:text-primary-foreground" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Classification Classes */}
        <Card>
          <CardContent className="p-8">
            <div className="flex items-center gap-2 mb-6">
              <ArrowRight className="w-5 h-5 text-primary" />
              <h3 className="text-xl font-semibold text-foreground">
                Supported Classifications
              </h3>
            </div>
            <p className="text-muted-foreground mb-6">
              Our model can classify dermoscopic images into the following 7
              categories:
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {classInfo.map((item) => (
                <div
                  key={item.code}
                  className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className={`w-3 h-3 rounded-full ${item.color}`} />
                  <div>
                    <p className="font-mono text-sm font-bold text-foreground uppercase">
                      {item.code}
                    </p>
                    <p className="text-xs text-muted-foreground">{item.name}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { FileText, Database, Award, Users } from "lucide-react";

const stats = [
  { icon: Database, value: "10,015", label: "Training Images" },
  { icon: Award, value: "95%", label: "Accuracy" },
  { icon: FileText, value: "7", label: "Skin Lesion Classes" },
  { icon: Users, value: "HAM10000", label: "Dataset" },
];

export function ResearchSection() {
  return (
    <section id="research" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Research & Performance
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Our model has been trained and validated on the HAM10000 dataset, a
            large collection of dermatoscopic images.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {stats.map((stat) => (
            <Card key={stat.label} className="text-center">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <stat.icon className="w-6 h-6 text-primary" />
                </div>
                <p className="text-3xl font-bold text-foreground">
                  {stat.value}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {stat.label}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Research Info */}
        <div className="grid lg:grid-cols-2 gap-8">
          <Card>
            <CardContent className="p-8">
              <h3 className="text-xl font-semibold text-foreground mb-4">
                Dataset Information
              </h3>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  The HAM10000 dataset is a large collection of multi-source
                  dermatoscopic images of common pigmented skin lesions. It
                  includes over 10,000 training images from different
                  populations.
                </p>
                <p>
                  Images were acquired using a variety of dermatoscopes and
                  represent the clinical diversity encountered in practice.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-8">
              <h3 className="text-xl font-semibold text-foreground mb-4">
                Model Architecture
              </h3>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  Our DeepVision model employs a novel deep metric learning
                  approach with three key innovations: relational learning,
                  lesion-aware attention, and drift regularization.
                </p>
                <p>
                  The architecture is based on modern convolutional neural
                  networks optimized for dermoscopic image analysis.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import { Scan, Github, Mail, FileText } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-foreground text-background py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
                <Scan className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-semibold">DeepVision</span>
            </Link>
            <p className="text-background/70 text-sm leading-relaxed">
              Advanced AI-powered skin cancer detection using deep metric
              learning for accurate dermoscopic image analysis.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              {["Home", "Upload", "About Model", "Research"].map((item) => (
                <li key={item}>
                  <Link
                    href={`#${item.toLowerCase().replace(" ", "-")}`}
                    className="text-sm text-background/70 hover:text-background transition-colors"
                  >
                    {item}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="#"
                  className="text-sm text-background/70 hover:text-background transition-colors flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  href="#"
                  className="text-sm text-background/70 hover:text-background transition-colors flex items-center gap-2"
                >
                  <Github className="w-4 h-4" />
                  GitHub Repository
                </Link>
              </li>
              <li>
                <Link
                  href="#"
                  className="text-sm text-background/70 hover:text-background transition-colors flex items-center gap-2"
                >
                  <Mail className="w-4 h-4" />
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Disclaimer */}
          <div>
            <h4 className="font-semibold mb-4">Disclaimer</h4>
            <p className="text-sm text-background/70 leading-relaxed">
              This is a research project for educational purposes. It is not
              intended for clinical diagnosis. Always consult a qualified
              healthcare professional.
            </p>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-background/20">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-background/50">
              © {new Date().getFullYear()} DeepVision Research Project. All
              rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link
                href="#"
                className="text-sm text-background/50 hover:text-background transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                href="#"
                className="text-sm text-background/50 hover:text-background transition-colors"
              >
                Terms of Use
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

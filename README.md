# PlantDoctorAI1
An end-to-end Precision Agriculture &amp; SaaS platform for crop disease diagnosis using PyTorch ResNet-50, Grad-CAM (XAI), Leaflet GIS mapping, live IoT/weather telemetry, and Dr. Flora AI assistant.
# 🌱 PlantDoctorAI — Precision Agriculture & Crop Diagnostics

PlantDoctorAI is a full-stack, SaaS-ready Precision Agriculture decision-support system designed to identify, visualize, and track crop diseases from leaf imagery.

## 🚀 Key Features

- **Deep Learning Inference:** Automated classification across 38 crop disease classes powered by a fine-tuned PyTorch ResNet-50 architecture.
- **Explainable AI (XAI):** Real-time symptom localization and lesion saliency maps utilizing Grad-CAM (layer4 feature activations).
- **Taxonomic Cross-Validation:** Verification of botanical species using the Pl@ntNet API.
- **GIS Outbreak Mapping:** Interactive epidemiological outbreak tracking powered by Leaflet.js and Esri World Gray basemaps.
- **Live Environmental Telemetry:** In-situ GPS fetching coupled with the Open-Meteo REST API for live temperature, humidity, and microclimate risk calculation.
- **Dr. Flora AI Agronomist:** A context-aware agricultural advisory assistant integrated directly with local disease treatment protocols and agronomic guidelines.
- **Official Prescription Export:** One-click automated PDF generation for official diagnostic reports and chemical/biological prescriptions.

## 🛠 Tech Stack

- **Backend:** Python, Flask, SQLite3, PyTorch, Torchvision, OpenCV
- **Frontend:** Responsive Vanilla HTML5/CSS3, JavaScript, Leaflet.js, Html2pdf.js
- **External Services:** Open-Meteo API, Pl@ntNet API, Esri ArcGIS

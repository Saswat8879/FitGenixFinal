# FitGenixFinal
Deployment repo for fitgenix
#Overview
FitGenix combines:
> A modern web app for user onboarding, tracking, and coaching experience
> A FastAPI backend for authentication, plan generation, and API orchestration
> A multi-model ML layer for risk scoring, personalization, exercise ranking, nutrition planning, and stress detection
> The project is organized as a single monorepo and is designed for CPU-friendly deployment.

# Key Capabilities
> Personalized onboarding and profile-driven coaching
> Diabetes risk estimation with surrogate support when lab values are missing
> User embedding and clustering for behavior-based personalization
> Exercise recommendation and ranking
> Diet and meal planning under health constraints
> Stress signal detection from behavior and physiological proxies
> RAG-style wellness chat assistant with context retrieval
> Daily/periodic plan adaptation via background scheduler
# Architecture
> Frontend: Next.js application
> Backend: FastAPI application with SQLAlchemy and background jobs
> ML: Training, preprocessing, inference, and saved artifacts
# High-level flow:
> User data and activity signals enter the backend
> Backend runs orchestration and model inference
> Personalization engine composes recommendations
> Frontend renders plans, progress, and assistant interactions
# Tech Stack
__Frontend__
> Next.js 14
> React 18
> TypeScript
> Tailwind CSS
> Framer Motion
> React Query
> Zustand
> React Hook Form + Zod
> Recharts
__Backend__
> FastAPI
> Uvicorn
> SQLAlchemy
> Pydantic Settings
> APScheduler
> JWT auth and encryption support
> Google API integrations
__ML and AI__
> scikit-learn
> XGBoost
> PyTorch
sentence-transformers
FAISS (CPU)
NumPy, Pandas
Gemini API integration for assistant generation

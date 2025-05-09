# MatchWise Frontend

The frontend application for the MatchWise football prediction system, built with React, TypeScript, and Tailwind CSS.

## Overview

This modern frontend provides:

- Interactive dashboards for football data analysis
- Match predictions and historical results
- Team and player statistics
- Administrative interfaces for data management
- Responsive design for desktop and mobile

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- Vite (for fast development)
- React Router (for routing)
- Axios (for API communication)

## Directory Structure

```
frontend/
├── public/              # Static assets
├── src/                 # Source code
│   ├── api/             # API client and services
│   ├── assets/          # Images, icons, etc.
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── types/           # TypeScript type definitions
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Application entry point
├── index.html           # HTML template
└── package.json         # Dependencies and scripts
```

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

3. Build for production:

```bash
npm run build
```

## Backend Integration

The frontend communicates with the FastAPI backend through:

- The API client in `src/api/client.ts`
- Type definitions in `src/types/api.ts` that mirror backend schemas

All backend endpoints are available at `/api/v1/*` with the following key endpoints:

- `/api/v1/fixtures` - Match fixtures and results
- `/api/v1/teams` - Team information
- `/api/v1/players` - Player statistics
- `/api/v1/predictions` - Match predictions
- `/api/v1/ingestion` - Data ingestion status and control

## Features

### Admin Dashboard

Administrative interface for managing users, data, and system settings

### Match Predictions

View predicted match outcomes based on machine learning models

### Team Analysis

Detailed team statistics and performance metrics

### Fixture Results

View match results and historical data

## Development

### Recommended Setup

- VS Code with the following extensions:
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense

### Style Guide

- Follow ESLint configuration for code style
- Use functional components with hooks
- Create reusable components in the components directory
- Add types for all props and state

### Commands

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build
- `npm run test` - Run tests

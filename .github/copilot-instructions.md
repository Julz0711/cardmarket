# CardMarket Project

You are working on a full-stack trading card management application with the following structure:

## Project Overview

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS v4
- **Backend**: Python Flask with REST API
- **Purpose**: Manage and track trading card collections with CardMarket data

## Architecture

- Frontend runs on http://localhost:5173 (Vite dev server)
- Backend runs on http://localhost:5000 (Flask server)
- API communication via custom TypeScript client

## Key Components

- `src/App.tsx`: Main React application
- `src/components/CardTable.tsx`: Interactive card table with sorting/filtering
- `src/components/StatsDashboard.tsx`: Collection statistics display
- `src/api/client.ts`: TypeScript API client for backend communication
- `backend/app.py`: Flask REST API with CORS support

## Data Model

Cards have the following structure:

```typescript
interface Card {
  id?: number;
  tcg: string;
  expansion: string;
  number: number;
  name: string;
  rarity: string;
  supply: number;
  current_price: number;
  price_bought: number;
  psa: string;
}
```

## Development Guidelines

- Use TypeScript strict mode
- Follow React functional component patterns
- Use Tailwind CSS v4 (no config file needed)
- Implement proper error handling
- Maintain responsive design
- Keep API endpoints RESTful

## Coding Standards

- Use async/await for API calls
- Implement proper loading states
- Add comprehensive error handling
- Use semantic HTML elements
- Follow accessibility best practices
- Add meaningful TypeScript types

## Current Status

- Frontend: Complete with all components implemented
- Backend: Complete Flask API with CRUD operations
- Integration: TypeScript API client connecting frontend to backend
- Styling: Tailwind CSS v4 with modern, responsive design

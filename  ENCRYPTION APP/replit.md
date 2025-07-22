# Script Generator Application

## Overview

This is a full-stack web application that generates Python scripts for file encryption and decryption. The application allows users to configure target locations, backup settings, and passwords through a web interface, then generates downloadable Python scripts that can be executed locally on their systems.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript
- **Build Tool**: Vite for development and production builds
- **UI Library**: shadcn/ui components built on Radix UI primitives
- **Styling**: Tailwind CSS with CSS variables for theming
- **State Management**: TanStack Query for server state, React hooks for local state
- **Routing**: Wouter for client-side routing
- **Form Handling**: React Hook Form with Zod validation

### Backend Architecture
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js
- **Database ORM**: Drizzle ORM configured for PostgreSQL
- **Database Provider**: Neon Database (serverless PostgreSQL)
- **Session Management**: PostgreSQL-based sessions using connect-pg-simple
- **Build System**: esbuild for production bundling

### Data Storage Solutions
- **Primary Database**: PostgreSQL via Neon Database serverless
- **Schema Management**: Drizzle ORM with migrations
- **In-Memory Storage**: Fallback MemStorage class for development/testing
- **Session Storage**: PostgreSQL-based session store

## Key Components

### Frontend Components
- **Home Page**: Main interface for configuring script generation parameters
- **UI Components**: Complete shadcn/ui component library including forms, dialogs, alerts, and navigation
- **Custom Hooks**: Mobile detection, toast notifications
- **Form Validation**: Zod schemas for type-safe form validation

### Backend Components
- **Route Handlers**: Express routes for script generation and download
- **Storage Layer**: Abstracted storage interface with memory and database implementations
- **Script Generators**: Functions that create Python encryption/decryption scripts based on user configuration
- **Development Server**: Vite integration for hot module replacement in development

### Database Schema
- **Script Configurations Table**: Stores user configurations including:
  - Password (for encryption key generation)
  - Target location (directory to encrypt)
  - Backup location (where to store backups)
  - Custom backup path (optional custom location)

## Data Flow

1. **User Configuration**: User fills out form with encryption parameters
2. **Form Validation**: Client-side validation using Zod schemas
3. **Script Generation**: POST request to `/api/scripts/encrypt` or `/api/scripts/decrypt`
4. **Dynamic Script Creation**: Server generates Python scripts based on configuration
5. **File Download**: Scripts are served as downloadable Python files
6. **Local Execution**: Users run downloaded scripts on their local systems

## External Dependencies

### Frontend Dependencies
- **React Ecosystem**: React, React DOM, React Hook Form
- **UI Framework**: Radix UI components, Lucide React icons
- **Styling**: Tailwind CSS, class-variance-authority for component variants
- **State Management**: TanStack Query for server state
- **Validation**: Zod for schema validation
- **Utilities**: date-fns, clsx for conditional classes

### Backend Dependencies
- **Core**: Express.js, TypeScript, tsx for development
- **Database**: Drizzle ORM, @neondatabase/serverless
- **Session Management**: express-session, connect-pg-simple
- **Validation**: Zod, drizzle-zod for database schema validation
- **Security**: PBKDF2 key derivation in generated scripts

### Development Tools
- **Build Tools**: Vite, esbuild, TypeScript compiler
- **Database Tools**: Drizzle Kit for migrations and schema management
- **Replit Integration**: Custom plugins for development environment

## Deployment Strategy

### Development Environment
- **Development Server**: Vite dev server with Express backend
- **Hot Reload**: Vite HMR for frontend, tsx for backend auto-restart
- **Database**: Neon Database with environment-based connection string

### Production Build
- **Frontend Build**: Vite builds React app to `dist/public`
- **Backend Build**: esbuild bundles Express server to `dist/index.js`
- **Static Serving**: Express serves built frontend assets
- **Database Migrations**: Drizzle Kit manages schema changes

### Environment Configuration
- **Database URL**: Required environment variable for PostgreSQL connection
- **Build Scripts**: Separate scripts for development, build, and production
- **Type Checking**: TypeScript compilation verification

### Security Considerations
- **Password Handling**: Passwords are used only for script generation, not stored permanently
- **Script Security**: Generated scripts use PBKDF2 for key derivation with salt
- **Environment Variables**: Database credentials managed through environment variables
- **CORS**: Express configured for development and production environments

The application architecture supports both development flexibility and production deployment, with clear separation between frontend UI, backend API, and data persistence layers.
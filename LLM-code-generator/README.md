# LLM Code Generator

A production-ready **LLM-powered Code Generation Platform** built using **FastAPI**, designed with secure authentication, role-based access control, persistent chat storage, and Dockerized deployment. This project demonstrates real-world backend engineering practices suitable for enterprise-grade applications.

---

## Overview

The LLM Code Generator allows authenticated users to submit prompts and receive generated code from a Large Language Model workflow. The system securely manages users, stores prompt-response history, and provides administrators with visibility into platform usage through dedicated APIs.

This project emphasizes **scalability**, **security**, and **clean backend architecture**, making it suitable for SaaS-style deployments.

---

## Key Features

- LLM-based code generation using a modular workflow engine
- FastAPI backend with async request handling
- JWT-based authentication and authorization
- Role-based access control (Admin and User)
- User registration and secure login
- Admin-level APIs for user and chat management
- Persistent storage of prompts and responses
- Static frontend served directly from backend
- Dockerized application for consistent deployment
- Environment-based configuration and secrets management

---

## Technology Stack

**Backend**
- Python
- FastAPI
- SQLAlchemy ORM
- Pydantic
- OAuth2 with JWT authentication

**Database**
- Relational database using SQLAlchemy
- PostgreSQL

**DevOps**
- Docker
- Environment-based configuration (.env)

---

## Authentication & Authorization

- Secure login using JWT tokens
- OAuth2 Bearer token flow
- Role-based access enforcement
- Admin account auto-seeded via environment variables

---
## Code Generation Flow

1. User submits a prompt via API or frontend
2. Prompt is processed through the LLM interaction workflow
3. Generated response is returned to the user
4. Prompt and response are stored in the database
5. Admins can review interactions via admin APIs

---


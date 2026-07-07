# Intellex

Enterprise AI Knowledge Platform powered by Retrieval-Augmented Generation (RAG).

Intellex enables organizations to securely upload internal documents and interact with them using natural language while enforcing enterprise-grade access control through Role-Based and ACL-based permissions.

Unlike traditional chatbots, Intellex ensures users only retrieve information they are authorized to access, making it suitable for confidential organizational knowledge.

---

## Features

- Multi-Tenant Architecture
- Organization Management
- Department & Team Hierarchy
- JWT Authentication
- Role-Based Access Control (RBAC)
- Document Access Control Lists (ACL)
- Secure Document Upload Pipeline
- Hybrid Search Retrieval
- Semantic Search using Vector Embeddings
- Chat Sessions
- Chat History
- Enterprise-grade Database Design
- Modular FastAPI Backend
- Alembic Database Migrations

---

## Tech Stack

Backend

- FastAPI
- Python
- SQLAlchemy 2.x
- Alembic

Database

- PostgreSQL
- Qdrant

AI

- LangChain
- Gemini
- Jina / Nomic Embeddings
- Hybrid Search
- Reranking

Frontend (Upcoming)

- Next.js

---

## Architecture

(User Architecture Diagram)

(RAG Pipeline Diagram)

---

## Project Structure

app/
models/
api/
services/
schemas/
core/
database/

alembic/

uploads/

---

## Database Design

Current Entities

- Organizations
- Departments
- Teams
- Users
- Documents
- Chat Sessions
- Chat History
- Document ACL

---

## Roadmap

- Authentication
- Admin Dashboard
- Document Upload
- OCR Support
- Dynamic Chunking
- Embedding Pipeline
- Qdrant Integration
- Hybrid Search
- Reranker
- Citation Support
- Semantic Cache
- Feedback System
- LangGraph Agents

---

## Current Status

Database Architecture Completed

Authentication (Next)

---

## Author

Abhishek

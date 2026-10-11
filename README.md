# Database Homelab

## Overview

Setting up an environment to practice database management and understand low-level concepts.
Added a FastAPI with 

## Completed Tasks

- [x] Replication: Done
- [x] Caching: Done
- [x] Authentication: Done
- [ ] PgPooling: Pending
- [ ] Sharding: Pending
- [x] pg_dump and pg_restore: Done

## Prerequisites

only docker Docker Compose is needed

### Environment Setup

```bash
cp .env.example .env
```
- Modify the required fields in .env

### Start the Environment

```bash
docker compose up -d
```
## Verify running processes

```bash
docker compose stats
```
### Stop the Environment

```bash
docker compose down
```

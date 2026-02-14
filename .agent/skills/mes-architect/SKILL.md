---
name: mes-architect
description: Design patterns for Manufacturing Execution Systems (MES), ISA-95 standards, and industrial data modeling.
---

# MES Architecture Guidelines

When designing data models or workflows for MES (Manufacturing Execution Systems), adhere to these principles:

### 1. Hierarchy (ISA-95 compliant)
Model data utilizing the standard physical hierarchy:
- **Enterprise** (Company)
- **Site** (Physical Factory)
- **Area** (Production Zone)
- **Work Center / Line** (Logical grouping of equipment)
- **Work Unit / Equipment** (Physical Machine)

### 2. Data Integrity & Traceability
- **Immutability**: Production logs (telemetry, operator actions) must be append-only. Never UPDATE historical records.
- **Genealogy**: Every `Lot` or `Batch` must reference its parent materials and the specific `WorkOrder` that produced it.
- **Audit Trails**: All critical actions (status changes, setpoint updates) must record `user_id`, `timestamp`, and `previous_value`.

### 3. State Machines
- Equipment and Work Orders must follow strict state machines (e.g., Created -> Scheduled -> Running -> Paused -> Completed).
- Define valid transitions explicitly in the database (e.g., via a `transitions` table or strict application logic).

### 4. SaaS/Multi-tenancy
- For SaaS MES, ensure strict data isolation using `organization_id` on ALL tables.
- Use composite primary keys where appropriate (e.g., `organization_id` + `serial_number`) to prevent collisions across tenants.

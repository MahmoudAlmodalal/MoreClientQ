# API Interface Contracts: Auth & Tenancy

This document defines the HTTP request/response contracts for the endpoints introduced in Phase 1.

---

## 1. Authentication & Tenant Setup Endpoints

### 1.1 Tenant Registration (`POST /api/v1/auth/register`)
Exposes public registration to create a tenant and the primary owner account.

* **Method**: `POST`
* **Path**: `/api/v1/auth/register`
* **Access**: Public
* **Request Body** (`application/json`):
  ```json
  {
    "slug": "acme",
    "tenant_name": "Acme Corp",
    "email": "owner@acme.com",
    "password": "StrongPassword123!"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Tenant registered successfully",
    "data": {
      "tenant": {
        "id": "8fa53874-9844-4861-bf96-5f7bd0cb11aa",
        "slug": "acme",
        "name": "Acme Corp",
        "is_active": true
      },
      "user": {
        "id": "e0b9b3cc-660c-4395-8857-e6f79d95cf10",
        "email": "owner@acme.com",
        "role": "owner"
      }
    }
  }
  ```
* **Errors**:
  * `400 Bad Request`: If the slug is already registered, or password/slug format is invalid.

---

### 1.2 User Login (`POST /api/v1/auth/login`)
Authenticates credentials and returns session tokens.

* **Method**: `POST`
* **Path**: `/api/v1/auth/login`
* **Access**: Public
* **Request Body** (`application/json`):
  ```json
  {
    "email": "owner@acme.com",
    "password": "StrongPassword123!"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "d748f2b79a83d4c38210feab99...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
  * *Note: The access token JWT payload contains claims: `sub` (User UUID), `tenant_id` (Tenant UUID), `tenant_slug` (string), `role` (owner|admin|member|viewer), `jti` (unique token ID), and `exp` (timestamp).*
* **Errors**:
  * `401 Unauthorized`: Invalid email or password.
  * `403 Forbidden`: Account or tenant deactivated.

---

### 1.3 Refresh Token (`POST /api/v1/auth/refresh`)
Generates a new access token using a refresh token.

* **Method**: `POST`
* **Path**: `/api/v1/auth/refresh`
* **Access**: Public
* **Request Body** (`application/json`):
  ```json
  {
    "refresh_token": "d748f2b79a83d4c38210feab99..."
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
* **Errors**:
  * `401 Unauthorized`: Invalid or expired refresh token.

---

## 2. Team Management Endpoints

*All endpoints under this section require a valid access token in the `Authorization: Bearer <token>` header, and an `X-Tenant-ID` header matching the user's tenant UUID.*

### 2.1 Invite Team Member (`POST /api/v1/users/invite`)
Allows administrators or owners to invite a new user.

* **Method**: `POST`
* **Path**: `/api/v1/users/invite`
* **Access**: Tenant Admin, Tenant Owner
* **Request Body** (`application/json`):
  ```json
  {
    "email": "collaborator@acme.com",
    "role": "member"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Invitation created successfully",
    "data": {
      "id": "51bc6d73-6111-4f11-9a74-d4b912c9bf10",
      "email": "collaborator@acme.com",
      "role": "member",
      "invitation_link": "http://acme.localhost:3000/register?token=inv_tok_8f9024c3"
    }
  }
  ```
  * *Note: In Phase 1, `invitation_link` is returned in the API payload to simulate email delivery.*

---

### 2.2 Accept Invitation (`POST /api/v1/auth/invite/accept`)
Registers a user profile using a secure invitation token.

* **Method**: `POST`
* **Path**: `/api/v1/auth/invite/accept`
* **Access**: Public
* **Request Body** (`application/json`):
  ```json
  {
    "token": "inv_tok_8f9024c3",
    "password": "SecurePassword987!"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Invitation accepted successfully. Account activated.",
    "data": {
      "user_id": "c88f1141-9988-4c12-9ab1-cdb4929c1e10",
      "email": "collaborator@acme.com",
      "role": "member"
    }
  }
  ```

---

### 2.3 List Users (`GET /api/v1/users`)
Lists all members in the current tenant workspace.

* **Method**: `GET`
* **Path**: `/api/v1/users`
* **Access**: Tenant Owner, Admin, Member
* **Response (200 OK)**:
  ```json
  [
    {
      "id": "e0b9b3cc-660c-4395-8857-e6f79d95cf10",
      "email": "owner@acme.com",
      "role": "owner",
      "is_active": true,
      "created_at": "2026-06-06T12:00:00Z"
    },
    {
      "id": "c88f1141-9988-4c12-9ab1-cdb4929c1e10",
      "email": "collaborator@acme.com",
      "role": "member",
      "is_active": true,
      "created_at": "2026-06-06T12:15:00Z"
    }
  ]
  ```

---

### 2.4 Update User Role (`PATCH /api/v1/users/{id}`)
Modifies a team member's role.

* **Method**: `PATCH`
* **Path**: `/api/v1/users/e0b9b3cc-660c-4395-8857-e6f79d95cf10`
* **Access**: Tenant Owner, Admin (Admins cannot change Owner roles)
* **Request Body** (`application/json`):
  ```json
  {
    "role": "admin"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "User role updated successfully",
    "data": {
      "id": "e0b9b3cc-660c-4395-8857-e6f79d95cf10",
      "role": "admin"
    }
  }
  ```

---

### 2.5 Remove User (`DELETE /api/v1/users/{id}`)
Removes a team member from the workspace.

* **Method**: `DELETE`
* **Path**: `/api/v1/users/c88f1141-9988-4c12-9ab1-cdb4929c1e10`
* **Access**: Tenant Owner, Admin
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "User deleted successfully"
  }
  ```

---

## 3. Tenant Management & Offboarding

### 3.1 Tenant Offboarding / Delete (`DELETE /api/v1/tenants/self`)
Performs partial tenant offboarding by cascade-deleting database entries and blocklisting keys.

* **Method**: `DELETE`
* **Path**: `/api/v1/tenants/self`
* **Access**: Tenant Owner
* **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Tenant offboarded successfully. PostgreSQL cascade deleted, JWT active sessions blocklisted."
  }
  ```

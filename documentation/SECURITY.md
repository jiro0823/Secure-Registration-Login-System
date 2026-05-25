# Security Documentation — Secure Registration & Login System

## 1. What is Hashing?

**Hashing** is a one-way mathematical function that converts input data into a fixed-length string of characters. Unlike encryption, hashing is **irreversible** — you cannot recover the original data from the hash.

### How it works:
```
Input: "MyPassword123!"
          ↓
   Hash Function (bcrypt)
          ↓
Output: "$2b$12$LJ3m4ys8Gp0bW5Fz..."
```

### Why use hashing for passwords?
- Even if the database is compromised, attackers cannot retrieve plaintext passwords
- Each login attempt re-hashes the input and compares with the stored hash
- **bcrypt** is specifically designed for passwords — it's intentionally slow to resist brute force

---

## 2. What is Salt?

A **salt** is a unique, randomly generated string that is combined with the password **before** hashing. Each user gets their own unique salt.

### Why salt is critical:
- **Without salt**: Two users with the same password produce the same hash → attackers can use precomputed tables (rainbow tables)
- **With salt**: Every hash is unique, even for identical passwords

### Example:
```
User A: password="hello" + salt="abc123" → hash="x9f2k..."
User B: password="hello" + salt="def456" → hash="m3p7q..."
```

Same password, different hashes!

### Our implementation:
```python
import secrets
salt = secrets.token_hex(32)  # 64-char cryptographic salt
```

---

## 3. What is Pepper?

A **pepper** is an application-wide secret that is combined with the password **in addition to** the salt. Unlike salt, the pepper is:

- **NOT stored in the database**
- Stored only in environment variables (`.env` file)
- The same for all users (but unique per application)

### Defense-in-depth:
```
Scenario: Database is fully compromised
- Attacker has: hashes + salts
- Attacker does NOT have: pepper
- Result: Cannot perform offline cracking without the pepper
```

### Our formula:
```
bcrypt(password + salt + pepper) → stored_hash
```

---

## 4. Password Strength Validation

Strong passwords are the first line of defense. Our system enforces:

| Rule | Requirement | Example Pass | Example Fail |
|------|-------------|-------------|--------------|
| Length | ≥ 12 characters | `Cyber@2026Secure` | `Ab1!` |
| Uppercase | ≥ 1 uppercase letter | `C`, `S` | all lowercase |
| Lowercase | ≥ 1 lowercase letter | `yber`, `ecure` | ALL CAPS |
| Digit | ≥ 1 number | `2026` | no numbers |
| Special | ≥ 1 special character | `@` | no symbols |

### Strength levels:
- **Weak** (0-2 rules passed): Red bar, rejected
- **Medium** (3-4 rules passed): Orange bar, rejected
- **Strong** (all 5 rules passed): Green bar, accepted

---

## 5. Why Strong Passwords Matter

| Attack Type | Weak Password Time | Strong Password Time |
|------------|--------------------|--------------------|
| Brute Force | Seconds to minutes | Centuries |
| Dictionary | Instant | Not applicable |
| Rainbow Table | Instant (without salt) | Not applicable (with salt) |
| Credential Stuffing | If reused | Unique passwords resist |

---

## 6. OWASP Top 10 Risks Mitigated

| OWASP Risk | Our Mitigation |
|-----------|----------------|
| **A01: Broken Access Control** | JWT-protected routes, authorization checks |
| **A02: Cryptographic Failures** | bcrypt + salt + pepper, secure JWT signing |
| **A03: Injection** | SQLAlchemy ORM (no raw SQL), input sanitization |
| **A04: Insecure Design** | Clean architecture, defense-in-depth |
| **A05: Security Misconfiguration** | Security headers, CORS whitelist, .env secrets |
| **A06: Vulnerable Components** | Pinned dependency versions |
| **A07: Auth Failures** | Rate limiting, account lockout, password strength |
| **A08: Data Integrity Failures** | JWT signature verification |
| **A09: Logging Failures** | Structured error handling |
| **A10: Server-Side Request Forgery** | No external URL fetching |

---

## 7. Screenshots Checklist

- [ ] Registration page with password strength meter
- [ ] Weak password rejection
- [ ] Strong password acceptance
- [ ] Login page
- [ ] Successful login and JWT token
- [ ] Dashboard with security status
- [ ] Account lockout after 5 failures
- [ ] Rate limiting (429 response)
- [ ] Database showing hashed passwords (no plaintext)
- [ ] Security headers in browser DevTools
- [ ] API documentation (/docs)
- [ ] Live deployed URL

---

## 8. Architecture Security Overview

```
┌─────────────────────────────────────────┐
│              CLIENT (Browser)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Register │ │  Login   │ │Dashboard │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │             │             │       │
│       │    JWT in localStorage    │       │
└───────┼─────────────┼─────────────┼───────┘
        │ HTTPS       │ HTTPS       │ HTTPS
┌───────┼─────────────┼─────────────┼───────┐
│       ▼             ▼             ▼       │
│  ┌────────────────────────────────────┐   │
│  │        SECURITY MIDDLEWARE         │   │
│  │  Rate Limit │ CORS │ CSP Headers  │   │
│  └──────────────────┬─────────────────┘   │
│                     ▼                     │
│  ┌────────────────────────────────────┐   │
│  │        INPUT VALIDATION            │   │
│  │  Pydantic │ Sanitization │ Length  │   │
│  └──────────────────┬─────────────────┘   │
│                     ▼                     │
│  ┌────────────────────────────────────┐   │
│  │        AUTH LOGIC                  │   │
│  │  Salt + Pepper + Bcrypt │ JWT     │   │
│  └──────────────────┬─────────────────┘   │
│                     ▼                     │
│  ┌────────────────────────────────────┐   │
│  │        DATABASE (SQLAlchemy ORM)   │   │
│  │  hash │ salt │ attempts │ lockout │   │
│  └────────────────────────────────────┘   │
│              SERVER (FastAPI)              │
└───────────────────────────────────────────┘
```

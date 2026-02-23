# Auth — Аутентификация и авторизация

## Обзор

Три основных flow:
1. **Регистрация** — 3-шаговая с верификацией email (6-значный код)
2. **Авторизация** — login + JWT access/refresh tokens
3. **Восстановление пароля** — одноразовый токен на почту

Задействованные таблицы: `User`, `EmailVerification`, `RefreshToken`, `PasswordReset`.

---

## Участники

```
Client (Flutter)
  ↓ HTTP
API Gateway (:3000)
  ↓ NATS request/response
Game-Core (AuthService)
  ↓ NATS event (fire-and-forget)
Notification Service → Email (Resend / AWS SES)
```

---

## 1. Регистрация

Трёхшаговый flow. User создаётся **только после** подтверждения email.

### Диаграмма

```
Client                  API Gateway              Game-Core                Notification
  │                         │                        │                        │
  │ POST /auth/register/    │                        │                        │
  │      send-code          │                        │                        │
  │ { email }               │                        │                        │
  │────────────────────────>│                        │                        │
  │                         │  auth.register.        │                        │
  │                         │       send_code        │                        │
  │                         │───────────────────────>│                        │
  │                         │                        │ 1. Normalize email     │
  │                         │                        │ 2. Check: User exists? │
  │                         │                        │    → 409 Conflict      │
  │                         │                        │ 3. Generate 6-digit    │
  │                         │                        │    code                │
  │                         │                        │ 4. Delete old          │
  │                         │                        │    EmailVerification   │
  │                         │                        │    for this email      │
  │                         │                        │ 5. Create              │
  │                         │                        │    EmailVerification   │
  │                         │                        │    (TTL 15 мин)        │
  │                         │                        │                        │
  │                         │                        │ emit: notify.send_     │
  │                         │                        │ email.resend           │
  │                         │                        │───────────────────────>│
  │                         │                        │                        │ Render
  │                         │                        │                        │ registration-code.hbs
  │                         │                        │                        │ → Send email
  │                         │  { message }           │                        │
  │                         │<───────────────────────│                        │
  │ 200 { message:          │                        │                        │
  │  "Verification code     │                        │                        │
  │   sent" }               │                        │                        │
  │<────────────────────────│                        │                        │
  │                         │                        │                        │
  │ POST /auth/register/    │                        │                        │
  │      verify-code        │                        │                        │
  │ { email, code }         │                        │                        │
  │────────────────────────>│                        │                        │
  │                         │  auth.register.        │                        │
  │                         │       verify_code      │                        │
  │                         │───────────────────────>│                        │
  │                         │                        │ 1. Find                │
  │                         │                        │    EmailVerification   │
  │                         │                        │    where email + code  │
  │                         │                        │    + not expired       │
  │                         │                        │ 2. Set verified = true │
  │                         │  { message }           │                        │
  │                         │<───────────────────────│                        │
  │ 200 { message:          │                        │                        │
  │  "Email verified" }     │                        │                        │
  │<────────────────────────│                        │                        │
  │                         │                        │                        │
  │ POST /auth/register     │                        │                        │
  │ { email, password }     │                        │                        │
  │────────────────────────>│                        │                        │
  │                         │  auth.register         │                        │
  │                         │───────────────────────>│                        │
  │                         │                        │ 1. Check: User exists? │
  │                         │                        │    → 409              │
  │                         │                        │ 2. Check:              │
  │                         │                        │    EmailVerification   │
  │                         │                        │    verified = true     │
  │                         │                        │    + not expired       │
  │                         │                        │    → 400 if not       │
  │                         │                        │ 3. Hash password       │
  │                         │                        │    (bcrypt, cost 12)   │
  │                         │                        │ 4. Transaction:        │
  │                         │                        │    - Create User       │
  │                         │                        │    - Delete            │
  │                         │                        │      EmailVerification │
  │                         │                        │                        │
  │                         │                        │ emit: welcome email    │
  │                         │                        │───────────────────────>│
  │                         │  { message }           │                        │ welcome.hbs
  │                         │<───────────────────────│                        │
  │ 200 { message:          │                        │                        │
  │  "User created" }       │                        │                        │
  │<────────────────────────│                        │                        │
```

### Эндпоинты

| Шаг | Метод | URL | Body | NATS pattern |
|-----|-------|-----|------|--------------|
| 1. Отправка кода | POST | `/auth/register/send-code` | `{ email }` | `auth.register.send_code` |
| 2. Подтверждение кода | POST | `/auth/register/verify-code` | `{ email, code }` | `auth.register.verify_code` |
| 3. Создание аккаунта | POST | `/auth/register` | `{ email, password }` | `auth.register` |

### Валидация (DTO)

| Поле | Правила |
|------|---------|
| email | `@IsEmail()` |
| code | `@IsString()`, `@MinLength(6)`, `@MaxLength(6)` |
| password | `@IsString()`, `@MinLength(8)`, `@MaxLength(64)` |

### Таблицы БД

**EmailVerification** — временная запись, живёт до создания User.

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID, PK | |
| email | String | |
| code | String | 6-значный код (`randomInt(0, 1_000_000).toString().padStart(6, '0')`) |
| expiresAt | DateTime | `now() + 15 минут` |
| verified | Boolean | `false` → `true` после подтверждения кода |
| createdAt | DateTime | |

Индексы: `email`, `expiresAt`.

При повторном запросе кода — старые записи для этого email удаляются. После успешного создания User — запись EmailVerification удаляется.

### Ошибки

| Ситуация | Код | Сообщение |
|----------|-----|-----------|
| Email уже зарегистрирован | 409 | Conflict |
| Код неверный или истёк | 400 | Bad Request |
| Email не верифицирован | 400 | Bad Request |

---

## 2. Авторизация (Login)

### Диаграмма

```
Client                  API Gateway              Game-Core
  │                         │                        │
  │ POST /auth/login        │                        │
  │ { email, password }     │                        │
  │────────────────────────>│                        │
  │                         │  auth.login            │
  │                         │───────────────────────>│
  │                         │                        │ 1. Normalize email
  │                         │                        │ 2. Find User by email
  │                         │                        │    → 401 if not found
  │                         │                        │ 3. bcrypt.compare()
  │                         │                        │    → 401 if mismatch
  │                         │                        │ 4. Issue tokens
  │                         │  { accessToken,        │
  │                         │    refreshToken }       │
  │                         │<───────────────────────│
  │ 200 { accessToken,      │                        │
  │       refreshToken }    │                        │
  │<────────────────────────│                        │
```

### JWT Tokens

**Access Token:**

| Параметр | Значение |
|----------|----------|
| Алгоритм | HS256 (по умолчанию) или RS256 |
| TTL | 15 минут (env `JWT_ACCESS_TTL`) |
| Secret | env `JWT_SECRET` |
| Payload | `{ sub: userId, email }` |

**Refresh Token:**

| Параметр | Значение |
|----------|----------|
| Алгоритм | тот же, что и access |
| TTL | 30 дней (env `JWT_REFRESH_TTL_DAYS`) |
| Secret | env `JWT_REFRESH_SECRET` |
| Payload | `{ sub: userId, email, rid: randomUUID() }` |
| Хранение | Запись в таблице `RefreshToken` |

Таблица **RefreshToken**:

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID, PK | |
| token | String, unique | Полный JWT |
| userId | UUID, FK → User | |
| expiresAt | DateTime | |
| createdAt | DateTime | |

### Refresh (обновление access token)

```
Client                  API Gateway              Game-Core
  │                         │                        │
  │ POST /auth/refresh      │                        │
  │ { refreshToken }        │                        │
  │────────────────────────>│                        │
  │                         │  auth.refresh          │
  │                         │───────────────────────>│
  │                         │                        │ 1. Verify JWT signature
  │                         │                        │ 2. Find RefreshToken
  │                         │                        │    in DB
  │                         │                        │ 3. Check expiresAt
  │                         │                        │ 4. Generate new
  │                         │                        │    access token
  │                         │  { accessToken }       │
  │                         │<───────────────────────│
  │ 200 { accessToken }     │                        │
  │<────────────────────────│                        │
```

Refresh token **не ротируется** — возвращается только новый access token.

### Валидация токена (guard)

Все защищённые эндпоинты используют `GatewayJwtGuard`:

```
Client                  API Gateway              Game-Core
  │                         │                        │
  │ GET /character/me       │                        │
  │ Authorization:          │                        │
  │   Bearer <accessToken>  │                        │
  │────────────────────────>│                        │
  │                         │ GatewayJwtGuard:       │
  │                         │  auth.validate_token   │
  │                         │───────────────────────>│
  │                         │                        │ Verify JWT
  │                         │  { valid, user:        │
  │                         │    { sub, email } }    │
  │                         │<───────────────────────│
  │                         │                        │
  │                         │ req.user = user        │
  │                         │ → proceed to handler   │
  │                         │                        │
```

Guard извлекает `Bearer` токен из заголовка `Authorization`, отправляет его в game-core через NATS (`auth.validate_token`). При успехе — в `req.user` записывается `{ sub: userId, email }`.

### Ошибки

| Ситуация | Код | Сообщение |
|----------|-----|-----------|
| Неверный email или пароль | 401 | Unauthorized |
| Токен невалиден / истёк | 401 | Unauthorized |
| Refresh token не найден в БД | 401 | Unauthorized |

---

## 3. Восстановление пароля

### Диаграмма

```
Client                  API Gateway              Game-Core                Notification
  │                         │                        │                        │
  │ POST /auth/             │                        │                        │
  │      forgot-password    │                        │                        │
  │ { email }               │                        │                        │
  │────────────────────────>│                        │                        │
  │                         │  auth.forgot_password  │                        │
  │                         │───────────────────────>│                        │
  │                         │                        │ 1. Normalize email     │
  │                         │                        │ 2. Find User by email  │
  │                         │                        │ 3. If not found →      │
  │                         │                        │    return success      │
  │                         │                        │    (security)          │
  │                         │                        │ 4. Generate UUID token │
  │                         │                        │ 5. Create              │
  │                         │                        │    PasswordReset       │
  │                         │                        │    (TTL 1 час)         │
  │                         │                        │                        │
  │                         │                        │ emit: password-reset   │
  │                         │                        │───────────────────────>│
  │                         │                        │                        │ password-reset.hbs
  │                         │                        │                        │ → Send email with
  │                         │                        │                        │   resetLink
  │                         │  { message }           │                        │
  │                         │<───────────────────────│                        │
  │ 200 { message:          │                        │                        │
  │  "If email exists,      │                        │                        │
  │   reset link sent" }    │                        │                        │
  │<────────────────────────│                        │                        │
  │                         │                        │                        │
  │ POST /auth/             │                        │                        │
  │      reset-password     │                        │                        │
  │ { token, newPassword }  │                        │                        │
  │────────────────────────>│                        │                        │
  │                         │  auth.reset_password   │                        │
  │                         │───────────────────────>│                        │
  │                         │                        │ 1. Find PasswordReset  │
  │                         │                        │    by token            │
  │                         │                        │ 2. Check: exists?      │
  │                         │                        │    used = false?       │
  │                         │                        │    not expired?        │
  │                         │                        │ 3. Hash new password   │
  │                         │                        │    (bcrypt, cost 12)   │
  │                         │                        │ 4. Transaction:        │
  │                         │                        │    - Update User       │
  │                         │                        │      passwordHash      │
  │                         │                        │    - Set used = true   │
  │                         │                        │                        │
  │                         │                        │ emit: password-changed │
  │                         │                        │───────────────────────>│
  │                         │  { message }           │                        │ password-changed.hbs
  │                         │<───────────────────────│                        │
  │ 200 { message:          │                        │                        │
  │  "Password changed" }   │                        │                        │
  │<────────────────────────│                        │                        │
```

### Эндпоинты

| Шаг | Метод | URL | Body | NATS pattern |
|-----|-------|-----|------|--------------|
| 1. Запрос сброса | POST | `/auth/forgot-password` | `{ email }` | `auth.forgot_password` |
| 2. Новый пароль | POST | `/auth/reset-password` | `{ token, newPassword }` | `auth.reset_password` |

### Валидация (DTO)

| Поле | Правила |
|------|---------|
| email | `@IsEmail()` |
| token | `@IsString()` |
| newPassword | `@IsString()`, `@MinLength(8)` |

### Таблица БД

**PasswordReset:**

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID, PK | |
| token | String, unique | UUID v4 |
| userId | UUID, FK → User | |
| expiresAt | DateTime | `now() + 1 час` |
| used | Boolean | `false` → `true` после использования |
| createdAt | DateTime | |

### Безопасность

- **Забытый пароль всегда возвращает 200** — не раскрывает, существует ли email в системе
- **Токен одноразовый** — `used = true` после применения, повторное использование невозможно
- **TTL 1 час** — после истечения токен невалиден
- **Уведомление** — после смены пароля на email отправляется подтверждение (template `password-changed`)

### Ошибки

| Ситуация | Код | Сообщение |
|----------|-----|-----------|
| Токен не найден / уже использован / истёк | 400 | Bad Request |

---

## Сводная таблица эндпоинтов

| Метод | URL | Guard | Описание |
|-------|-----|-------|----------|
| POST | `/auth/register/send-code` | -- | Отправить код верификации на email |
| POST | `/auth/register/verify-code` | -- | Подтвердить 6-значный код |
| POST | `/auth/register` | -- | Создать аккаунт (email должен быть verified) |
| POST | `/auth/login` | -- | Получить access + refresh tokens |
| POST | `/auth/refresh` | -- | Обновить access token |
| POST | `/auth/forgot-password` | -- | Запросить сброс пароля |
| POST | `/auth/reset-password` | -- | Установить новый пароль по токену |

---

## Email-шаблоны

| Шаблон | Когда отправляется | Контекст |
|--------|-------------------|----------|
| `registration-code.hbs` | Шаг 1 регистрации | `{ code, expiresMinutes }` |
| `welcome.hbs` | Шаг 3 регистрации (после создания User) | `{ loginLink }` |
| `password-reset.hbs` | Forgot password | `{ email, resetLink }` |
| `password-changed.hbs` | После смены пароля | `{ email }` |

---

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `JWT_SECRET` | Секрет для подписи access token (HS256) | **обязательна** |
| `JWT_REFRESH_SECRET` | Секрет для подписи refresh token | **обязательна** |
| `JWT_ALGORITHM` | `HS256` или `RS256` | `HS256` |
| `JWT_ACCESS_TTL` | TTL access token | `15m` |
| `JWT_REFRESH_TTL_DAYS` | TTL refresh token в днях | `30` |
| `REGISTRATION_CODE_TTL_MINUTES` | TTL кода верификации | `15` |
| `APP_URL` | Базовый URL для ссылок в email | -- |

---

## Известные ограничения

- Нет эндпоинта logout / отзыва refresh token (таблица `RefreshToken` готова, endpoint не реализован)
- Refresh token не ротируется при обновлении access token
- `emitEmail` не логирует ошибки NATS (fire-and-forget)
- Нет rate limiting на auth-эндпоинтах

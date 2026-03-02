# Geolocation — Геолокация, направление и состояние движения

## Обзор

Геолокация привязана к **User**, а не к Character. Физический человек ходит по миру — при смене персонажа координаты сохраняются.

Сервер определяет:
- **Позицию** (lat, lng) — от GPS клиента
- **Направление** (heading, 0-360) — от компаса клиента или вычисляется из двух точек
- **Состояние** (moving / idle) — вычисляется сервером по буферу позиций

---

## Модель данных

### PostgreSQL — User (изменения)

Геолокация переносится из Character в User:

| Поле | Тип | Описание |
|---|---|---|
| lat | Float? | Широта |
| lng | Float? | Долгота |
| heading | Float? | Направление 0-360, север = 0 |
| lastMovedAt | DateTime? | Время последнего перемещения |

Индекс: `@@index([lat, lng])`

> Character больше не содержит lat, lng, lastMovedAt.

### Redis — ключи

#### `user:pos:{userId}` — текущая позиция (TTL 1h)

```json
{
  "lat": 55.7558,
  "lng": 37.6173,
  "heading": 45.2,
  "speed": 4.8,
  "isMoving": true,
  "at": "2026-02-25T12:00:00.000Z",
  "clientHeading": 44.0
}
```

Основной ключ. Используется для:
- Anti-cheat (скорость между точками)
- Текущее состояние для ответа клиенту
- Fallback при переподключении

#### `user:pos:buf:{userId}` — буфер позиций (TTL 30s)

Redis List, последние 5 точек (LPUSH + LTRIM 0 4):

```json
{ "lat": 55.7558, "lng": 37.6173, "at": "2026-02-25T12:00:00.000Z" }
```

Используется для определения isMoving — усредняет GPS-шум.

#### `geo:players` — Redis GEO Set

```
GEOADD geo:players {lng} {lat} {userId}
```

Для поиска ближайших игроков через `GEORADIUS`. Обновляется при каждом `character:move`. Удаляется при disconnect (`ZREM`).

#### `user:pos:pub:{userId}` — публичный кэш (TTL 60s)

```json
{
  "userId": "uuid",
  "characterId": "uuid",
  "characterName": "Achilles",
  "characterClass": "WARRIOR",
  "characterLevel": 12,
  "lat": 55.7558,
  "lng": 37.6173,
  "heading": 45.2,
  "isMoving": true
}
```

Для быстрой сборки списка ближайших без обращения к PostgreSQL. Обновляется при `character:move` и при смене персонажа.

---

## Определение направления (heading)

### Формула bearing (forward azimuth)

```
y = sin(lng2 - lng1) * cos(lat2)
x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lng2 - lng1)
heading = atan2(y, x) → нормализовать в [0, 360)
```

Где 0 = север, 90 = восток, 180 = юг, 270 = запад.

### Алгоритм выбора heading

```
distance = haversine(prev, new)

1. distance < 2м (JITTER_THRESHOLD)
   → heading = предыдущий (GPS-джиттер, не менять)

2. clientHeading передан И distance > 5м (MIN_HEADING_DISTANCE)
   → heading = clientHeading (доверяем компасу)

3. distance >= 3м (MIN_BEARING_DISTANCE)
   → heading = bearing(prev, new) (вычисляем из точек)

4. иначе
   → heading = предыдущий
```

### Гибридный подход: почему

- **Компас устройства** — точнее при повороте на месте (человек развернулся, но не сдвинулся). Но не на всех устройствах стабилен.
- **Серверный bearing** — надёжный fallback, работает всегда при >= 2 точках. Шумит при малых расстояниях.
- **Приоритет клиента** при достаточном перемещении.

### Константы

| Константа | Значение | Описание |
|---|---|---|
| JITTER_THRESHOLD_M | 2 | Менее 2м — GPS-джиттер |
| MIN_HEADING_DISTANCE_M | 5 | Доверяем clientHeading при > 5м |
| MIN_BEARING_DISTANCE_M | 3 | Вычисляем bearing при > 3м |
| DEFAULT_HEADING | 0 | По умолчанию — север |

---

## Определение состояния движения (moving / idle)

### Алгоритм

При каждом `character:move`:

```
1. LPUSH позицию в буфер user:pos:buf:{userId}
   LTRIM 0 4 (держим 5 последних)

2. Если в буфере < 2 точек → isMoving = false

3. Иначе:
   totalDistance = сумма haversine(buf[i], buf[i+1]) по всем парам
   timeDelta = newest.at - oldest.at
   speed = totalDistance / timeDelta (км/ч)

   isMoving = speed > 1.5 км/ч И totalDistance > 3м
```

### Idle timeout

Клиент может перестать слать обновления (экран погас, GPS молчит). Сервер сам переводит в idle:

- `setInterval` каждые 3 секунды на GameGateway
- Для каждого подключённого: если `(now - pos.at) > 5 секунд` и `pos.isMoving = true` → обновить `isMoving = false` в Redis, broadcast ближайшим

### Фильтрация GPS-джиттера

GPS на мобильных даёт погрешность 3-15 метров. Когда человек стоит, координаты "плавают".

Стратегии:
- **Буфер из 5 точек** — усредняет шум
- **Порог дистанции 3м** — если суммарно < 3м за 5 точек → стоит
- **Порог скорости 1.5 км/ч** — нормальная ходьба 4-6 км/ч, 1.5 отсекает дрейф
- **Поле accuracy от клиента** — при accuracy > 20м можно увеличить пороги

### Константы

| Константа | Значение | Описание |
|---|---|---|
| MOVING_SPEED_THRESHOLD_KMH | 1.5 | Скорость ниже — считаем стоит |
| MOVING_DISTANCE_THRESHOLD_M | 3 | Дистанция ниже — считаем стоит |
| IDLE_TIMEOUT_MS | 5000 | Нет обновлений > 5с → idle |
| POSITION_BUFFER_SIZE | 5 | Размер буфера позиций |

---

## WebSocket события

### `character:move` (вход, расширение)

Клиент → сервер:

```typescript
{
  lat: number;
  lng: number;
  clientHeading?: number;  // heading от компаса (0-360), опционально
  accuracy?: number;       // точность GPS в метрах, опционально
}
```

Сервер → клиент (ответ):

```typescript
{
  ok: boolean;
  reason?: 'speed_limit' | 'rate_limit';
  heading?: number;    // результирующий heading
  isMoving?: boolean;  // текущее состояние
  speed?: number;      // скорость км/ч
}
```

### `player:moved` (новое, broadcast)

Сервер → ближайшим игрокам при движении кого-то:

```typescript
{
  userId: string;
  characterId: string;
  lat: number;
  lng: number;
  heading: number;
  isMoving: boolean;
}
```

### `players:nearby` (новое, snapshot)

Сервер → клиенту, периодически или по запросу:

```typescript
[{
  userId: string;
  characterId: string;
  characterName: string;
  characterClass: string;
  characterLevel: number;
  lat: number;
  lng: number;
  heading: number;
  isMoving: boolean;
}]
```

---

## NATS контракты

### Новые паттерны

| Паттерн | Описание |
|---|---|
| `user.update_position` | Обновить позицию User в PostgreSQL |
| `user.get_position` | Получить позицию User |

### Интерфейсы

```typescript
interface UserUpdatePositionRequest {
  userId: string;
  lat: number;
  lng: number;
  heading: number;
  isMoving: boolean;
  speed: number;
  movedAt: string;  // ISO 8601
}

interface UserPositionResponse {
  lat: number | null;
  lng: number | null;
  heading: number | null;
  isMoving: boolean;
  lastMovedAt: string | null;
}
```

### Deprecated

`character.update_position` — заменён на `user.update_position`.

---

## Поток данных

```
Flutter (GPS + Compass)
  │
  │  WS: character:move { lat, lng, clientHeading?, accuracy? }
  ▼
api-gateway / GameGateway
  │
  ├─ 1. Валидация координат
  ├─ 2. Rate limit (не чаще 500мс)
  ├─ 3. Redis GET user:pos:{userId}
  ├─ 4. Anti-cheat: checkSpeed() ≤ 30 км/ч
  ├─ 5. haversine() → distance
  ├─ 6. resolveHeading() → heading
  ├─ 7. Redis LPUSH user:pos:buf:{userId} + computeIsMoving()
  ├─ 8. Redis SET user:pos:{userId}
  ├─ 9. Redis GEOADD geo:players
  ├─ 10. NATS → game-core → PostgreSQL User.update(lat, lng, heading, lastMovedAt)
  ├─ 11. Redis GEORADIUS geo:players 500м → nearby userIds
  └─ 12. Для каждого nearby: emit('player:moved', { ... })
  │
  ▼
Ответ: { ok, heading, isMoving, speed }
```

---

## Anti-cheat

### Исправление бага checkSpeed

Текущий код возвращает `0` при `hours <= 0` — позволяет телепорт при одинаковом timestamp.

```
// Было:
if (hours <= 0) return 0;

// Стало:
if (hours <= 0) return Infinity;
```

### Rate limiting

Не более 1 обновления позиции в 500мс на пользователя. При превышении — `{ ok: false, reason: 'rate_limit' }`.

### Позиция для битвы

Позиция берётся из `User.lat/lng` на сервере, а не из payload клиента. Это исключает спуфинг координат для начала битвы с далёким мобом.

```
// Было: payload.characterLat (от клиента — можно подделать)
// Стало: User.lat из БД (серверная правда)
```

### Heading валидация

Если клиент передаёт `clientHeading`, а серверный `bearing` отличается > 90 при перемещении > 10м — логировать как подозрительное (не блокировать, только мониторинг).

### Потеря GPS и переподключение

Если `(now - lastAt) > 30 секунд` при получении нового `character:move` — пропустить проверку скорости. GPS мог накопить drift за время простоя.

---

## Смена персонажа

При `POST /characters/:id/select`:

1. Позиция на User **не меняется** — физический игрок не двигался
2. heading, isMoving **сохраняются**
3. Обновить публичный кэш `user:pos:pub:{userId}` с данными нового персонажа (имя, класс, уровень)
4. Отправить ближайшим событие `player:changed` (смена аватара, не позиции)

---

## Edge cases

### Первое подключение (нет позиции)

- Redis пуст, PostgreSQL User.lat = null
- Anti-cheat пропускается
- heading = clientHeading или DEFAULT_HEADING (0, север)
- isMoving = false (буфер из 1 точки)

### GPS-джиттер при стоянии

- Буфер показывает суммарное перемещение < 3м
- isMoving = false
- heading не меняется (distance < 2м)
- Redis `at` обновляется (для актуальности), heading и isMoving — нет

### Смена персонажа во время ходьбы

- Координаты на User — не теряются
- Публичный кэш обновляется с новым character
- Для ближайших — смена спрайта, позиция та же

### Потеря GPS (туннель, здание)

- Клиент перестаёт слать `character:move`
- Через 5 секунд серверный idle-check переводит в idle
- При восстановлении GPS — новая позиция
- Если прошло > 30 сек и большое расстояние — anti-cheat не блокирует (пропуск проверки скорости)

### Disconnect и reconnect

- Disconnect: `ZREM geo:players {userId}`, ключ `user:pos` остаётся (TTL 1h)
- Reconnect: клиент шлёт `character:move`, сервер находит `user:pos` в Redis
- Если Redis протух — fallback из PostgreSQL User.lat/lng

---

## Радиус видимости

| Параметр | Значение | Описание |
|---|---|---|
| NEARBY_BROADCAST_RADIUS_M | 500 | Радиус real-time broadcast player:moved |
| NEARBY_REQUEST_MAX_RADIUS_M | 1000 | Максимальный радиус для map:request |

### Оптимизация broadcast

- Throttle: `player:moved` не чаще 1 раза в секунду для каждого наблюдателя
- Пропуск: если позиция изменилась менее чем на 1м — не broadcast'ить

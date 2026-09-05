# Инвентарь: чего не хватает от бэкенда

Аудит от 2026-07-02: сверка Hero-экрана Flutter (профиль + инвентарь единым скроллом,
сейчас на моке `HeroRepositoryImpl`) с реальным API troy-backend.

## Что уже есть — работы не требует

| Клиенту нужно | Бэкенд |
|---|---|
| Профиль: имя, класс, уровень, exp / expToNextLevel, золото | `GET /character/me` |
| Атрибуты (STR/INT/STA/AGI/SPI) + свободные очки | там же: base + freePoints, `computedStats.unspentPoints` |
| Производные статы (maxHp, physAtk, magicAtk, armor, magicResist, attackSpeed, critChance, mana/rage) | `computedStats` (учитывает base + level growth + очки + экипировку) |
| Раскидать очки атрибутов | `POST /character/me/points` |
| Список предметов с rarity, slot, equipped, quantity | `GET /inventory` (и в `/character/me` внутри) |
| Equip / unequip с проверкой слота и автоснятием предыдущего | `POST /inventory/equip/:itemId`, `POST /inventory/unequip/:slot` |
| Лут из боя попадает в инвентарь (стакается) | `InventoryService.addItems` из battle |
| 6 слотов, rarity 5 ступеней | enum'ы совпадают (ACCESSORY ↔ ring — вопрос маппинга) |

## Гэпы (бэкенд)

### 1. `Item.description` — нет колонки
Item-inspect sheet на клиенте показывает описание предмета. В модели `Item` поля нет.
**Сделать:** колонка `description String?` + миграция + заполнить в seed + отдаётся в
`GET /inventory` и `/character/me`.
**План (05.09):** [description-discard.md](./description-discard.md), SCRUM-15. Уточнение: в `/character/me` не
`include`, а `select`-whitelist, и только надетое — см. #7; поле добавляется явно, миграция `0019_item_description` отдельная.
**Бэкенд закрыт 05.09** (сессия 1) — колонка, миграция, seed, Swagger DTO, админка; клиентская выдача (карточка на клиенте) — сессия 2.

### 2. Consumables — тип есть, механики нет
`ItemType.CONSUMABLE` существует, но у Item нет полей эффекта (hpRestore и т.п.)
и нет endpoint'а применения.
**Сделать:** поля эффекта на Item (минимум `hpRestore Int @default(0)`),
`POST /inventory/use/:itemId` — декремент quantity (удаление при 0), применение эффекта.
**Блокер-вопрос:** текущего HP между боями в схеме нет (Character без `currentHp`) —
либо зелья вне скоупа MVP-3, либо сначала решить про персистентный HP.
**Решение (05.09):** зелья — боевое действие по правилу WoW «одно зелье за бой», персистентный HP не
заводим; вынесено из MVP-3 в [items/](../items/README.md) §2.3, SCRUM-19.

### 3. Выбросить / продать предмет — endpoint'а нет
Мешок растёт бесконечно, избавиться от предмета нельзя.
**Минимум:** `DELETE /inventory/:itemId` (discard, с query `?quantity=`).
**Если нужна экономика:** `Item.sellPrice` + `POST /inventory/sell/:itemId` (золото персонажу).
**Решение (05.09):** только discard — `DELETE /inventory/:itemId?quantity=N`; целиком надетый стак не
выбрасывается (400 «Unequip the item first»), частично — можно; ответ — полный инвентарь. Продажа — тема
[vendors/](../vendors/README.md). План — [description-discard.md](./description-discard.md), SCRUM-16.
**Бэкенд закрыт 05.09** (сессия 1) — эндпоинт, сервис, 6 unit-тестов; кнопка Discard на клиенте — сессия 2.

### 4. Class restrictions на предметах
README.md фазы упоминает проверку ограничений по классу. У Item нет
`allowedClasses`, equip не проверяет. **Решить:** режем из MVP-3 или добавляем
(колонка-массив + проверка в `InventoryService.equip`).
**Решение (05.09):** добавляем — `allowedClassCodes String[]` + проверка в equip + личный лут по классу
(фильтр DropTable до взвешивания); вынесено в [items/](../items/README.md) §2.1–2.2, SCRUM-17.

### 5. Стак экипируемых предметов — кривой edge
`@@unique([characterId, itemId])` + инкремент quantity: второй дроп того же меча
стакается, а `isEquipped` — флаг на всю запись. UI покажет «Rusty Blade ×3 (equipped)»,
бонус при этом считается один раз (`getEquipmentBonuses` игнорирует quantity).
**Решить модель:** экипируемое не стакается (отдельные записи) или UI/контракт
явно живёт с «стак надет целиком». Сейчас поведение неопределённое.
**Решение (05.09):** без миграции — `quantity` = число копий, `isEquipped` = одна копия надета, бонус
один раз; лишние копии — discard (#3). См. [items/](../items/README.md) §2.4, SCRUM-18 — закрыт 05.09.

### 6. Иконки предметов
`Item.iconUrl` везде `null` в seed. Клиент рисует глифы по type/slot — работает без
бэкенда. **Решить:** либо оставить глифы (тогда гэпа нет), либо заполнить iconUrl,
когда появится арт.

### 7. `/character/me` отдаёт только надетое
Найдено 05.09 при разборе SCRUM-15: `ACTIVE_CHARACTER_SELECT.inventory.where = { isEquipped: true }`
(`character.service.ts`), а клиент собирает и куклу, и мешок только из `/character/me`
(`HeroRemoteDataSource.getMe`; `GET /inventory` не вызывается). На реальном API мешок пуст.
**Решение (05.09):** в `getMe` инвентарь отдаётся полным списком отдельным `findMany` (include item);
`ACTIVE_CHARACTER_SELECT` для горячих путей не трогаем. Чинится в [description-discard.md](./description-discard.md), этап 1.
**Закрыто 05.09** (сессия 1) — `getMe` отдаёт полный список, тест на это есть.

## Не гэпы бэкенда (заметки для Flutter-стороны)

- `InventoryItem` entity на клиенте устарел: `atkBonus/defBonus/hpBonus` против
  9 бонусов бэкенда (str/int/sta/agi/spi/armor/mResist/physDmg/magicDmg).
  Мапперу и inspect-sheet нужен новый шейп.
- «Title» героя («Iron Vanguard») — есть только в моке; на бэкенде не задизайнен.
  Убрать из UI или выводить на клиенте из класса+уровня.
- Фильтр «accessory» в чипсах: у бэкенда `ItemType` без ACCESSORY — фильтровать
  по `slot == ACCESSORY`.
- `HeroCubit.equip/unequip/allocate` мутируют локальный стейт — переподключить на
  реальные вызовы + перезагрузка снапшота (или оптимистичное обновление).

## Порядок

1, 3 и 7 — обязательные для DoD MVP-3, бэкенд закрыт 05.09 (сессия 1), клиентская часть — сессия 2, план [description-discard.md](./description-discard.md); 2, 4, 5 — решены 05.09 и живут в теме [items/](../items/README.md).
6 — открытый вопрос (глифы по type/slot или iconUrl), кода не требует.

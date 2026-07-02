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
`GET /inventory` и `/character/me` (там `include: { item: true }`, так что подтянется само).

### 2. Consumables — тип есть, механики нет
`ItemType.CONSUMABLE` существует, но у Item нет полей эффекта (hpRestore и т.п.)
и нет endpoint'а применения.
**Сделать:** поля эффекта на Item (минимум `hpRestore Int @default(0)`),
`POST /inventory/use/:itemId` — декремент quantity (удаление при 0), применение эффекта.
**Блокер-вопрос:** текущего HP между боями в схеме нет (Character без `currentHp`) —
либо зелья вне скоупа MVP-3, либо сначала решить про персистентный HP.

### 3. Выбросить / продать предмет — endpoint'а нет
Мешок растёт бесконечно, избавиться от предмета нельзя.
**Минимум:** `DELETE /inventory/:itemId` (discard, с query `?quantity=`).
**Если нужна экономика:** `Item.sellPrice` + `POST /inventory/sell/:itemId` (золото персонажу).

### 4. Class restrictions на предметах
inventory-profile.md упоминает проверку ограничений по классу. У Item нет
`allowedClasses`, equip не проверяет. **Решить:** режем из MVP-3 или добавляем
(колонка-массив + проверка в `InventoryService.equip`).

### 5. Стак экипируемых предметов — кривой edge
`@@unique([characterId, itemId])` + инкремент quantity: второй дроп того же меча
стакается, а `isEquipped` — флаг на всю запись. UI покажет «Rusty Blade ×3 (equipped)»,
бонус при этом считается один раз (`getEquipmentBonuses` игнорирует quantity).
**Решить модель:** экипируемое не стакается (отдельные записи) или UI/контракт
явно живёт с «стак надет целиком». Сейчас поведение неопределённое.

### 6. Иконки предметов
`Item.iconUrl` везде `null` в seed. Клиент рисует глифы по type/slot — работает без
бэкенда. **Решить:** либо оставить глифы (тогда гэпа нет), либо заполнить iconUrl,
когда появится арт.

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

1–3 — обязательные для DoD MVP-3 (кроме зелий, если решим резать: тогда только 1 и 3).
4–6 — решения, не обязательно код. Пункт 5 стоит закрыть до того, как лут начнёт
дропать дубликаты экипировки.

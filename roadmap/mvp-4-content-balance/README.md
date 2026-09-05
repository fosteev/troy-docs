# MVP-4 — Content and Balance

> **Статус: инфраструктура готова, контента нет.** Seed, админка и рендер закрыты (галочки ниже), game-design и баланс не начаты. Заделы: админка контента (CRUD предметов и мобов, drop tables с `nothingWeight`, спавн-зоны, S3-загрузки), карточки классов в [classes/](../../classes/README.md), конвейер ассетов в [assets/](../assets/README.md), балансные хвосты из [polish](../mvp-2-battle-loop/polish/README.md#баланс-пересекается-с-mvp-4).

Цель: MVP должен иметь достаточно контента, чтобы проверить loop, progression и баланс.

## Продуктовый результат

Игрок может провести несколько боев подряд, получить разные предметы и поднять несколько уровней без ручного вмешательства разработчика.

## Game Design

- [ ] Минимальный набор мобов для уровней 1-10.
- [ ] Минимальные drop tables.
- [ ] Минимальный набор предметов — все 6 слотов (HEAD и ACCESSORY сейчас пустые), itemLevel 1–10,
      бюджет статов по редкости из [items/](../items/README.md) §3, классовый шмот через
      `allowedClassCodes` (SCRUM-50; ждёт миграции `item_progression`, SCRUM-62):
  - weapon;
  - armor;
  - accessory.
- [ ] Баланс XP: раскачка слишком быстрая, растянуть. Кривая линейная (`level × 100`, `REQUIRED_EXP_MULTIPLIER`), награды 18–65 XP за моба — крутить либо награды, либо кривую (кандидат: перейти с линейной на растущую), не оба сразу.
- [ ] Расхождение: `LEVEL_CAP = 30` в `libs/shared/utils/src/lib/leveling.ts`, а кап MVP по докам — 10. Закрыть в одну сторону.
- [ ] Плотность спавна: мобов на карте мало. `ZONE_CAPACITY = 8` захардкожен в `spawn-cron.service.ts` — вынести в env и поднять; смотреть вместе с кластеризацией маркеров.
- [ ] Баланс урона и выживаемости Warrior/Mage.
- [ ] Темп боя: бой слишком быстрый даже после HP ×1.5. Сначала снять TTK по срезам и записать целевой, потом крутить — по одному рычагу (HP-пул / урон / скорость атак и кулдауны), а не веером.
- [ ] Skill set для стартовых уровней.

## Backend

- [x] Seed zones.
- [x] Seed monsters. *(10 мобов в `prisma/seed.ts`; набор под 1–10 lvl — см. Game Design)*
- [x] Seed items. *(5 предметов; минимальный набор по слотам — см. Game Design)*
- [x] Drop tables.
- [x] Spawn rules для тестовой зоны.
- [x] Повторяемый dev seed для локальной разработки.

## Flutter

- [x] Иконки/спрайты для основных мобов MVP. *(рендер с бэкенда есть; сами файлы — [assets/](../assets/README.md), шаг 3)*
- [x] Отображение rarity.
- [x] Отображение level и threat моба.
- [x] Result screen с loot и XP.

## Связанные документы

- [classes.md](../../game-design/classes.md)
- [combat.md](../../game-design/combat.md)
- [leveling.md](../../game-design/leveling.md)
- [stats-and-formulas.md](../../game-design/stats-and-formulas.md)

## Документы, которые нужно добавить

- [ ] `game-design/monsters.md` — только зоны уровней, распределение и принципы поведения;
      числа конкретных мобов уже живут в карточках [mobs/](../../mobs/README.md) (источник
      правды), в monsters.md их не дублировать
- [ ] `game-design/loot-and-items.md` — правило бюджета и веса редкости из [items/](../items/README.md) §3 (SCRUM-34)
- [ ] `game-design/inventory-and-equipment.md`

## Definition of Done

- [x] Есть тестовая зона с мобами.
- [ ] Есть loot progression.
- [ ] Warrior и Mage оба playable до 10 уровня.
- [x] Seed можно пересоздать без ручных SQL-правок.

## Промт для сессии

> Самодостаточный промт: скопировать целиком в свежую сессию. Общие правила (архитектура, тесты, делегирование) — в [roadmap/README.md](../README.md).

```
Работаем в /Users/fost/Projects/troy (в основном backend troy-backend + game-design доки).

Прочитай:
- troy-docs/roadmap/mvp-4-content-balance/README.md;
- troy-docs/game-design/classes.md, combat.md, leveling.md, stats-and-formulas.md.

Game-design — дописать недостающие доки: game-design/monsters.md (только зоны/распределение/поведение — числа мобов в troy-docs/mobs/, это источник правды), loot-and-items.md, inventory-and-equipment.md.
Контент/баланс: мобы 1–10 lvl, drop tables, минимум предметов (weapon/armor/accessory), баланс XP до 10 lvl, баланс Warrior/Mage, skill set стартовых уровней.

Backend (troy-backend) — seed: zones, monsters, items, drop tables, spawn rules для тестовой зоны; повторяемый dev seed одной командой (без ручных SQL-правок).
Flutter — иконки/спрайты основных мобов, отображение rarity, level/threat, result screen с loot+XP.

Тесты: на формулы/баланс, где они есть (XP-таблица, расчёт урона/защиты, drop-роллы) — unit-тесты на детерминированную часть; smoke на воспроизводимость seed.

DoD: есть тестовая зона с мобами; loot progression; Warrior и Mage playable до 10 lvl; seed пересоздаётся одной командой; тесты формул зелёные. Коммит. Отметить фазу [x] в troy-docs/roadmap/README.md.
```

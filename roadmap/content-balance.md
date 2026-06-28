# MVP-4 — Content and Balance

Цель: MVP должен иметь достаточно контента, чтобы проверить loop, progression и баланс.

## Продуктовый результат

Игрок может провести несколько боев подряд, получить разные предметы и поднять несколько уровней без ручного вмешательства разработчика.

## Game Design

- Минимальный набор мобов для уровней 1-10.
- Минимальные drop tables.
- Минимальный набор предметов:
  - weapon;
  - armor;
  - accessory.
- Баланс XP до 10 уровня.
- Баланс урона и выживаемости Warrior/Mage.
- Skill set для стартовых уровней.

## Backend

- Seed zones.
- Seed monsters.
- Seed items.
- Drop tables.
- Spawn rules для тестовой зоны.
- Повторяемый dev seed для локальной разработки.

## Flutter

- Иконки/спрайты для основных мобов MVP.
- Отображение rarity.
- Отображение level и threat моба.
- Result screen с loot и XP.

## Связанные документы

- [classes.md](../game-design/classes.md)
- [combat.md](../game-design/combat.md)
- [leveling.md](../game-design/leveling.md)
- [stats-and-formulas.md](../game-design/stats-and-formulas.md)

## Документы, которые нужно добавить

- `game-design/monsters.md`
- `game-design/loot-and-items.md`
- `game-design/inventory-and-equipment.md`

## Definition of Done

- Есть тестовая зона с мобами.
- Есть loot progression.
- Warrior и Mage оба playable до 10 уровня.
- Seed можно пересоздать без ручных SQL-правок.

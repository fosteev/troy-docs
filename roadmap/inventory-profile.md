# MVP-3 — Profile, Inventory, Equipment

Цель: игрок должен видеть прогресс персонажа и усиливать его через предметы.

## Продуктовый результат

После боев игрок получает предметы, открывает инвентарь, экипирует предмет и видит изменение характеристик.

## Backend

- Endpoint профиля активного персонажа.
- Endpoint инвентаря.
- Equip/unequip endpoint.
- Проверка слотов экипировки.
- Проверка class restrictions, если они есть у предмета.
- Computed stats должны учитывать:
  - base stats;
  - level growth;
  - free attribute points;
  - equipment bonuses.

## Flutter

- Экран профиля персонажа:
  - имя;
  - класс;
  - уровень;
  - XP progress;
  - основные статы;
  - computed stats.
- Экран инвентаря:
  - список предметов;
  - rarity;
  - slot;
  - equipped state.
- Экран экипировки:
  - текущие слоты;
  - equip/unequip action;
  - визуальная обратная связь после изменения статов.

## Связанные документы

- [database-schema.md](../technical/database-schema.md)
- [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- [leveling.md](../game-design/leveling.md)

## Definition of Done

- Полученный в бою предмет появляется в инвентаре.
- Предмет можно экипировать и снять.
- Экипировка меняет computed stats.
- UI не требует restart для отображения изменений.

# MVP-2 — Battle Loop

Цель: бой должен быть полноценным server-driven gameplay loop, который меняет состояние персонажа.

## Продуктовый результат

Игрок начинает бой с мобом, использует доступные действия, побеждает или проигрывает, получает результат и возвращается в игровой цикл.

## Backend

- `POST /battle/start` должен проверять:
  - активного персонажа;
  - существование моба;
  - дистанцию до моба;
  - доступность моба.
- Battle state должен включать:
  - HP игрока;
  - HP моба;
  - class resource: Rage или Mana;
  - cooldowns;
  - active effects;
  - battle result.
- Реализовать skill usage.
- Реализовать autoattack timing.
- Реализовать победу:
  - XP;
  - level progression;
  - loot roll;
  - удаление или деактивация моба.
- Реализовать поражение:
  - результат боя;
  - безопасный возврат на карту.

## Flutter

- Экран боя должен получать состояние с backend.
- UI должен показывать:
  - HP игрока и моба;
  - Rage или Mana;
  - cooldowns;
  - cast/progress state;
  - результат боя.
- Нельзя рассчитывать исход боя на клиенте.
- После победы показать XP, level up и loot.
- После окончания боя вернуть пользователя на карту.

## Связанные документы

- [combat.md](../game-design/combat.md)
- [classes.md](../game-design/classes.md)
- [stats-and-formulas.md](../game-design/stats-and-formulas.md)
- [leveling.md](../game-design/leveling.md)

## Definition of Done

- Бой можно пройти от старта до результата.
- Результат боя сохраняется в backend.
- XP и loot не теряются после restart приложения.
- Клиент не содержит game-authoritative расчетов.

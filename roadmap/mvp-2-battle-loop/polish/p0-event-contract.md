# P0 — Контракт событий (backend) — [x] сделано

Фаза [battle polish](./README.md) → [MVP-2](../README.md).

Работаем в `troy-backend/apps/game-core/src/app/battle/engine/**`,
`battle.service.ts` (`toStateDto`/`appendLog`), `libs/shared/contracts`.

- `BattleEvent` расширить: `crit?: boolean`, `miss?: boolean` для `kind:'skill'`;
  `effectType?: EffectKind` для `kind:'effect'`; `target: 'player'|'monster'`;
  `damageType?: DamageType` для всех урон-событий. `kind` остаётся как есть
  (обратная совместимость клиента).
- Новые `kind`: `cast_start` (source, skillCode, `durationMs`), `cast_interrupted`
  (source, skillCode), `effect_expired` (target, effectType).
- Реализовать SLOW (×0.7 к attack speed цели, см. combat.md), ABSORB (щит
  поглощает `value` урона до истечения), BUFF (пока `value` к STR/INT — уточнить
  в combat.md). HEAL/BUFF/ABSORB применяются к **source**, не к target.
- Прокинуть в `BattleStateDto.log` и `BattleEndDto.log`; Swagger/контракты обновить.
- Ack `battle:action`: добавить `reason: 'casting'` (сейчас активный каст
  отдаётся как `on_cooldown`).
- Сид: мобам сильным скиллам дать `castTimeSec` 1.0–1.5 (`mob_stun_slam`,
  `mob_finisher_bolt`) — появляется окно для интеррапта.

DoD: `engine.spec.ts` покрывает crit/miss на скилле, `effectType` в событии,
SLOW/ABSORB/BUFF, self-target у HEAL, `cast_start`/`cast_interrupted`/
`effect_expired`; `npx nx test game-core` зелёный; Flutter-маппер терпит новые
поля (unknown kind → пропуск, не падение). Коммит в troy-backend.

**Сделано** (troy-backend `a76d8b1`, troy-flutter `0e29e1e`): контракт расширен,
SLOW/ABSORB/BUFF реализованы, HEAL/BUFF/ABSORB — на кастера, ack отдаёт
`casting`, сид получил касты мобам. Тесты: 174 backend, `npm run build` зелёный.
Замечания по ходу: `Combatant.shield` и `ActiveEffect.source/damageType`
сделаны опциональными — сессии в Redis переживают деплой; ABSORB не
стакается (новый щит заменяет старый, снимается при истечении последнего);
`amount` у урон-события — то, что реально дошло до HP (щит вычтен). Swagger
DTO лога в api-gateway нет (лог идёт только через WS) — правки не потребовалось.

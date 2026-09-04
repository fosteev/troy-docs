# Касты и сбитие — channel-скиллы и INTERRUPT

> **Статус: сделан (04.09).** Сквозная тема боёвки поверх [battle-session.md](../../technical/battle-session.md)
> v2 и паков. Решения: channel-скилл — да; INTERRUPT с локаутом — да; мобы игрока **не**
> сбивают; pushback от урона — **не делаем**. Арт для Counterspell и Arcane Missiles не
> генерировался — промты в [classes/mage.md](../../classes/mage.md).

Расширение боевой механики «как в WoW» в трёх пунктах: канальные способности (урон тиками,
срываются в любой момент), кик — эффект `INTERRUPT`, который срывает каст цели и на N секунд
запрещает ей кастовать, и два новых скилла магу — Counterspell и Arcane Missiles.

## Продуктовый результат

- Маг с 2 уровня умеет **сбить каст** моба (Counterspell): Stun Slam или Finisher Bolt не
  долетают, моб 4 с не может начать новый каст, инстантами бьёт как раньше.
- Маг с 4 уровня получает **канал** (Arcane Missiles): три залпа за 1.5 с; стан от моба срывает
  канал, уже прилетевшие залпы остаются.
- Воин сбивает как и раньше — станом (Shield Slam); ничего нового ему не даём.
- На клиенте каст-бар канала **опустошается**, а не наполняется, и размечен тиками; сорванный
  каст — «ПРЕРВАНО!» как сейчас; локаут — чип эффекта на цели.

## Ограничения (осознанные)

- **Мобы не сбивают касты игрока.** Движок это умеет (эффект симметричный, условие AI можно
  завести данными), но в контенте у мобов `INTERRUPT` нет. Возможное расширение — условие
  `target_casting` в AI, отдельным шагом.
- **Pushback от урона нет.** Против пака из трёх маг никогда не докастовал бы Meteor. Если
  понадобится — MVP-4, ограниченно (максимум 2 сдвига за каст, только от скиллов).
- Локаут — общий, а не по школам: у нас одна «школа» на сторону (PHYSICAL/MAGICAL — тип
  урона, а не школа заклинаний). Заблокированы все скиллы с `castTimeSec > 0`, инстанты —
  нет.

---

## 1. Данные

`ClassSkill` и `MonsterSkill`:

```prisma
channelTicks Int @default(0)   // 0 — обычный каст; > 0 — канал на channelTicks тиков
```

`EffectType` — новое значение `INTERRUPT`. Миграция `0018_casting_interrupt`
(`ALTER TYPE … ADD VALUE` + две колонки; PG 16, в транзакции допустимо — значение в той же
миграции не используется). Накатывать `migrate deploy`, **не** `migrate dev`.

Админка: поле «channel ticks» в обеих формах скилла, `INTERRUPT` в селекте эффекта.

## 2. Channel-скилл

- `castTimeSec` — длительность канала целиком; AGI сокращает её как у каста.
- Тики равномерны: i-й тик в `startedAt + i × (duration / ticks)`, первый — не в ноль, последний —
  в конец канала.
- **Урон** (`baseDamage + scaling`, потом crit → defense → dodge) — на **каждом** тике; событие
  `kind: 'skill'` c `channelTick: true`.
- **Эффект** (если не NONE) — **один раз, на первом тике**. Иначе DOT/BUFF стакались бы по числу
  тиков, а STUN становился бы перма-станом.
- **Ресурс** списывается целиком на старте; при срыве не возвращается («за уже прошедшие тики»
  — и за остальные тоже, как у обычного каста).
- Автоатака во время канала не бьёт (как в касте). Кулдаун ставится по окончании или срыву.
- **Срыв** (STUN или INTERRUPT) — как у каста: канал снят, прилетевшие тики остаются, штраф
  50 % КД, событие `cast_interrupted`.

Сессия (`CastState`): `{ skillCode, endsAtMs, channel?: { startedAtMs, ticks, done } }`.
DTO: `BattleCastDto.channel?: { ticks, done }` — клиент по нему рисует опустошающийся бар с
рисками. Мобы могут каналить теми же данными — AI трактует канал как каст.

## 3. INTERRUPT + локаут

Скилл с `effectType: INTERRUPT`, `effectDurationSec: N`:

- цель **кастует** (каст или канал) → каст срывается по текущим правилам (50 % КД,
  `cast_interrupted`), на цель вешается эффект `INTERRUPT` на N с (**локаут**), событие
  `effect`. `N = 0` — только срыв, без чипа;
- цель **не кастует** → ничего не происходит, но урон скилла (если есть) наносится и **КД
  уходит** — «в молоко», как в современном WoW;
- под локаутом нельзя **начать** скилл с `castTimeSec > 0`. Игрок: ack `battle:action`
  `{ accepted: false, reason: 'locked_out' }`, кнопки таких скиллов `usable: false`; моб: AI
  пропускает такие скиллы, инстанты работают.

Стан по-прежнему срывает каст сам по себе (combat.md → «Прерывание каста»).

## 4. Контент — маг

| Слот | Ур. | code | Название | Cast | CD | Mana | Урон | Эффект |
|---|---|---|---|---|---|---|---|---|
| 5 | 2 | `counterspell` | Counterspell / Контрзаклинание | 0 | 20s | 15 | — | INTERRUPT, локаут 4s |
| 6 | 4 | `arcane_missiles` | Arcane Missiles / Чародейские снаряды | канал 1.5s × 3 | 8s | 30 | 12 + INT×0.5 за тик | NONE |

Воину — без изменений (Shield Slam = его сбитие). Карточка [classes/mage.md](../../classes/mage.md)
— источник правды по числам; seed и админка — за ней.

## 5. Клиент

- `BattleCast`: `channelTicks`, `channelDone`; `BattleLogEntry.channelTick`;
  `EffectType.interrupt` («Локаут»); `BattleRejectReason.lockedOut` (тост «Каст сбит»).
- Каст-бар канала: заполнение убывает (WoW), риски по числу тиков, подпись «Канал: …».
- Хореография: тик канала — impact + цифра без выпада (`windup = 0`); первый тик может
  запустить атак-анимацию как обычный скилл.
- Лента намерений и «!» — без изменений: канал моба для клиента тот же каст.

## 6. Тесты

Backend: `engine.spec` — тики канала по времени и их число, эффект один раз, срыв канала
STUN'ом/INTERRUPT'ом (тики остались, 50 % КД), INTERRUPT по не кастующей цели (КД, нет
локаута), локаут блокирует касты и не блокирует инстанты (игрок и моб), истечение локаута;
`battle.service.spec` — ack `locked_out`, `usable:false` под локаутом; `monster-admin` /
`class-admin` — `channelTicks` проходит и валидируется (≥ 0, целое).
Flutter: маппер (`channel`, `interrupt`, `locked_out`, `channelTick`), хореограф (тик без
выпада), widget-smoke каст-бара канала.

## 7. DoD

- [x] Миграция, `channelTicks` и `INTERRUPT` в схеме, контрактах, админке.
- [x] Движок: канал тикает, срывается, ресурс/КД по правилам; INTERRUPT срывает и локаутит; локаут держит касты у обеих сторон.
- [x] Маг: Counterspell (ур. 2) и Arcane Missiles (ур. 4) в seed и карточке класса.
- [x] Клиент: канальный бар, чип локаута, тост `locked_out`, лог тиков.
- [x] combat.md и battle-session.md обновлены; `npx nx run-many -t test`, `flutter analyze && flutter test` чистые.

Накат на dev: `npm run prisma:migrate` (**не** `migrate dev`), затем `npm run prisma:seed` или
завести два скилла мага через админку по таблице раздела 4 — seed на dev не гоняют.

## Промт для сессии

```
Работаем в /Users/fost/Projects/troy (backend troy-backend + клиент troy-flutter + админка troy-admin).

Задача: channel-скиллы и сбитие каста (INTERRUPT с локаутом), магу — Counterspell и
Arcane Missiles. Спека: troy-docs/roadmap/combat-casting/README.md — прочитай целиком.
Контекст: troy-docs/technical/battle-session.md (контракт v2, паки), game-design/combat.md.

Порядок: 1) БД/контракты (миграция 0018, migrate deploy — НЕ migrate dev); 2) движок:
CastState.channel, тики, INTERRUPT/локаут, ack locked_out; 3) админка: channel ticks +
INTERRUPT; 4) seed и classes/mage.md; 5) Flutter: маппер/сущности/бар канала/чип/тост;
6) тесты по разделу 6; 7) combat.md, battle-session.md.

Backend — по troy/CLAUDE.md, Flutter — по Architecture rules из troy-flutter/CLAUDE.md.
Ветка main, коммиты без подписей ассистента. По завершении: DoD здесь, таблица в
roadmap/README.md.
```

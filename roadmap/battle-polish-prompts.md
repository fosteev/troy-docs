# Шаг 3Б (battle polish) — промты для реализации

Два промта, по одному на сессию: **A = P0 (backend)**, **B = P1 (Flutter)**.
Сначала A, после зелёного DoD и коммита — B. Источник требований —
[battle-polish.md](./battle-polish.md).

---

## Промт A — P0: контракт событий боя (troy-backend)

```
Работаем в /Users/fost/Projects/troy/troy-backend (NestJS + Nx, ветка main,
коммитим прямо в main). Дев-процессы НЕ запускать и НЕ перезапускать —
только build/test. `prisma migrate dev` НЕ использовать (дропает PostGIS-таблицы);
схема БД в этой фазе не меняется.

Задача: фаза P0 из troy-docs/roadmap/battle-polish.md — расширить контракт
боевых событий и дореализовать эффекты движка, чтобы клиент мог строить
хореографию боя. Прочитай battle-polish.md (разделы «Диагноз» и «P0») и
troy-docs/game-design/combat.md (разделы «Эффекты», «Механика каста»,
«Прерывание каста»).

Код:
- apps/game-core/src/app/battle/engine/types.ts — BattleEvent, Combatant, SkillDef
- apps/game-core/src/app/battle/engine/engine.ts — tick(): applyEffects,
  finishCasts, applyAutos, applyPlayerIntent, applyMonsterSkill, applySkill,
  applyEffect, applyDamageRoll, pushDamageEvent, interruptCastOnStun
- apps/game-core/src/app/battle/engine/formulas.ts — resolveHit (не трогать формулы)
- apps/game-core/src/app/battle/engine/engine.spec.ts, formulas.spec.ts
- apps/game-core/src/app/battle/battle.service.ts — validateSkill (~596),
  toStateDto / appendLog / recentLog, finalize → BattleEndDto
- libs/shared/contracts/src/lib/contracts.ts — BattleStateDto, BattleEndDto, BattleActionAck
- prisma/seed.ts — mobSkillRows (~455), классовые скиллы (~276–450)

Текущее состояние (факты, не перепроверяй):
- BattleEvent = { at, kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot', source, skillCode?, amount? }.
- applySkill пишет kind:'skill' и теряет crit/miss из applyDamageRoll.
- applyEffect пишет kind:'effect' с amount = effectValue и без типа эффекта;
  HEAL/BUFF/ABSORB применяются к target (противнику) — по дизайну они self.
- Движок реализует только DOT и STUN. SLOW/BUFF/ABSORB не действуют.
- Событий начала/прерывания каста и истечения эффекта нет.
- validateSkill: активный каст отдаётся как 'on_cooldown'.
- Клиент (troy-flutter) маппит неизвестный kind → 'hit' (рисует цифру урона!).

Сделать:
1. types.ts — BattleEvent:
   kind: 'hit'|'crit'|'miss'|'skill'|'effect'|'dot'|'cast_start'|'cast_interrupted'|'effect_expired'
   target: 'player'|'monster'        (обязательное, у всех событий)
   crit?: boolean; miss?: boolean    (для kind:'skill' с уроном)
   damageType?: 'PHYSICAL'|'MAGICAL' (для hit/crit/miss/skill/dot)
   effectType?: EffectKind           (для effect/effect_expired)
   durationMs?: number               (для cast_start)
   Значение kind у существующих событий не менять (обратная совместимость).
2. engine.ts:
   - applySkill: пробросить crit/miss/damageType в событие 'skill';
   - applyEffect: effectType в событие; HEAL/BUFF/ABSORB — на actor (source),
     STUN/SLOW/DOT — на target;
   - SLOW: пока активен, attackIntervalSec цели ×(1/0.7) — реализовать через
     проверку активного SLOW в canAutoAttack/при выставлении nextAutoAtMs
     (без мутации базового attackIntervalSec); value эффекта игнорируем,
     константа SLOW_FACTOR = 0.7 в formulas.ts;
   - ABSORB: Combatant.shield: number; damageCombatant сначала снимает shield,
     событие с amount = фактически прошедший урон; при истечении эффекта shield=0;
   - BUFF: value прибавляется к attrs.STR и attrs.INT на время действия
     (применять в skillRawDamage через эффективные attrs, не мутируя базу);
   - cast_start: при постановке каста (игрок в applyPlayerIntent, моб в
     applyMonsterSkill) с durationMs = castTimeSec*1000;
   - cast_interrupted: в interruptCastOnStun;
   - effect_expired: в applyEffects при удалении истёкшего эффекта
     (сейчас истёкшие просто фильтруются — добавить событие).
   - Math.random()/Date.now() внутри движка запрещены — rng только параметром.
3. battle.service.ts: validateSkill — активный каст → reason 'casting';
   BattleActionAck['reason'] расширить. Убедиться, что новые поля событий
   доходят в BattleStateDto.log и BattleEndDto.log (appendLog/recentLog не
   режут поля).
4. contracts.ts — обновить типы лога и ack; Swagger DTO в api-gateway, если
   лог описан там отдельно (grep BattleLog в apps/api-gateway).
5. seed.ts — mob_stun_slam: castTimeSec 1.2; mob_finisher_bolt: castTimeSec 1.5.
   Больше баланс не трогать.
6. troy-flutter (минимально, чтобы не сломать клиент до фазы B):
   lib/features/battle/data/mappers/battle_mapper.dart — неизвестный kind
   → запись пропускается (не 'hit'); новые kind 'cast_start'/'cast_interrupted'/
   'effect_expired' добавить в BattleLogKind (domain/entities/battle_enums.dart)
   и НЕ считать их визуальными в battle_page (_hasVisualCue). Тесты маппера
   обновить. flutter analyze / flutter test зелёные.

Тесты (engine.spec.ts, детерминированный rng):
- skill с rng→crit даёт kind:'skill', crit:true, amount = raw*2*(1-reduction);
- skill с rng→miss даёт miss:true, amount 0;
- STUN-скилл: событие effect с effectType:'STUN', target = противник;
- HEAL-скилл лечит source, не target;
- SLOW: у цели следующая автоатака через interval/0.7;
- ABSORB: щит 10, удар 15 → hp −5, amount 5; после истечения shield = 0;
- BUFF STR +10 повышает raw физического скилла на 10*scalingRatio;
- cast_start при постановке каста с durationMs; cast_interrupted при стане
  кастующего; effect_expired после истечения;
- каждое событие имеет target.
Существующие тесты не удалять — править только там, где изменился контракт.

НЕ делать: не менять формулы урона/XP/лута; не трогать map/spawn/inventory;
не добавлять новых NATS-паттернов; не менять Prisma-схему.

DoD: `npx nx test game-core` и `npx nx run-many -t test` зелёные;
`npm run build` проходит; во flutter `flutter analyze` чисто и `flutter test`
зелёный. Два коммита: troy-backend и troy-flutter (сообщения по conventional
commits). Отметить P0 в battle-polish.md как [x].
```

---

## Промт B — P1: отзывчивость и читаемость боя (troy-flutter)

```
Работаем в /Users/fost/Projects/troy/troy-flutter (Flutter, BLoC, Clean
Architecture, ветка main, коммитим прямо в main). Бэкенд НЕ запускать.
Визуальную проверку в браузере/симуляторе делает пользователь — твоя проверка:
flutter analyze, flutter test, чтение кода.

Задача: фаза P1 из troy-docs/roadmap/battle-polish.md. Прочитай её (разделы
«Диагноз» и «P1») и раздел "Architecture rules (MUST follow)" в CLAUDE.md.
Фаза P0 уже сделана: события лога несут target, crit/miss у 'skill',
effectType, damageType, и появились kind cast_start/cast_interrupted/
effect_expired; ack battle:action отдаёт reason
(on_cooldown | no_resource | stunned | casting | not_active).

Код (всё в lib/features/battle/**):
- presentation/pages/battle_page.dart (~1850 строк — прочитай целиком, это
  главный файл): _ActiveBattle, _BattleStage (диспетчер событий _onBattleActive
  ~488, _hasVisualCue/_isPlayerAction ~676, _startPlayerAction/_startMonsterAction,
  тайминги-константы вверху файла), _CombatantModel, _FloatingDamage,
  _SkillBar/_SkillButton (~1503), _CastBar, _EffectChip, _FleeButton,
  _CombatLog (мёртвый, unused_element), _BattleResult, _BattleLogLine
- presentation/bloc/battle_bloc.dart — BattleSkillPressed (~148) игнорирует ack
- data/datasources/battle_socket_datasource.dart, data/mappers/battle_mapper.dart
- domain/entities/* (freezed) — BattleLogEntry, BattleSkill, BattleEffect, BattleActionResult
- lib/shared/widgets/stat_bar.dart, sprite_sheet_animator.dart
- lib/core/socket/socket_events.dart
- assets/translations/{ru,en}.json — ключи battle.*
- test/features/battle/** — существующие тесты (battle_page_redesign_test.dart,
  data/…), стиль: flutter_test + mocktail, без golden

Факты (не перепроверяй):
- Бой real-time, всё состояние — снапшот battle:state; клиент математику не
  считает. Диспетчер сравнивает log по watermark _lastRenderedAt и запускает
  анимации для новых записей; события одного снапшота стартуют ПАРАЛЛЕЛЬНО.
- Имена скиллов есть в ClassSkillInfo (ClassRepository.getClassSkills, уже
  грузится в _BattleStage), иконки — ClassSkillInfo.icon (URL) если задан.
- Лут в BattleEndDto — только itemId (UUID) + quantity. Имена предметов —
  вне этой фазы (P3), не трогать.
- Монстровые спрайты: MonsterVisuals (idle/attack/per-skill), hit/death нет.

Сделать (в этом порядке, коммит после каждого блока):

Блок 1 — очередь событий (Opus сам, не делегировать):
- Вынести хореографию из _BattleStage в presentation/logic/battle_choreographer.dart
  (pure Dart, без виджетов): вход — список новых BattleLogEntry, выход —
  последовательность Cue {delay, type: lunge/impact/damageNumber/castStart/
  castInterrupted/effectApplied/effectExpired, actor, entry}. Правила:
  события сортируются по at, затем source==player раньше monster при равном at;
  между impact'ами минимум 120 мс; hit-stop 60 мс (пауза спрайт-анимаций) на
  каждом impact; cast_start → каст-бар сразу, без задержки.
- _BattleStage проигрывает Cue через один таймер-планировщик (заменить
  _impactTimers). Тесты хореографа с fake clock: порядок, зазоры, что
  cast_start/effect_expired не порождают damageNumber.
- Крит у kind:'skill' (crit:true) → тряска + красный, как у kind:'crit';
  miss:true → «МИМО». Эффекты с effectType STUN/SLOW/DOT — не зелёные «+N»:
  показывать подпись эффекта («Оглушение», «Замедление») цветом
  DamageNumberColors.dot; HEAL — зелёный +N; ABSORB — «Щит N» синим.

Блок 2 — отзывчивость кнопок и ack:
- BattleBloc: результат useSkill (BattleActionResult) → состояние/side-effect
  BattleActionRejected(skillCode, reason); UI: дрожь кнопки (±6 px, 200 мс) +
  SnackBar/тост 1.2 с с локализованной причиной (ключи battle.reject.*).
- Кнопка скилла: AnimatedScale 0.92 на tapDown (без ожидания сервера); для
  скиллов с castTimeSec == 0 — оптимистичный старт выпада и атак-спрайта по
  тапу; если ack accepted:false — вернуть в idle.
- _SkillButton: иконка (если есть), имя, стоимость ресурса, радиальный кулдаун
  (CustomPainter, сектор поверх иконки) вместо текста «X.Xs»; состояние
  «не хватает ресурса» (resource < cost) визуально отлично от «на кулдауне».

Блок 3 — читаемость:
- Каст-бар: имя скилла вместо кода; tween-сглаживание (AnimatedFractionallySizedBox
  или TweenAnimationBuilder), для монстра — пульс рамки модели + «!» над
  головой на cast_start; cast_interrupted → всплывающая подпись «Прервано!».
- _EffectChip: иконка (Material icon по типу) + цвет по типу + таймер; имена из
  переводов battle.effect.*.
- Полоски: числа HP/ресурса; при HP < 25 % — пульс полоски и красная
  виньетка по краям экрана (RadialGradient overlay, IgnorePointer).
- Живой лог: оживить _CombatLog — 3 последние строки над панелью скиллов,
  человеческие строки («Вы: Тяжёлый удар — 12 (крит)», «Гоблин: промах»),
  fade старых. _BattleLogLine в журнале — те же строки.
- Цифры урона привязать к модели бойца: у _CombatantModel GlobalKey, позиция
  из RenderBox вместо долей экрана в _DamageNumbersLayer.
- _FleeButton: линейный прогресс канала поверх кнопки (flee.remainingSec /
  общая длительность, длительность взять из первого снапшота с flee != null).

Блок 4 — устойчивость:
- PopScope на _BattleView: back во время BattleActive → диалог «Сбежать из боя?»
  (Да → BattleFleePressed(start) и держать до результата / Нет); при BattleEnded —
  обычный pop.
- Реконнект: подписаться на статус сокета (SocketService в lib/core/socket) —
  при disconnect в бою показать оверлей «Переподключение…» поверх сцены,
  при reconnect диспатчить BattleResumed (уже есть в bloc); BattleFailure —
  только если resume вернул accepted:false.

НЕ делать: не считать урон/исход на клиенте; не трогать map/character/auth
вне точечных правок; не добавлять аудио/VFX/арены (P2); не менять экран
результата и лут (P3); не добавлять пакетов кроме flutter_animate при
реальной необходимости (лучше без).

Тесты: хореограф (порядок/зазоры/типы cue), BattleBloc (rejected → состояние),
виджет: отказ показывает причину; кулдаун и стоимость рендерятся; PopScope
открывает диалог; эффект STUN не рисуется как хил. Существующие тесты
battle_page_redesign_test.dart сохранить зелёными (править под новые виджеты).

DoD: flutter analyze чисто; flutter test зелёный; 4 коммита по блокам
(conventional commits). Отметить P1 в battle-polish.md как [x] и Шаг 3Б в
execution-plan.md — «P0+P1 done».
```

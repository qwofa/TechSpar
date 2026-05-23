// ============================================================
// CombatSystem.cs
// 战斗系统完整演示 — Flexi 风格
//
// 数据流向总览（配合注释阅读）：
//
//   输入/触发层
//     └─► Player.LevelUp()           触发升级事件
//           └─► StatRefresh           重新计算属性（暴击率从 10% → 15%）
//
//   技能释放层
//     └─► Player.CastSkill()         释放技能（中毒/灼烧）
//           └─► BuffSystem.Apply()   应用 DOT 效果
//                 └─► DotBuff        创建持续伤害实例
//                       └─► DotTick() 每秒触发一次伤害
//
//   事件系统
//     └─► EventBus.Publish()         发布伤害事件
//           └─► 任何人可以订阅并响应（Buff系统监听DOT伤害）
//                 └─► BurnOverridePoison  灼烧覆盖中毒逻辑检查
//
// ============================================================

namespace FlexiStyleDemo
{
    // ============================================================
    // 第一部分：Stat（属性系统）
    //
    // Flexi 的 Stat 系统核心思想：
    //   一个 StatOwner（属性持有者，如玩家、敌人）持有很多 Stat（属性）。
    //   每个 Stat 有 BaseValue（基础值）和 CurrentValue（当前值）。
    //   BaseValue 是固定的，CurrentValue 由 BaseValue + 所有 StatModifier 计算得出。
    //
    // 为什么这样设计？
    //   假设有装备+100攻击力（Add）、buff+50%攻击力（Multiply）、套装效果覆盖为500（Override）
    //   正确计算顺序：先 Add，再 Multiply，最后 Override。
    //   Flexi 通过 StatModifier.Operator 枚举控制计算顺序。
    // ============================================================

    /// <summary>
    /// 属性ID枚举 — 所有角色可能拥有的属性都在这里定义。
    /// 这样做的好处：IDE 自动补全 + 编译期类型安全（不会拼错属性名）。
    /// </summary>
    public enum StatId
    {
        None = 0,
        MaxHealth = 1,    // 最大生命值
        CurrentHealth = 2, // 当前生命值
        Attack = 3,       // 攻击力
        Defense = 4,      // 防御力
        CritChance = 5,   // 暴击几率（百分比，0-100）
        CritDamage = 6,   // 暴击伤害倍率（通常是150%）
        Level = 7,        // 等级
    }

    /// <summary>
    /// 修饰符操作类型 — 决定如何将修饰符值应用到基础值上。
    ///
    /// ADD（加法）：叠加数值
    ///   例如：装备 +100 攻击力，buff +50 攻击力
    ///   最终 = BaseValue + 100 + 50
    ///
    /// MULTIPLY（乘法）：乘以倍率
    ///   例如：buff 提供 +50% 攻击力（即 ×1.5）
    ///   处于 ADD 之后执行，所以会影响所有加法叠加后的结果
    ///
    /// OVERRIDE（覆盖）：直接替换最终值
    ///   例如：套装效果强制将攻击力锁定为 500
    ///   处于所有计算的最后一步，优先级最高
    /// </summary>
    public enum ModifierOperator
    {
        ADD,       // 加法叠加
        MULTIPLY,  // 乘法叠加
        OVERRIDE,  // 直接覆盖
    }

    /// <summary>
    /// StatModifier — 单个修饰符
    ///
    /// 数据流位置：
    ///   Player 添加一个 StatModifier（例如：升级送 +5% 暴击）
    ///   → StatOwner.AppendModifier() 将其加入列表
    ///   → StatRefresh 时，ModifierHandler 遍历列表，按顺序应用
    /// </summary>
    public class StatModifier
    {
        public StatId StatId { get; }
        public float Value { get; }
        public ModifierOperator Operator { get; }

        public StatModifier(StatId statId, float value, ModifierOperator op)
        {
            StatId = statId;
            Value = value;
            Operator = op;
        }
    }

    /// <summary>
    /// 单个属性的数据结构
    ///
    /// BaseValue   — 基础值（由等级、装备等决定，不随buff变化）
    /// CurrentValue — 当前值（经过所有 Modifier 计算后的最终值）
    /// _modifiers  — 修饰符列表，每次 StatRefresh 时重新计算 CurrentValue
    /// </summary>
    public class Stat
    {
        // BaseValue 由 StatOwner 在构造或显式调用时设定，之后不会在 StatRefresh 中被修改
        public float BaseValue { get; private set; }

        // CurrentValue 是"对外暴露"的值，所有外部逻辑读的都应该是这个
        public float CurrentValue { get; private set; }

        // 修饰符列表，装载所有附加到这个属性上的效果
        private readonly List<StatModifier> _modifiers = new();

        public Stat(float baseValue)
        {
            BaseValue = baseValue;
            CurrentValue = baseValue;
        }

        /// <summary>
        /// 刷新属性值
        ///
        /// 计算公式（严格按照 Flexi 官方文档定义）：
        ///   result = BaseValue
        ///   → 遍历所有 Operator 为 ADD 的修饰符，result += modifier.Value
        ///   → 遍历所有 Operator 为 MULTIPLY 的修饰符，result *= modifier.Value
        ///   → 遍历所有 Operator 为 OVERRIDE 的修饰符，result = modifier.Value（最后一次覆盖生效）
        ///
        /// 重要：OVERRIDE 之后不会再做 ADD/MULTIPLY，它就是最终值。
        ///       这也是为什么"套装效果覆盖"能工作的原因。
        /// </summary>
        public void Refresh()
        {
            float result = BaseValue;

            // 第一轮：加法修饰符（先处理所有加法）
            foreach (var mod in _modifiers.Where(m => m.Operator == ModifierOperator.ADD))
            {
                result += mod.Value;
            }

            // 第二轮：乘法修饰符（加法结果的基础上乘以倍率）
            foreach (var mod in _modifiers.Where(m => m.Operator == ModifierOperator.MULTIPLY))
            {
                result *= mod.Value;
            }

            // 第三轮：覆盖修饰符（直接替换为指定值）
            // 注意：最后一个 OVERRIDE 会覆盖前面的，覆盖修饰符之间是"后者覆盖前者"的关系
            foreach (var mod in _modifiers.Where(m => m.Operator == ModifierOperator.OVERRIDE))
            {
                result = mod.Value;
            }

            CurrentValue = result;
        }

        /// <summary>
        /// 添加一个修饰符
        ///
        /// 数据流：
        ///   调用者（如 Player.Upgrade()）构建 StatModifier
        ///   → 调用此方法加入列表（此时不立即刷新，计算延迟到 StatRefresh）
        ///   → 后续调用 StatOwner.RefreshAll() 统一刷新所有属性
        ///
        /// 设计思想："收集"和"应用"分离
        ///   Flexi 在 Wiki 中特别强调：如果在 AddModifier 后立即 Refresh，
        ///   会导致"判断用的值"和"实际生效的值"不一致。
        ///   所以我们先收集所有修饰符，最后一次性应用。
        /// </summary>
        public void AppendModifier(StatModifier modifier)
        {
            _modifiers.Add(modifier);
        }

        /// <summary>
        /// 获取当前有效的属性值（对外接口）
        /// </summary>
        public float GetValue() => CurrentValue;

        /// <summary>
        /// 获取基础值（不受修饰符影响）
        /// </summary>
        public float GetBaseValue() => BaseValue;
    }

    /// <summary>
    /// StatOwner — 属性的持有者和容器
    ///
    /// 相当于 Flexi 中的 StatOwner 类。
    /// 所有需要属性的实体（玩家、敌人、Boss）都应该继承此类或持有其实例。
    ///
    /// 数据流：
    ///   创建 StatOwner → AddStat(StatId.CritChance, 10) 初始化基础值
    ///   → 升级/获得Buff → AppendModifier() 添加修饰符
    ///   → StatRefresh() → 每个 Stat.Refresh() 计算最终值
    /// </summary>
    public class StatOwner
    {
        // 存放所有属性的字典，以 StatId 为 key
        // 使用字典而非列表的好处：O(1) 查找，代码更清晰
        private readonly Dictionary<StatId, Stat> _stats = new();

        /// <summary>
        /// 初始化一个属性
        /// 必须在角色创建时调用一次，之后基础值不应随意改动
        /// </summary>
        public void AddStat(StatId id, float baseValue)
        {
            _stats[id] = new Stat(baseValue);
        }

        /// <summary>
        /// 获取属性值（返回当前值，即经过修饰符计算后的值）
        /// </summary>
        public float GetStat(StatId id)
        {
            return _stats.TryGetValue(id, out var stat) ? stat.GetValue() : 0f;
        }

        /// <summary>
        /// 获取基础值（不受修饰符影响）
        /// </summary>
        public float GetBaseStat(StatId id)
        {
            return _stats.TryGetValue(id, out var stat) ? stat.GetBaseValue() : 0f;
        }

        /// <summary>
        /// 添加一个修饰符到指定属性
        ///
        /// 数据流：
        ///   Player.CastSkill() → BuffSystem.Apply() → Buff.AppendModifier()
        ///   → StatOwner.AppendModifier() → 修饰符进入列表
        ///   → StatRefreshAll() → Stat.Refresh() → CurrentValue 更新
        /// </summary>
        public void AppendModifier(StatId id, StatModifier modifier)
        {
            if (_stats.TryGetValue(id, out var stat))
            {
                stat.AppendModifier(modifier);
            }
        }

        /// <summary>
        /// 刷新指定属性的当前值
        /// 调用时机会在后面的"升级"和"Buff应用"章节详细说明
        /// </summary>
        public void RefreshStat(StatId id)
        {
            if (_stats.TryGetValue(id, out var stat))
            {
                stat.Refresh();
            }
        }

        /// <summary>
        /// 刷新所有属性的当前值
        /// 通常在"批量修改完成后"统一调用，例如升级时一次性刷新所有属性
        /// </summary>
        public void RefreshAllStats()
        {
            foreach (var stat in _stats.Values)
            {
                stat.Refresh();
            }
        }
    }

    // ============================================================
    // 第二部分：Ability System（技能系统）
    //
    // Flexi 的技能系统核心：
    //   一个 Ability（技能）由多个 Node（节点）组成的有向无环图（DAG）表示。
    //   StartNode 是入口，连接到一个或多个 ProcessNode/ModifierNode。
    //   技能执行时，从 StartNode 开始，沿着连接线依次执行各节点。
    //
    // 本 Demo 简化版：
    //   我们将技能实现为一个带 Execute() 方法的类，
    //   用"事件触发"代替"节点图"，核心设计思想完全一致。
    // ============================================================

    /// <summary>
    /// 技能执行结果 — 对应 Flexi 的 FlowState
    ///   Success  — 技能成功执行完毕
    ///   Failure  — 技能执行失败（如蓝量不足、目标不存在）
    ///   Continue — 技能需要等待某些条件（如读条），暂停执行
    /// </summary>
    public enum AbilityResult
    {
        Success,
        Failure,
        Continue,
    }

    /// <summary>
    /// 技能基类 — 所有技能从这个类派生
    ///
    /// 设计思想：
    ///   - Execute() 是技能的入口，接收释放者和目标列表
    ///   - 返回 AbilityResult，调用者根据结果决定下一步
    ///   - 技能本身不关心"谁在释放"，只关心"做什么效果"
    ///   这和 Flexi 的 ProcessNode.OnExecute() 完全一致
    /// </summary>
    public abstract class Ability
    {
        // 技能名称（用于调试输出）
        public string Name { get; protected set; }

        // 技能消耗（如果有的话，如 MP、能量、怒气）
        public float Cost { get; protected set; }

        // 冷却时间（秒）
        public float Cooldown { get; protected set; }

        // 剩余冷却时间（运行时状态，不序列化为资产数据）
        private float _remainingCooldown = 0f;

        public Ability(string name)
        {
            Name = name;
        }

        /// <summary>
        /// 执行技能
        ///
        /// 数据流：
        ///   Player.CastSkill(skill)  →  检查冷却/消耗
        ///   → skill.Execute(caster, targets) → 技能具体逻辑
        ///   → 返回 AbilityResult → Player 根据结果播放动画/音效
        /// </summary>
        public abstract AbilityResult Execute(StatOwner caster, List<StatOwner> targets);

        /// <summary>
        /// 检查冷却是否就绪
        /// </summary>
        public bool IsReady()
        {
            return _remainingCooldown <= 0f;
        }

        /// <summary>
        /// 开始冷却
        /// 技能释放成功后调用
        /// </summary>
        public void StartCooldown()
        {
            _remainingCooldown = Cooldown;
        }

        /// <summary>
        /// 每帧/每秒更新冷却计时器
        /// 在 GameLoop 或 Character.Update() 中调用
        /// </summary>
        public void TickCooldown(float deltaTime)
        {
            if (_remainingCooldown > 0f)
            {
                _remainingCooldown -= deltaTime;
                if (_remainingCooldown < 0f) _remainingCooldown = 0f;
            }
        }
    }

    // ============================================================
    // 第三部分：DOT 系统（持续伤害效果）
    //
    // DOT = Damage Over Time（持续性伤害）
    //
    // 设计思路（核心）：
    //   DOT 是一个"Buff"，它附加在目标身上，每隔一段时间造成一次伤害。
    //   它不是一次性的技能效果，而是持续存在的状态。
    //
    // 覆盖机制（Burning 覆盖 Poison）的实现：
    //   每个 DotBuff 有一个 Priority（优先级）。
    //   当 Apply() 一个新 DOT 时，BuffSystem 检查目标身上是否已有 DOT：
    //     - 如果已有 DOT 的优先级 < 新 DOT 的优先级 → 移除旧 DOT，应用新 DOT
    //     - 如果已有 DOT 的优先级 >= 新 DOT 的优先级 → 不覆盖
    //
    //   例如：
    //     Poison   Priority = 1
    //     Burning  Priority = 2
    //     Burning 覆盖 Poison，因为 2 > 1
    //     反过来 Poison 不会覆盖 Burning
    // ============================================================

    /// <summary>
    /// DOT 类型枚举 — 定义 DOT 的种类
    /// 不同的 DOT 可以有不同效果（灼烧扣血/减速，中毒扣血/减治疗等）
    /// </summary>
    public enum DotType
    {
        Poison,   // 中毒
        Burning,  // 灼烧
    }

    /// <summary>
    /// DotBuff — 单个持续伤害效果实例
    ///
    /// 数据流：
    ///   Skill.Execute() → BuffSystem.Apply(new DotBuff(...))
    ///   → BuffSystem 验证优先级 → 添加到目标身上
    ///   → GameLoop 每帧 Tick() → DotBuff.Tick()
    ///   → 满足 TickInterval 后 → DotBuff.ApplyTick() → 造成伤害
    ///   → 达到 Duration 后 → DotBuff.End() → 从目标身上移除
    /// </summary>
    public class DotBuff
    {
        public DotType Type { get; }
        public int Priority { get; }
        public float TickInterval { get; }    // 每多少秒触发一次伤害
        public float TickDamage { get; }      // 每次触发造成的伤害
        public float Duration { get; }        // 总持续时间
        public float ElapsedTime { get; private set; } // 已经过的时间
        public float ElapsedSinceLastTick { get; private set; } // 距上次触发过了多久

        public DotBuff(DotType type, int priority, float tickInterval, float tickDamage, float duration)
        {
            Type = type;
            Priority = priority;
            TickInterval = tickInterval;
            TickDamage = tickDamage;
            Duration = duration;
            ElapsedTime = 0f;
            ElapsedSinceLastTick = 0f;
        }

        /// <summary>
        /// 每帧更新
        ///
        /// 数据流（当 GameLoop 调用 DotBuff.Tick(dt) 时）：
        ///   ElapsedTime += dt              → 追踪总时间
        ///   ElapsedSinceLastTick += dt     → 追踪距上次伤害过了多久
        ///   if (ElapsedSinceLastTick >= TickInterval) → 触发伤害
        ///       → DamageEvent bus  → 发布伤害事件
        ///       → ElapsedSinceLastTick = 0（重置计时器）
        ///   if (ElapsedTime >= Duration)  → 持续时间结束，标记为结束
        /// </summary>
        public void Tick(float deltaTime, StatOwner source, StatOwner target, Action<DamageEvent> onDamage)
        {
            // 更新时间
            ElapsedTime += deltaTime;
            ElapsedSinceLastTick += deltaTime;

            // 触发条件：距上次触发已超过间隔时间
            if (ElapsedSinceLastTick >= TickInterval)
            {
                // 重置计时器（注意：不清零 ElapsedTime，因为那是追踪总时长的）
                ElapsedSinceLastTick = 0f;

                // 创建并发布伤害事件
                // 注意：DOT 伤害通常不会暴击（除非特殊设计），这里按不暴击处理
                var damageEvent = new DamageEvent(
                    source: source,
                    target: target,
                    rawDamage: TickDamage,
                    isCrit: false,
                    damageType: DotTypeToDamageType(Type),
                    effectType: EffectType.DOT
                );

                // 通过回调让调用者（BuffSystem）发布事件
                // 这样 BuffSystem 可以监听自己的 DOT 伤害来做覆盖逻辑
                onDamage?.Invoke(damageEvent);
            }
        }

        /// <summary>
        /// DOT 是否已结束
        /// </summary>
        public bool IsExpired() => ElapsedTime >= Duration;

        private static DamageType DotTypeToDamageType(DotType dotType)
        {
            return dotType switch
            {
                DotType.Poison => DamageType.Poison,
                DotType.Burning => DamageType.Fire,
                _ => DamageType.Physical,
            };
        }
    }

    /// <summary>
    /// BuffSystem — Buff 管理器
    ///
    /// 核心职责：
    ///   1. 管理目标身上的所有 Buff（包括 DOT）
    ///   2. 应用新 Buff 时检查优先级（实现覆盖逻辑）
    ///   3. 每帧刷新所有 Buff 的状态
    ///
    /// 数据流：
    ///   Skill 执行 → BuffSystem.Apply(buff)
    ///   → 检查优先级 → 决定是覆盖还是忽略
    ///   → 添加到 _activeBuffs 列表
    ///   → GameLoop 每帧调用 BuffSystem.Tick()
    ///   → 遍历 _activeBuffs，调用每个 Buff 的 Tick()
    ///   → 移除已过期的 Buff
    /// </summary>
    public class BuffSystem
    {
        // 目标身上当前活跃的所有 Buff
        private readonly List<DotBuff> _activeDots = new();

        // DOT 优先级表：数字越大优先级越高，高优先级可以覆盖低优先级
        // 这是实现"灼烧覆盖中毒"的关键数据结构
        // 注意：此字段是 public static，因此可以在技能类中通过 BuffSystem.DotPriorities 访问
        public static readonly Dictionary<DotType, int> DotPriorities = new()
        {
            { DotType.Poison, 1 },   // 中毒优先级 = 1
            { DotType.Burning, 2 }, // 灼烧优先级 = 2（高于中毒）
        };

        /// <summary>
        /// 应用一个 DOT Buff 到目标
        ///
        /// 覆盖逻辑详解（"灼烧覆盖中毒"的数据流）：
        ///
        ///   场景：目标身上已有 Poison DOT（优先级 1）
        ///   动作：释放 Burning 技能（优先级 2）
        ///
        ///   数据流：
        ///     Skill_Burning.Execute()
        ///       → BuffSystem.Apply(new DotBuff(DotType.Burning, ...))
        ///         → 检查 _activeDots 中是否有 Burning（没有）
        ///         → 检查 _activeDots 中是否有 Poison（优先级 1 < 2）
        ///         → 移除 Poison DOT
        ///         → 添加 Burning DOT
        ///         → 返回 true（应用成功）
        ///
        ///   反过来：如果已有 Burning，再释放 Poison：
        ///     → 检查 Poison 优先级（1 < 2）
        ///     → 1 < 2，条件不满足 → 不覆盖，Poison 被忽略
        ///     → 返回 false（应用失败/被拒绝）
        ///
        /// </summary>
        public bool Apply(DotBuff newDot)
        {
            int newPriority = DotPriorities.GetValueOrDefault(newDot.Type, 0);

            // 遍历所有活跃 DOT，检查是否需要覆盖
            for (int i = _activeDots.Count - 1; i >= 0; i--)
            {
                var existingDot = _activeDots[i];

                // 如果已有同类型 DOT：刷新时间（重置/叠加），不重复添加
                // 这样做的好处：同类 DOT 刷新持续时间，实现"刷新而非堆叠"
                if (existingDot.Type == newDot.Type)
                {
                    // 刷新已存在的 DOT 持续时间
                    // 相当于重新开始倒计时
                    // 注意：我们不能直接修改 DotBuff 的 ElapsedTime，
                    // 这里用"移除旧DOT + 添加新DOT"的方式实现刷新
                    _activeDots.RemoveAt(i);
                    // 不在这里添加 continue，继续执行后面的逻辑来添加新 DOT
                }
                else
                {
                    // 不同类型 DOT，检查优先级
                    int existingPriority = DotPriorities.GetValueOrDefault(existingDot.Type, 0);

                    // 关键判断：新 DOT 优先级更高 → 覆盖旧 DOT
                    if (newPriority > existingPriority)
                    {
                        Console.WriteLine($"  [覆盖] {existingDot.Type} 被 {newDot.Type} 覆盖！");
                        _activeDots.RemoveAt(i); // 移除低优先级 DOT
                    }
                    // 如果 newPriority <= existingPriority，新 DOT 被拒绝，不添加
                    else
                    {
                        Console.WriteLine($"  [拒绝] {newDot.Type} 无法覆盖现有的 {existingDot.Type}（优先级不足）");
                        return false; // 应用失败
                    }
                }
            }

            _activeDots.Add(newDot);
            Console.WriteLine($"  [应用] {newDot.Type} DOT 生效！持续 {newDot.Duration} 秒，每 {newDot.TickInterval} 秒造成 {newDot.TickDamage} 点伤害。");
            return true;
        }

        /// <summary>
        /// 每帧刷新所有 DOT
        ///
        /// 数据流：
        ///   GameLoop 每帧调用 BuffSystem.Tick(deltaTime)
        ///   → 遍历 _activeDots，调用每个 DotBuff.Tick()
        ///   → Tick() 内部判断是否触发伤害，触发则调用 onDamage 回调
        ///   → 回调发布 DamageEvent 到事件总线
        ///   → 移除已过期的 DOT
        /// </summary>
        public void Tick(float deltaTime, StatOwner target, Action<DamageEvent> onDamage)
        {
            for (int i = _activeDots.Count - 1; i >= 0; i--)
            {
                var dot = _activeDots[i];

                // DotBuff.Tick() 内部会判断是否触发伤害，
                // 如果触发则调用 onDamage 回调（该回调发布 DamageEvent）
                dot.Tick(deltaTime, null, target, onDamage);

                // 如果 DOT 已过期，从列表中移除
                if (dot.IsExpired())
                {
                    Console.WriteLine($"  [结束] {dot.Type} DOT 已结束。");
                    _activeDots.RemoveAt(i);
                }
            }
        }

        /// <summary>
        /// 获取当前活跃的所有 DOT 信息（用于调试/UI显示）
        /// </summary>
        public List<(DotType type, float remainingTime)> GetActiveDots()
        {
            return _activeDots
                .Select(d => (d.Type, d.Duration - d.ElapsedTime))
                .ToList();
        }
    }

    // ============================================================
    // 第四部分：Event System（事件系统）
    //
    // Flexi 的事件系统是整个框架的"神经中枢"。
    // 所有组件之间通过事件进行通信，而非直接相互调用。
    //
    // 好处：
    //   1. 解耦：技能不需要知道是谁在释放，Buff 系统不需要知道谁在受伤
    //   2. 可扩展：新增一个"受伤时回血"的被动技能，只需要订阅事件即可
    //   3. 可调试：所有事件都经过 EventBus，便于日志和调试
    //
    // 数据流：
    //   任何地方调用 EventBus.Publish(new DamageEvent(...))
    //   → EventBus 找到所有订阅了 DamageEvent 的处理器
    //   → 依次调用每个处理器
    // ============================================================

    /// <summary>
    /// 伤害类型枚举 — 用于区分不同类型的伤害，影响最终的计算
    /// </summary>
    public enum DamageType
    {
        Physical,
        Fire,
        Poison,
        True,  // 真实伤害（无视防御）
    }

    /// <summary>
    /// 效果类型 — 区分即时伤害和持续伤害
    /// </summary>
    public enum EffectType
    {
        Instant,  // 即时伤害
        DOT,      // 持续伤害（由 DOT 系统触发）
    }

    /// <summary>
    /// 伤害事件 — 游戏中最重要的事件之一
    ///
    /// 数据流（完整生命周期）：
    ///
    ///   【产生】
    ///   Skill.Execute()
    ///     → 计算最终伤害（基础伤害 + 暴击判定）
    ///     → new DamageEvent(caster, target, damage, isCrit, ...)
    ///     → EventBus.Publish(damageEvent)
    ///
    ///   【传播】
    ///   EventBus.Publish()
    ///     → 找到所有订阅者（BuffSystem、UI层、战斗日志等）
    ///     → 依次调用 HandleDamageEvent()
    ///
    ///   【处理（BuffSystem 视角）】
    ///   BuffSystem.HandleDamageEvent()
    ///     → 读取 damageEvent.DamageType
    ///     → 如果是 DOT 伤害，检查是否触发某些特殊 buff
    ///     → （本 demo 中，DOT 伤害由 DotBuff 自己通过回调触发，不走这里）
    ///
    ///   【处理（防御计算视角）】
    ///   防御逻辑可以订阅此事件，在伤害生效前修改伤害值：
    ///     → 护盾减少伤害
    ///     → 减伤buff减少伤害
    ///     → 最终写入 target.CurrentHealth
    /// </summary>
    public class DamageEvent
    {
        public StatOwner Source { get; }          // 伤害来源（释放者）
        public StatOwner Target { get; }           // 受伤目标
        public float RawDamage { get; }           // 原始伤害值（未计算防御）
        public bool IsCrit { get; }               // 是否暴击
        public DamageType DamageType { get; }     // 伤害类型
        public EffectType EffectType { get; }     // 效果类型
        public float FinalDamage { get; private set; } // 最终伤害（经过各种计算后的值）

        public DamageEvent(StatOwner source, StatOwner target, float rawDamage,
                           bool isCrit, DamageType damageType, EffectType effectType)
        {
            Source = source;
            Target = target;
            RawDamage = rawDamage;
            IsCrit = isCrit;
            DamageType = damageType;
            EffectType = effectType;
            FinalDamage = rawDamage; // 默认等于原始伤害
        }

        /// <summary>
        /// 设置最终伤害
        /// 供事件订阅者修改（如防御系统减少伤害）
        /// </summary>
        public void SetFinalDamage(float damage)
        {
            FinalDamage = Math.Max(0f, damage); // 伤害不能为负
        }
    }

    /// <summary>
    /// 事件处理器委托 — 所有事件的处理函数都遵循这个签名
    /// </summary>
    public delegate void EventHandler<T>(T eventData) where T : class;

    /// <summary>
    /// 事件总线 — 全局事件分发中心
    ///
    /// 设计思想：
    ///   这是一个简化版的"发布-订阅"系统。
    ///   任何组件可以订阅某种类型的事件（Subscribe）
    ///   任何组件可以发布某种类型的事件（Publish）
    ///   EventBus 负责将发布的事件分发给所有订阅者。
    ///
    /// Flexi 中的对应物：EventBus ≈ FlexiCore + IFlexiEventResolver
    ///   Flexi 的 IFlexiEventResolver.ResolveEvent() 决定哪些 Ability 响应事件
    ///   我们这里的 EventBus 做得更通用，任何东西都可以订阅
    /// </summary>
    public class EventBus
    {
        // 订阅者列表，每个事件类型对应一个处理函数列表
        private readonly Dictionary<Type, List<Delegate>> _subscribers = new();

        /// <summary>
        /// 订阅某个事件类型
        ///
        /// 数据流：
        ///   BuffSystem 构造时 → EventBus.Subscribe&lt;DamageEvent&gt;(HandleDamageEvent)
        ///   → EventBus 内部记录：DamageEvent → [HandleDamageEvent]
        ///   → 后续有任何代码 Publish&lt;DamageEvent&gt;() 时，HandleDamageEvent 会被调用
        /// </summary>
        public void Subscribe<T>(EventHandler<T> handler) where T : class
        {
            var type = typeof(T);
            if (!_subscribers.ContainsKey(type))
            {
                _subscribers[type] = new List<Delegate>();
            }
            _subscribers[type].Add(handler);
        }

        /// <summary>
        /// 取消订阅
        /// </summary>
        public void Unsubscribe<T>(EventHandler<T> handler) where T : class
        {
            var type = typeof(T);
            if (_subscribers.TryGetValue(type, out var list))
            {
                list.Remove(handler);
            }
        }

        /// <summary>
        /// 发布事件 — 核心分发逻辑
        ///
        /// 数据流：
        ///   调用 Publish(new DamageEvent(...))
        ///   → 根据事件类型（T）找到所有订阅者列表
        ///   → 遍历列表，依次调用每个订阅者的处理函数
        ///   → 注意：订阅顺序可能影响结果（本 demo 不处理优先级）
        /// </summary>
        public void Publish<T>(T eventData) where T : class
        {
            var type = typeof(T);
            if (_subscribers.TryGetValue(type, out var handlers))
            {
                // 复制一份列表，避免在迭代过程中有人修改订阅列表导致异常
                foreach (var handler in handlers.ToList())
                {
                    if (handler is EventHandler<T> typedHandler)
                    {
                        typedHandler(eventData);
                    }
                }
            }
        }
    }

    // ============================================================
    // 第五部分：技能实现
    //
    // 两个核心技能：
    //   1. PoisonSkill（中毒技能） — Priority = 1
    //   2. BurningSkill（灼烧技能） — Priority = 2
    // ============================================================

    /// <summary>
    /// 中毒技能
    ///
    /// 效果：为目标附加一个 Poison DOT
    ///   - 每 1 秒造成 10 点伤害
    ///   - 持续 5 秒
    ///   - 总伤害：10 × 5 = 50 点
    /// </summary>
    public class PoisonSkill : Ability
    {
        public PoisonSkill() : base("中毒术")
        {
            Cost = 20f;      // 消耗 20 点资源
            Cooldown = 3f;   // 冷却 3 秒
        }

        public override AbilityResult Execute(StatOwner caster, List<StatOwner> targets)
        {
            // 冷却检查（由调用者在调用前检查，这里做兜底检查）
            if (!IsReady())
            {
                Console.WriteLine($"  [失败] {Name} 冷却中！");
                return AbilityResult.Failure;
            }

            // 消耗检查（省略资源系统，这里假设总是有足够的资源）
            // 真实项目中：if (!HasEnoughResource(Cost)) return AbilityResult.Failure;

            // 对每个目标应用中毒效果
            foreach (var target in targets)
            {
                // 从 caster（施法者）获取对应组件来应用 buff
                // 这里假设 caster 实现了 GetBuffSystem() 方法
                if (caster is Character character && target is Character targetChar)
                {
                    // 创建中毒 DOT
                    // DotBuff 的参数：类型、优先级、触发间隔、每次伤害、持续时间
                    var poisonDot = new DotBuff(
                        type: DotType.Poison,
                        priority: BuffSystem.DotPriorities[DotType.Poison],  // = 1
                        tickInterval: 1f,      // 每 1 秒触发一次
                        tickDamage: 10f,       // 每次 10 点伤害
                        duration: 5f           // 持续 5 秒
                    );

                    // 尝试应用到目标
                    // 返回值告知我们是否应用成功（可能被更高优先级的 DOT 覆盖而失败）
                    bool applied = targetChar.Buffs.Apply(poisonDot);

                    if (applied)
                    {
                        Console.WriteLine($"  [成功] {Name} 对目标施加了中毒效果！");
                    }
                }
            }

            // 技能释放成功，开始冷却
            StartCooldown();
            return AbilityResult.Success;
        }
    }

    /// <summary>
    /// 灼烧技能
    ///
    /// 效果：为目标附加一个 Burning DOT
    ///   - 每 1 秒造成 15 点伤害
    ///   - 持续 4 秒
    ///   - 总伤害：15 × 4 = 60 点
    ///
    /// 重要：由于 Burning 的优先级（2）高于 Poison（1），
    ///       当目标身上有中毒时释放灼烧，中毒会被覆盖！
    /// </summary>
    public class BurningSkill : Ability
    {
        public BurningSkill() : base("灼烧术")
        {
            Cost = 30f;      // 消耗更多资源（比中毒强）
            Cooldown = 5f;   // 冷却时间更长
        }

        public override AbilityResult Execute(StatOwner caster, List<StatOwner> targets)
        {
            if (!IsReady())
            {
                Console.WriteLine($"  [失败] {Name} 冷却中！");
                return AbilityResult.Failure;
            }

            foreach (var target in targets)
            {
                if (caster is Character character && target is Character targetChar)
                {
                    var burningDot = new DotBuff(
                        type: DotType.Burning,
                        priority: BuffSystem.DotPriorities[DotType.Burning],  // = 2
                        tickInterval: 1f,      // 每 1 秒触发一次
                        tickDamage: 15f,       // 每次 15 点伤害（比中毒高）
                        duration: 4f           // 持续 4 秒（比中毒短，这是平衡设计）
                    );

                    bool applied = targetChar.Buffs.Apply(burningDot);

                    if (applied)
                    {
                        Console.WriteLine($"  [成功] {Name} 对目标施加了灼烧效果！");
                    }
                }
            }

            StartCooldown();
            return AbilityResult.Success;
        }
    }

    // ============================================================
    // 第六部分：Character（角色）
    //
    // 角色是所有上述系统的整合者。
    // 一个 Character 持有：
    //   - StatOwner：属性（生命值、攻击力、暴击率等）
    //   - BuffSystem：Buff/DOT 管理
    //   - 技能列表
    //   - 事件总线订阅（用于监听受伤事件）
    // ============================================================

    /// <summary>
    /// 角色类 — 游戏实体的基类
    ///
    /// 数据流总览（在这个类中汇聚）：
    ///
    ///   【输入】
    ///   LevelUp()
    ///     → AppendModifier(StatId.CritChance, +5%)   添加暴击率修饰符
    ///     → RefreshAllStats()                        重新计算所有属性
    ///     → CurrentHealth = MaxHealth                升级时回复生命
    ///
    ///   【技能释放】
    ///   CastSkill(skillIndex)
    ///     → skill.Execute(this, targets)             执行技能逻辑
    ///     → 技能内部调用 BuffSystem.Apply()           应用 DOT
    ///     → StartCooldown()                          开始冷却
    ///
    ///   【DOT 伤害】
    ///   TakeDamage(event)
    ///     → 计算防御减伤
    ///     → CurrentHealth -= FinalDamage
    ///     → 检查死亡
    ///
    ///   【每帧刷新】
    ///   Tick(deltaTime)
    ///     → BuffSystem.Tick()                        刷新所有 DOT
    ///     → 技能冷却 TickCooldown()
    /// </summary>
    public class Character : StatOwner
    {
        public string Name { get; }
        public BuffSystem Buffs { get; }    // Buff 系统（注意：BuffSystem 是独立的，不继承 StatOwner）
        private EventBus _eventBus;         // 事件总线引用
        private readonly List<Ability> _skills = new(); // 技能列表

        public Character(string name, EventBus eventBus)
        {
            Name = name;
            _eventBus = eventBus;
            Buffs = new BuffSystem();

            // ---- 初始化属性 ----
            // 注意：AddStat 设置的是 BaseValue（基础值），不受修饰符影响
            AddStat(StatId.Level, 1);
            AddStat(StatId.MaxHealth, 100f);
            AddStat(StatId.CurrentHealth, 100f);  // 当前生命初始等于最大生命
            AddStat(StatId.Attack, 50f);
            AddStat(StatId.Defense, 10f);
            AddStat(StatId.CritChance, 10f);     // 初始暴击率 10%（升级后会增加）
            AddStat(StatId.CritDamage, 150f);    // 暴击伤害 150%

            // ---- 初始化技能 ----
            _skills.Add(new PoisonSkill());
            _skills.Add(new BurningSkill());

            // ---- 订阅受伤事件 ----
            // 这里订阅 DamageEvent，当任何伤害事件发布时会收到通知
            // 本 demo 中主要用于调试日志，真实项目中可以在这里处理受伤特效、硬直等
            _eventBus.Subscribe<DamageEvent>(HandleDamageEvent);
        }

        /// <summary>
        /// 升级！
        ///
        /// 数据流详解：
        ///
        ///   LevelUp()
        ///     ① GetStat(StatId.Level) + 1
        ///        → 当前是 1 级，+1 = 2 级
        ///
        ///     ② AppendModifier(StatId.CritChance, new StatModifier(
        ///           StatId.CritChance, 5f, ModifierOperator.ADD))
        ///        → 往 CritChance 的修饰符列表中添加一条 +5% 的修饰符
        ///        → 注意：此时 CurrentValue 还没有变化！
        ///
        ///     ③ RefreshAllStats()
        ///        → 遍历所有 Stat，调用 Stat.Refresh()
        ///        → CritChance.Refresh() 执行计算：
        ///            result = BaseValue(10) + Modifiers(5) = 15
        ///        → CurrentValue 更新为 15
        ///
        ///     ④ Console.WriteLine($"暴击率提升到 {GetStat(StatId.CritChance)}%");
        ///        → 输出"暴击率提升到 15%"
        ///
        ///     ⑤ MaxHealth 增加（升级加血）
        ///        AppendModifier → RefreshAllStats
        ///        CurrentHealth = MaxHealth（升级时回复生命）
        /// </summary>
        public void LevelUp()
        {
            int currentLevel = (int)GetStat(StatId.Level);
            int newLevel = currentLevel + 1;

            Console.WriteLine($"\n{'='} {Name} 升级！{currentLevel} → {newLevel}");

            // 设置新等级
            // 注意：这里用 AppendModifier 而非直接 SetBaseValue，
            // 目的是保持和暴击率修饰符一致的设计——所有数值变化都通过修饰符系统
            // 不过更简单的做法是直接修改 BaseValue：
            // GetStatObject(StatId.Level).BaseValue = newLevel;
            // 两种方式都可以，关键是和团队约定
            AppendModifier(StatId.Level, new StatModifier(StatId.Level, 1f, ModifierOperator.ADD));
            RefreshStat(StatId.Level);

            // 暴击率 +5%（这是升级的核心收益之一）
            // 数据流：AppendModifier → 添加到修饰符列表 → RefreshStat → CurrentValue = Base(10) + 5 = 15
            AppendModifier(StatId.CritChance, new StatModifier(StatId.CritChance, 5f, ModifierOperator.ADD));
            RefreshStat(StatId.CritChance);
            Console.WriteLine($"  暴击率提升到 {GetStat(StatId.CritChance)}% （基础 10%，升级加成 +{(newLevel - 1) * 5}%）");

            // 最大生命值 +20
            AppendModifier(StatId.MaxHealth, new StatModifier(StatId.MaxHealth, 20f, ModifierOperator.ADD));
            RefreshStat(StatId.MaxHealth);

            // 升级时回满血
            // 注意：CurrentHealth 是单独的属性，我们需要手动更新它
            // 真实项目中 CurrentHealth 通常有上下限保护
            AppendModifier(StatId.CurrentHealth,
                new StatModifier(StatId.CurrentHealth, GetStat(StatId.MaxHealth), ModifierOperator.OVERRIDE));
            RefreshStat(StatId.CurrentHealth);

            Console.WriteLine($"  最大生命提升到 {GetStat(StatId.MaxHealth)}，当前生命已回满。");
        }

        /// <summary>
        /// 释放技能
        ///
        /// 数据流：
        ///   CastSkill(0)  // 释放第一个技能（中毒）
        ///     → 检查冷却
        ///     → skill.Execute(this, [enemy])  // 传入施法者和目标列表
        ///       → Skill.Execute() 内部：
        ///           → new DotBuff(DotType.Poison, ...)
        ///           → enemy.Buffs.Apply(dotBuff)
        ///             → BuffSystem 检查优先级
        ///             → 添加到 _activeDots 列表
        ///           → skill.StartCooldown()
        ///     → 返回执行结果
        /// </summary>
        public void CastSkill(int skillIndex, List<Character> targets)
        {
            if (skillIndex < 0 || skillIndex >= _skills.Count)
            {
                Console.WriteLine($"  [错误] 技能索引 {skillIndex} 不存在！");
                return;
            }

            var skill = _skills[skillIndex];

            // 冷却检查
            if (!skill.IsReady())
            {
                Console.WriteLine($"  [跳过] {skill.Name} 冷却中...");
                return;
            }

            Console.WriteLine($"\n{Name} 释放【{skill.Name}】！");

            // 执行技能（将 Character 转型为 StatOwner 传递，因为技能只关心属性不关心角色）
            var statTargets = targets.Cast<StatOwner>().ToList();
            skill.Execute(this, statTargets);
        }

        /// <summary>
        /// 受到伤害
        ///
        /// 数据流：
        ///   DamageEvent 被发布
        ///   → EventBus 分发给所有订阅者
        ///   → Character.HandleDamageEvent() 被调用
        ///   → 从事件中读取 FinalDamage（此时可能已被防御系统修改）
        ///   → CurrentHealth -= FinalDamage
        ///   → 如果 CurrentHealth <= 0 → 死亡
        /// </summary>
        private void HandleDamageEvent(DamageEvent evt)
        {
            // 忽略非本角色的伤害事件
            if (evt.Target != this) return;

            // 从事件中获取最终伤害值（防御计算在发布事件前完成）
            float damage = evt.FinalDamage;

            // 扣除生命值
            // 注意：这里用 OVERRIDE 来设置当前生命，而不是直接赋值
            // 这是为了保持和修饰符系统的一致性
            // 真实项目中，你可能会直接写：_currentHealth -= damage;
            float currentHealth = GetStat(StatId.CurrentHealth);
            float newHealth = Math.Max(0f, currentHealth - damage);

            AppendModifier(StatId.CurrentHealth,
                new StatModifier(StatId.CurrentHealth, newHealth, ModifierOperator.OVERRIDE));
            RefreshStat(StatId.CurrentHealth);

            string critText = evt.IsCrit ? " [暴击！]" : "";
            string dotText = evt.EffectType == EffectType.DOT ? $" [{evt.DamageType}伤害]" : "";

            Console.WriteLine($"  {critText}{dotText} {Name} 受到 {damage:F1} 点伤害，生命剩余 {GetStat(StatId.CurrentHealth):F1}/{GetStat(StatId.MaxHealth)}");

            // 死亡检查
            if (GetStat(StatId.CurrentHealth) <= 0)
            {
                Console.WriteLine($"  [死亡] {Name} 倒下了！");
            }
        }

        /// <summary>
        /// 造成伤害（给外部调用的伤害接口）
        ///
        /// 这是主动伤害（如普攻、技能直接伤害）的入口。
        /// DOT 伤害不走这个方法，而是通过 DotBuff.Tick() → 回调 → EventBus.Publish()
        ///
        /// 数据流：
        ///   DealDamage(target, 50f)
        ///     → 获取攻击者攻击力（50）
        ///     → 暴击判定：Random < CritChance → isCrit = true
        ///     → 如果暴击：damage *= CritDamage / 100（×1.5）
        ///     → Defense 计算：finalDamage = damage * (1 - defenseRate)
        ///     → new DamageEvent(source, target, damage, isCrit, ...)
        ///     → EventBus.Publish(event) → 所有订阅者收到通知
        /// </summary>
        public void DealDamage(Character target, float baseDamage, DamageType damageType)
        {
            // 暴击判定
            bool isCrit = UnityEngine.Random.value * 100f < GetStat(StatId.CritChance);
            float damage = baseDamage;

            if (isCrit)
            {
                damage *= GetStat(StatId.CritDamage) / 100f;  // 暴击伤害倍率
            }

            // 防御减伤
            float defenseRate = target.GetStat(StatId.Defense) / 100f;
            damage *= (1f - defenseRate);

            // 创建并发布伤害事件
            var evt = new DamageEvent(
                source: this,
                target: target,
                rawDamage: damage,
                isCrit: isCrit,
                damageType: damageType,
                effectType: EffectType.Instant
            );

            // 防御系统可以在事件发布前修改 FinalDamage（本 demo 省略此步骤，直接发布）
            _eventBus.Publish(evt);
        }

        /// <summary>
        /// 每帧更新
        ///
        /// 数据流：
        ///   GameLoop 每帧调用 Character.Tick(deltaTime)
        ///   → BuffSystem.Tick(deltaTime) → 刷新所有 DOT
        ///     → 每个 DOT.Tick() 检查是否触发伤害
        ///     → 如果触发：回调 onDotDamage → EventBus.Publish(DamageEvent)
        ///     → Character.HandleDamageEvent() 收到事件 → 扣除生命
        ///   → 所有技能 TickCooldown(deltaTime)
        /// </summary>
        public void Tick(float deltaTime)
        {
            // 刷新所有 DOT
            // 注意：DOT 伤害通过回调发布到 EventBus，而不是直接在这里扣除生命
            // 这样保证了事件系统的统一性——所有伤害都走事件总线
            Buffs.Tick(deltaTime, this, (damageEvent) =>
            {
                _eventBus.Publish(damageEvent);
            });

            // 刷新所有技能冷却
            foreach (var skill in _skills)
            {
                skill.TickCooldown(deltaTime);
            }
        }

        /// <summary>
        /// 获取当前状态摘要（调试用）
        /// </summary>
        public string GetStatusSummary()
        {
            var dots = Buffs.GetActiveDots();
            string dotInfo = dots.Count == 0
                ? "无"
                : string.Join(", ", dots.Select(d => $"{d.type}({d.remainingTime:F1}s)"));

            return $"[{Name}] Lv.{GetStat(StatId.Level)} HP {GetStat(StatId.CurrentHealth):F0}/{GetStat(StatId.MaxHealth)} " +
                   $"ATK {GetStat(StatId.Attack)} DEF {GetStat(StatId.Defense)} " +
                   $"Crit {GetStat(StatId.CritChance)}% | DOT: {dotInfo}";
        }
    }

    // ============================================================
    // 第七部分：GameLoop（游戏主循环）
    //
    // 模拟 Unity 的 Update 循环
    // 负责驱动所有角色的 Tick()
    // ============================================================

    public class GameLoop
    {
        private readonly List<Character> _characters = new();
        private float _elapsedTime = 0f;

        public void AddCharacter(Character character)
        {
            _characters.Add(character);
        }

        /// <summary>
        /// 运行游戏循环
        ///
        /// 数据流：
        ///   while (true)
        ///     → _elapsedTime += deltaTime
        ///     → foreach character.Character.Tick(deltaTime)
        ///       → BuffSystem.Tick()
        ///         → DotBuff.Tick()
        ///           → 检查是否触发伤害
        ///           → 触发 → EventBus.Publish(DamageEvent)
        ///             → HandleDamageEvent → 扣除生命
        ///       → 技能冷却更新
        ///     → 等待 deltaTime（模拟帧间隔）
        ///     → 检查退出条件（所有敌人死亡或时间到达）
        /// </summary>
        public void Run(float duration, float deltaTime = 0.1f)
        {
            Console.WriteLine($"\n游戏开始！持续 {duration} 秒\n");

            while (_elapsedTime < duration)
            {
                _elapsedTime += deltaTime;

                foreach (var character in _characters)
                {
                    character.Tick(deltaTime);
                }

                // 每秒输出一次状态
                if (Math.Abs(_elapsedTime % 1f) < deltaTime / 2f)
                {
                    Console.WriteLine($"\n--- 时间 {_elapsedTime:F0}s ---");
                    foreach (var c in _characters)
                    {
                        Console.WriteLine($"  {c.GetStatusSummary()}");
                    }
                }

                // 简单延迟模拟
                Thread.Sleep((int)(deltaTime * 10)); // 加速运行（1秒游戏时间=100ms真实时间）
            }

            Console.WriteLine("\n游戏结束！");
        }
    }

    // ============================================================
    // 第八部分：程序入口 & 完整战斗演示
    //
    // 演示流程：
    //   1. 创建玩家和敌人
    //   2. 玩家升级 → 暴击率从 10% 提升到 15%
    //   3. 玩家释放中毒 → 敌人身上有中毒 DOT
    //   4. 玩家释放灼烧 → 中毒被灼烧覆盖，敌人身上只有灼烧 DOT
    //   5. 观察 DOT 的伤害记录
    // ============================================================

    public class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("=".PadRight(60, '='));
            Console.WriteLine("  Unity 战斗系统演示 - Flexi 风格");
            Console.WriteLine("  主题：升级系统 / DOT 覆盖机制 / 事件总线");
            Console.WriteLine("=".PadRight(60, '='));

            // ---- 创建事件总线 ----
            // EventBus 是全局唯一的，所有组件共享同一个实例
            // 这保证了任何组件发布的事件都能被任何其他组件收到
            var eventBus = new EventBus();

            // ---- 创建角色 ----
            var player = new Character("玩家", eventBus);
            var enemy = new Character("哥布林", eventBus);

            // ---- 游戏主循环 ----
            var game = new GameLoop();
            game.AddCharacter(player);
            game.AddCharacter(enemy);

            // ==========================================================
            // 阶段 1：初始状态
            // ==========================================================
            Console.WriteLine("\n## 阶段 1：初始状态");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine(player.GetStatusSummary());
            Console.WriteLine(enemy.GetStatusSummary());
            Console.WriteLine("\n初始暴击率：10%（基础值）");

            // ==========================================================
            // 阶段 2：升级
            // ==========================================================
            Console.WriteLine("\n## 阶段 2：玩家升级");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine("调用 player.LevelUp()...");
            Console.WriteLine("数据流向：AppendModifier(+5% Crit) → RefreshStat → CurrentValue = 15%");
            player.LevelUp();

            // ==========================================================
            // 阶段 3：释放中毒技能
            // ==========================================================
            Console.WriteLine("\n## 阶段 3：释放中毒技能");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine("调用 player.CastSkill(0, [enemy])...");
            Console.WriteLine("数据流向：PoisonSkill.Execute() → new DotBuff(Poison) → Buffs.Apply() → 加入 _activeDots 列表");
            player.CastSkill(0, new List<Character> { enemy });

            // 运行 2 秒，观察中毒伤害
            Console.WriteLine("\n--- 运行 2 秒（观察中毒伤害）---");
            RunSeconds(game, 2f, player, enemy);

            // ==========================================================
            // 阶段 4：释放灼烧技能（关键：覆盖中毒！）
            // ==========================================================
            Console.WriteLine("\n## 阶段 4：释放灼烧技能（覆盖中毒）");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine("调用 player.CastSkill(1, [enemy])...");
            Console.WriteLine("数据流向：BurningSkill.Execute() → Buffs.Apply()");
            Console.WriteLine("  → 检查 Burning 优先级（2）> Poison 优先级（1）");
            Console.WriteLine("  → 移除 Poison DOT → 添加 Burning DOT");
            Console.WriteLine("  → 中毒被灼烧覆盖！");
            player.CastSkill(1, new List<Character> { enemy });

            // ==========================================================
            // 阶段 5：再次尝试释放中毒（会被拒绝！）
            // ==========================================================
            Console.WriteLine("\n## 阶段 5：再次释放中毒（优先级不足，被拒绝）");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine("由于 Burning（优先级 2）> Poison（优先级 1），");
            Console.WriteLine("新的 Poison DOT 无法覆盖现有的 Burning DOT");
            player.CastSkill(0, new List<Character> { enemy });

            // 运行 3 秒，观察灼烧伤害
            Console.WriteLine("\n--- 运行 3 秒（观察灼烧伤害，无中毒）---");
            RunSeconds(game, 3f, player, enemy);

            // ==========================================================
            // 阶段 6：再次升级，暴击率提升
            // ==========================================================
            Console.WriteLine("\n## 阶段 6：再次升级");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine("累积升级加成：基础 10% + 5% + 5% = 20%");
            player.LevelUp();

            // ==========================================================
            // 最终状态
            // ==========================================================
            Console.WriteLine("\n## 最终状态");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine(player.GetStatusSummary());
            Console.WriteLine(enemy.GetStatusSummary());

            Console.WriteLine("\n" + "=".PadRight(60, '='));
            Console.WriteLine("  演示结束");
            Console.WriteLine("=".PadRight(60, '='));
        }

        /// <summary>
        /// 模拟运行指定秒数的游戏时间
        /// </summary>
        private static void RunSeconds(GameLoop game, float seconds, params Character[] characters)
        {
            float deltaTime = 0.1f; // 每步 0.1 秒（每秒 10 步）
            float elapsed = 0f;

            while (elapsed < seconds)
            {
                elapsed += deltaTime;
                foreach (var c in characters)
                {
                    c.Tick(deltaTime);
                }
            }
        }
    }
}

// ================================================================
// 附加：Unity 随机数适配（让代码在 C# 控制台和 Unity 中都能运行）
// ================================================================
namespace UnityEngine
{
    public static class Random
    {
        private static readonly System.Random _rng = new();
        public static float value => (float)_rng.NextDouble();
    }
}

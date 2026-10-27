# 规范评审 POC 清单

POC 分两部分：

- **A. 门禁 PoC（bot-gate-lab）**：按该仓库契约，每个 lint 一个 case（`cases/<rustc|clippy>/<lint>/`），`case.toml` 的 `id` 为 lint ID、`rule` 为条款编号；漏报以 `pass/<场景>/` 表达，断言目标 lint 0 次命中。运行 `./scripts/validate-guideline.sh`，已在 rustc 1.97.0 上全部通过（48 项检查）。
- **B. 学习用例（playground）**：按条款组织（`cases/guideline/<条款>/<场景>/`），除 lint 实测外，还包括运行时语义、示例能否编译、版本差异，并回显编译器原始输出。运行 `python scripts/validate-guideline.py`，结果来自 rustc 1.89.0 实测。

---

## A. 门禁 PoC（bot-gate-lab）

非触发对照样例：`边界` 表示 lint 有意豁免且与规范一致；`漏报` 表示规范要求覆盖但 lint 不报。

### G.CTF.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::unnecessary_unwrap` | `cases/clippy/unnecessary-unwrap` | 1 | — | 1.89 只识别局部变量，对结构体字段（如 self.v）先判断后 unwrap 不报；1.97 起支持。 |

### G.CTF.02

无对应 lint（检测能力：不支持），无 PoC。

### G.CTF.03

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::infinite_loop` | `cases/clippy/infinite-loop` | 1 | `never-return`（边界）：函数返回类型为 `!` 时豁免，与规范「有意常驻的循环声明为 `-> !`」一致。<br>`panic-exit`（漏报）：以 panic 为唯一出口的循环被视为可退出，但不属于规范要求的安全退出。 | 任何返回 `!` 的调用（panic!、process::exit）都被视为出口。<br>1.89 中未 await 的 async 块内的常驻循环会被误报，1.97 起豁免。 |
| `clippy::while_immutable_condition` | `cases/clippy/while-immutable-condition` | 1 | — | — |
| `unconditional_recursion` | `cases/rustc/unconditional-recursion` | 1 | `unreachable-base`（漏报）：n > 0 时永不终止，但存在终止分支，不报。 | 只要存在语法上的终止分支就不报，即使该分支实际不可达。 |

### G.EXP.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::absurd_extreme_comparisons` | `cases/clippy/absurd-extreme-comparisons` | 1 | — | — |
| `clippy::bad_bit_mask` | `cases/clippy/bad-bit-mask` | 2 | — | 掩码来自构建配置生成的常量、在某些配置下为 0 时同样报警（`&-masking with zero`），需按规范【例外】局部 allow。 |
| `clippy::eq_op` | `cases/clippy/eq-op` | 1 | — | — |
| `clippy::impossible_comparisons` | `cases/clippy/impossible-comparisons` | 1 | — | — |
| `clippy::overly_complex_bool_expr` | `cases/clippy/overly-complex-bool-expr` | 1 | — | 1.89 属 correctness（默认 deny），1.97 降为 pedantic，升级工具链后需显式开启。 |
| `unused_comparisons` | `cases/rustc/unused-comparisons` | 1 | — | — |

### G.EXP.02

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::precedence` | `cases/clippy/precedence` | 1 | `negative-literal-method`（漏报）：一元负号接方法调用不报，需 rustc ambiguous_negative_literals。<br>`bit-shift-mix`（漏报）：位运算与移位混用不报，需 clippy::precedence_bits。 | 1.89 起不再检查一元负号接方法调用，由 rustc 的 ambiguous_negative_literals 负责。<br>1.86 起位运算与移位混用拆到 clippy::precedence_bits。<br>`&&` 与 `||` 混用不在检查范围。 |
| `clippy::precedence_bits` | `cases/clippy/precedence-bits` | 1 | — | — |
| `ambiguous_negative_literals` | `cases/rustc/ambiguous-negative-literals` | 1 | — | — |

### G.FUD.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::large_types_passed_by_value` | `cases/clippy/large-types-passed-by-value` | 1 | `pub-fn-default`（漏报）：pub 函数默认被跳过（avoid-breaking-exported-api = true）。<br>`non-copy`（漏报）：非 Copy 的大结构体按值传入不报。 | 只检查 Copy 类型；非 Copy 的大类型需 clippy::needless_pass_by_value，且仅在参数未被消费时报。<br>默认 avoid-breaking-exported-api = true，跳过导出 API；在 clippy.toml 中设为 false 后可检查。 |
| `clippy::needless_pass_by_value` | `cases/clippy/needless-pass-by-value` | 1 | — | — |

### G.FUD.02

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::let_underscore_must_use` | `cases/clippy/let-underscore-must-use` | 1 | — | — |
| `clippy::must_use_candidate` | `cases/clippy/must-use-candidate` | 1 | — | — |
| `clippy::unused_result_ok` | `cases/clippy/unused-result-ok` | 1 | — | — |
| `unused_must_use` | `cases/rustc/unused-must-use` | 3 | `let-underscore`（漏报）：`let _ =` 显式丢弃，不报，需 clippy::let_underscore_must_use。<br>`ok-discard`（漏报）：`.ok();` 丢弃 Result，不报，需 clippy::unused_result_ok。<br>`option-wrapped`（漏报）：must_use 类型包在 Option 中返回，不报，没有 lint 能覆盖。 | 只检查调用方直接忽略；`let _ =`、`.ok();` 不报。<br>#[must_use] 标在类型上时，包一层 Option 后不再生效。 |

### G.TRA.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::derive_ord_xor_partial_ord` | `cases/clippy/derive-ord-xor-partial-ord` | 1 | `derived-eq-manual-ord`（漏报）：derive 的 PartialEq 比较全部字段、Ord 只比较 uid，a != b 时 cmp 仍可能为 Equal，但不报。 | 只检查 Ord 与 PartialOrd 一个 derive、一个手写；不检查排序与相等性（PartialEq/Eq）是否一致。 |
| `clippy::derived_hash_with_manual_eq` | `cases/clippy/derived-hash-with-manual-eq` | 1 | `both-manual`（漏报）：PartialEq 只比较 uid、Hash 还计入 name，口径不一致但不报。 | 只在 derive(Hash) 与手写 PartialEq 混用时介入，两边都手写时不检查口径是否一致。 |
| `clippy::non_canonical_partial_ord_impl` | `cases/clippy/non-canonical-partial-ord-impl` | 1 | — | 只检查 partial_cmp 是否写成 Some(self.cmp(other))，不检查 Ord 与 PartialEq 的口径是否一致。 |

### G.TRA.02

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::from_over_into` | `cases/clippy/from-over-into` | 1 | — | — |

### G.ERR.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::expect_used` | `cases/clippy/expect-used` | 1 | — | — |
| `clippy::panic` | `cases/clippy/panic` | 1 | — | — |
| `clippy::unwrap_used` | `cases/clippy/unwrap-used` | 1 | `expect-call`（漏报）：expect 不在检查范围，需 clippy::expect_used。<br>`unwrap-or-else-panic`（漏报）：闭包中 panic 与 unwrap 等价，但不报，需 clippy::panic 兜底。 | 规范允许的「已提前校验」场景同样报警，需用 #[expect(clippy::unwrap_used, reason = "...")] 局部豁免。<br>测试代码默认也报，需在 clippy.toml 中设置 allow-unwrap-in-tests = true。 |

### G.MOD.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::enum_glob_use` | `cases/clippy/enum-glob-use` | 1 | — | — |
| `clippy::wildcard_imports` | `cases/clippy/wildcard-imports` | 1 | `prelude-and-reexport`（边界）：prelude::* 与 pub use 再导出默认豁免，与规范例外一致。<br>`test-module`（漏报）：测试模块中的 use std::collections::* 也不报。<br>`enum-glob`（漏报）：枚举变体通配导入不报，需 clippy::enum_glob_use。 | cfg(test) 编译时整体跳过，测试模块内任何通配导入都不报。<br>`use Enum::*` 由 clippy::enum_glob_use 负责。 |

### G.MAC.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::macro_metavars_in_unsafe` | `cases/clippy/macro-metavars-in-unsafe` | 1 | `hardcoded-unsafe-call`（漏报）：宏把固定的 unsafe 调用包装成 safe fn，不经元变量，不报。<br>`proc-macro`（漏报）：过程宏把调用方表达式放进 unsafe 块，不报。 | 默认只检查导出宏；私有宏需 warn-unsafe-macro-metavars-in-private-macros = true（本 case 已开启）。<br>只检查实际被调用过的宏。<br>宏内写死、不经元变量的 unsafe 调用不报。<br>过程宏生成的 unsafe 块不在检查范围。 |
| `clippy::undocumented_unsafe_blocks` | `cases/clippy/undocumented-unsafe-blocks` | 1 | — | — |

### P.MAC.DCL.01

| lint | case | 期望 | pass 场景（0 次命中） | 覆盖限制 |
| --- | --- | :---: | --- | --- |
| `clippy::crate_in_macro_def` | `cases/clippy/crate-in-macro-def` | 1 | `bare-path`（漏报）：导出宏使用裸路径，跨 crate 调用会找不到 helper，但不报。 | 只检查导出宏中的 `crate::`；宏内裸路径（如 helper()、helper!()）不报。 |

### G.MAC.DCL.01

无对应 lint（检测能力：不支持），无 PoC。

### P.MAC.PRO.01

无对应 lint（检测能力：不支持），无 PoC。

---

## B. 学习用例（playground）

- 实跑工具链：`rustc 1.89.0 (29483883e 2025-08-04)`，`clippy 0.1.89 (29483883ee 2025-08-04)`
- lint 存在性与分组基线：rustc / Clippy **1.89.0** 源码（rust-lang/rust@1.89.0、rust-clippy@rust-1.89.0）
- 结果：64/64 PASS（PASS 表示实测结果与 case.toml 中声明的预期完全一致，预期本身可以是 0 次命中或编译失败）
- 运行：`python scripts/validate-guideline.py [过滤串]`，原始 Cargo JSON 在 `artifacts/guideline/logs/`

类别说明：**命中**＝lint 能检出；**漏报**＝条款要求覆盖但 lint 不报；**误报 / 误报风险**＝条款允许或意图正常但 lint 报警；**边界**＝lint 的豁免与条款一致；**语义验证**＝验证条款描述的运行时行为；**示例校验**＝验证原文或修订稿示例能否编译、行为是否正确；**版本差异**＝1.89 与实跑版本行为不同，结论来自源码比对。

「*」表示在 `clippy::all + pedantic + nursery` 下该 fixture 的全部 lint 告警数（已排除与本条无关的噪声 lint）。

### G.CTF.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.CTF.01-01 | 命中 | is_some() 后 unwrap() 被 unnecessary_unwrap 命中<br>`cases/guideline/g-ctf-01/g-ctf-01-01` | `clippy::unnecessary_unwrap` 1→1 | 原文第一个反例（Option 判断后取值）可被 clippy::unnecessary_unwrap 检出，该 lint 属 complexity 组、默认 warn。 | PASS |
| G.CTF.01-02 | 漏报 | is_empty() 后下标取值无任何 lint 命中<br>`cases/guideline/g-ctf-01/g-ctf-01-02` | `clippy::unnecessary_unwrap` 0→0<br>`*` 0→0 | 原文第二个反例（切片判空后下标取值）在 all+pedantic+nursery 下零告警；只有 restriction 组的 indexing_slicing 会报，但它不区分是否已判空，对本条而言粒度不对。 | PASS |
| G.CTF.01-03 | 版本差异 | 对结构体字段先判断后 unwrap<br>`cases/guideline/g-ctf-01/g-ctf-01-03` | `clippy::unnecessary_unwrap` 0→0 | Rust/Clippy 1.89.0 不命中字段接收者，属于漏报；1.97 起才能命中。<br>**版本说明**：1.89.0 的 unwrap.rs 仅通过 path_to_local 识别局部变量，字段接收者（self.v）不在检测范围，即 1.89 下为漏报；1.97 新增 FieldIdx 追踪后可命中（源码比对）。 | PASS |
| G.CTF.01-04 | 示例校验 | 原文反例 `let list: &[f32] = vec![1.23];` 无法编译<br>`cases/guideline/g-ctf-01/g-ctf-01-04` | 编译失败：mismatched types | 原文反例类型不匹配（Vec<f32> 不能直接赋给 &[f32]），需改为 `&[1.23]` 或 `&vec![1.23]`。 | PASS |
| G.CTF.01-05 | 示例校验 | 修订稿正例可编译且零告警<br>`cases/guideline/g-ctf-01/g-ctf-01-05` | `*` 0→0 | 修订稿正例补齐了 opt/list/index 的上下文，可独立编译。 | PASS |

### G.CTF.02

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.CTF.02-01 | 语义验证 | 或模式 + Guard：Guard 被执行 2 次，没有针对副作用的 lint<br>`cases/guideline/g-ctf-02/g-ctf-02-01` | `*` 0→0<br>输出：`add 1 / add 1 / final=2` | 原文反例行为属实：Guard 对或模式中每个匹配成功的子模式各执行一次。all+pedantic+nursery 只产生与副作用无关的 unnested_or_patterns 风格告警；排除该噪声后，本条相关 lint 为零。 | PASS |
| G.CTF.02-02 | 语义验证 | 单一模式 + Guard：Guard 只执行 1 次（对照组）<br>`cases/guideline/g-ctf-02/g-ctf-02-02` | 编译通过<br>输出：`add 1 / final=1` | 同样的值与 Guard，去掉 `\|` 后 Guard 只执行 1 次。可见多次执行来自或模式；原文「匹配几次就会执行 Guard 几次」未点明这一前提，需修订。 | PASS |

### G.CTF.03

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.CTF.03-01 | 命中 | 无退出条件的 loop 被 infinite_loop 命中<br>`cases/guideline/g-ctf-03/g-ctf-03-01` | `clippy::infinite_loop` 1→1 | 原文 lint 名应写全为 clippy::infinite_loop（restriction 组，需显式开启）。 | PASS |
| G.CTF.03-02 | 边界 | 返回类型声明为 `!` 的常驻循环不报<br>`cases/guideline/g-ctf-03/g-ctf-03-02` | `clippy::infinite_loop` 0→0 | lint 允许用 `-> !` 声明「有意常驻」。修订稿把它写成本条的合规写法，否则常驻服务循环无法合规。 | PASS |
| G.CTF.03-03 | 漏报 | 以 panic 作为唯一出口的循环被视为可退出<br>`cases/guideline/g-ctf-03/g-ctf-03-03` | `clippy::infinite_loop` 0→0 | lint 把任何返回 `!` 的调用（panic!、process::exit）都当作出口，而这两种方式都不会按本条要求「释放资源后安全退出」。 | PASS |
| G.CTF.03-04 | 版本差异 | 未 await 的 async 块中的常驻循环<br>`cases/guideline/g-ctf-03/g-ctf-03-04` | `clippy::infinite_loop` 1→1 | Rust/Clippy 1.89.0 会报警；这是未执行 async 块上的误报，1.97 起已豁免。<br>**版本说明**：1.89.0 的 get_parent_fn_ret_ty 会跳过 async 块向上找到外层 fn，外层 fn 不是 `-> !` 即报警；1.97 新增 is_inside_unawaited_async_block 豁免。即 1.89 下 spawn(async { loop {..} }) 类常驻任务为误报（源码比对）。 | PASS |
| G.CTF.03-05 | 命中 | while 条件变量在循环体内不变<br>`cases/guideline/g-ctf-03/g-ctf-03-05` | `clippy::while_immutable_condition` 1→1 | while 形式的死循环由 clippy::while_immutable_condition（correctness，默认 deny）覆盖，原文未列。 | PASS |
| G.CTF.03-06 | 命中 | 无出口递归被 rustc unconditional_recursion 命中<br>`cases/guideline/g-ctf-03/g-ctf-03-06` | `unconditional_recursion` 1→1 | 条款标题包含「递归」，rustc 默认 warn 的 unconditional_recursion 可覆盖「完全没有出口」的递归，原文未列。 | PASS |
| G.CTF.03-07 | 漏报 | 有基线条件但实际不可达的递归<br>`cases/guideline/g-ctf-03/g-ctf-03-07` | `unconditional_recursion` 0→0<br>`*` 0→0 | 只要存在语法上的出口就不报，递归能否终止需人工审视。 | PASS |

### G.EXP.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.EXP.01-01 | 命中 | 原文三个反例：两个 bad_bit_mask + 一个 overly_complex_bool_expr<br>`cases/guideline/g-exp-01/g-exp-01-01` | `clippy::bad_bit_mask` 2→2<br>`clippy::overly_complex_bool_expr` 1→1 | 原文只列 bad_bit_mask，只能覆盖前两个反例；第三个反例 `(x < y) && false` 需要 clippy::overly_complex_bool_expr。<br>**版本说明**：overly_complex_bool_expr 在 1.89 属 correctness（默认 deny），1.97 已降为 pedantic；POC 显式 -W 开启以消除差异。 | PASS |
| G.EXP.01-02 | 命中 | 原文未列、但同属「恒真/恒假」的其他 lint<br>`cases/guideline/g-exp-01/g-exp-01-02` | `clippy::impossible_comparisons` 1→1<br>`clippy::absurd_extreme_comparisons` 1→1<br>`clippy::eq_op` 1→1 | 区间矛盾、类型极值比较、自比较同样恒真/恒假，分别由 impossible_comparisons / absurd_extreme_comparisons / eq_op（均为 correctness）覆盖，建议补入。 | PASS |
| G.EXP.01-03 | 漏报 | 取模与「或不等」恒值表达式不报<br>`cases/guideline/g-exp-01/g-exp-01-03` | `*` 0→0 | `x % 2 == 2` 恒假、`x != 1 \|\| x != 2` 恒真，全量 lint 均不报。lint 只能部分覆盖本条。 | PASS |
| G.EXP.01-04 | 误报风险 | 以 const 作为特性开关掩码时 bad_bit_mask 报警<br>`cases/guideline/g-exp-01/g-exp-01-04` | `clippy::bad_bit_mask` 1→1 | 掩码来自配置常量、在某些构建下为 0 时，表达式在该配置下确实恒假，lint 照样报警。属于「技术上正确但意图正常」的告警，需允许局部 #[allow] 并写明原因。 | PASS |

### G.EXP.02

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.EXP.02-01 | 命中 | `1 << 2 + 3` 被 precedence 命中<br>`cases/guideline/g-exp-02/g-exp-02-01` | `clippy::precedence` 1→1 | 原文第一个反例可检出。 | PASS |
| G.EXP.02-02 | 漏报 | `-1i32.abs()` 不被 precedence 命中，需 rustc ambiguous_negative_literals<br>`cases/guideline/g-exp-02/g-exp-02-02` | `clippy::precedence` 0→0<br>`ambiguous_negative_literals` 1→1 | Clippy 已把一元负号的检查移交 rustc（1.89 的 precedence.rs 只检查算术/位移/位运算的混用），原文第二个反例需要 rustc 的 ambiguous_negative_literals（allow-by-default，需显式开启）。 | PASS |
| G.EXP.02-03 | 命中 | 位运算与移位混用归 precedence_bits<br>`cases/guideline/g-exp-02/g-exp-02-03` | `clippy::precedence` 0→0<br>`clippy::precedence_bits` 1→1 | 1.86 起「纯位运算 + 移位」拆到 restriction 组的 precedence_bits，仅开 precedence 会漏掉。 | PASS |
| G.EXP.02-04 | 漏报 | `&&` 与 `\|\|` 混用不报<br>`cases/guideline/g-exp-02/g-exp-02-04` | `*` 0→0 | 逻辑运算优先级混用在全量 lint 下零告警，需人工审视。 | PASS |

### G.FUD.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.FUD.01-01 | 命中 | 私有函数按值传入 4000 字节数组<br>`cases/guideline/g-fud-01/g-fud-01-01` | `clippy::large_types_passed_by_value` 1→1 | 原文反例可检出（pedantic 组，默认阈值 256 字节）。 | PASS |
| G.FUD.01-02 | 漏报 | pub 函数默认不报（avoid-breaking-exported-api = true）<br>`cases/guideline/g-fud-01/g-fud-01-02` | `clippy::large_types_passed_by_value` 0→0 | 对外导出的 API 默认被跳过，库代码中的公共接口恰恰是本条最该覆盖的部分。 | PASS |
| G.FUD.01-03 | 命中 | 关闭 avoid-breaking-exported-api 后 pub 函数可报<br>`cases/guideline/g-fud-01/g-fud-01-03` | `clippy::large_types_passed_by_value` 1→1 | 在 clippy.toml 中设置 avoid-breaking-exported-api = false 后，导出 API 也会被检查。 | PASS |
| G.FUD.01-04 | 漏报 | 非 Copy 的大结构体按值传入不触发 large_types_passed_by_value<br>`cases/guideline/g-fud-01/g-fud-01-04` | `clippy::large_types_passed_by_value` 0→0<br>`clippy::needless_pass_by_value` 1→1 | large_types_passed_by_value 只检查 Copy 类型；非 Copy 大类型要靠 needless_pass_by_value（仅在函数体未消费参数时才报）。 | PASS |

### G.FUD.02

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.FUD.02-01 | 命中 | 忽略 must_use 函数 / must_use 类型 / Result 返回值<br>`cases/guideline/g-fud-02/g-fud-02-01` | `unused_must_use` 3→3 | 三种方式均触发 rustc unused_must_use（默认 warn）。原文写的 `rustc::unused_must_use` 不是合法写法，rustc 内建 lint 没有工具前缀，应写为 unused_must_use。 | PASS |
| G.FUD.02-02 | 漏报 | `let _ =` 静默丢弃 must_use 值<br>`cases/guideline/g-fud-02/g-fud-02-02` | `unused_must_use` 0→0<br>`clippy::let_underscore_must_use` 2→2 | `let _ =` 会让 unused_must_use 失效，需 clippy::let_underscore_must_use（restriction）补位。 | PASS |
| G.FUD.02-03 | 漏报 | `.ok();` 丢弃 Result<br>`cases/guideline/g-fud-02/g-fud-02-03` | `unused_must_use` 0→0<br>`clippy::unused_result_ok` 1→1 | `.ok()` 把 Result 转为 Option 后丢弃，unused_must_use 不报，需 clippy::unused_result_ok（restriction，1.82+）。 | PASS |
| G.FUD.02-04 | 漏报 | must_use 类型包在 Option 中返回<br>`cases/guideline/g-fud-02/g-fud-02-04` | `unused_must_use` 0→0 | must_use 标注在类型上时，套一层 Option 即失效；对关键返回值宜在函数上也标注 #[must_use]。 | PASS |
| G.FUD.02-05 | 命中 | 作者侧：公共纯函数缺 must_use 被 must_use_candidate 提示<br>`cases/guideline/g-fud-02/g-fud-02-05` | `clippy::must_use_candidate` 1→1 | 本条约束的是「定义方是否合理标注」，unused_must_use 只检查调用方。作者侧可用 must_use_candidate / return_self_not_must_use（均 pedantic）辅助。 | PASS |

### G.TRA.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.TRA.01-01 | 命中 | 原文反例：derive(Hash) + 手写 PartialEq<br>`cases/guideline/g-tra-01/g-tra-01-01` | `clippy::derived_hash_with_manual_eq` 1→1 | 可检出（correctness，默认 deny）。 | PASS |
| G.TRA.01-02 | 命中 | 原文反例：derive(Ord) + 手写 PartialOrd<br>`cases/guideline/g-tra-01/g-tra-01-02` | `clippy::derive_ord_xor_partial_ord` 1→1 | 可检出（correctness，默认 deny）。 | PASS |
| G.TRA.01-03 | 示例校验 | 原文 Ord「正例」实际违反 Ord 与 Eq 的一致性<br>`cases/guideline/g-tra-01/g-tra-01-03` | `clippy::derive_ord_xor_partial_ord` 0→0<br>`clippy::non_canonical_partial_ord_impl` 1→1<br>输出：`eq=false cmp=Equal / btreeset_len=1` | PartialEq/Eq 由 derive 比较全部字段，Ord 只比较 uid，于是出现 a != b 但 a.cmp(&b) == Equal，BTreeSet 会把两人当作同一元素丢掉一个。这违反了 Ord 文档中「与 Eq 一致」的要求，原文却标为「符合」。该问题没有 lint 能发现（non_canonical_partial_ord_impl 只提示 partial_cmp 写法不规范）。 | PASS |
| G.TRA.01-04 | 漏报 | Hash 与 PartialEq 均手写且不一致<br>`cases/guideline/g-tra-01/g-tra-01-04` | `clippy::derived_hash_with_manual_eq` 0→0<br>`*` 0→0<br>输出：`eq=true same_hash=false` | 两边都手写时 lint 完全不介入（derived_hash_with_manual_eq 只看 derive(Hash)），一致性只能靠评审 / 单元测试。 | PASS |
| G.TRA.01-05 | 示例校验 | 修订稿 Ord 正例：相等性与排序口径一致<br>`cases/guideline/g-tra-01/g-tra-01-05` | `clippy::derive_ord_xor_partial_ord` 0→0<br>`clippy::non_canonical_partial_ord_impl` 0→0<br>`clippy::derived_hash_with_manual_eq` 0→0<br>输出：`eq=true cmp=Equal names=ab` | PartialEq 与 Ord 均以 uid 为准，partial_cmp 采用规范写法 Some(self.cmp(other))，相关 lint 零告警。 | PASS |

### G.TRA.02

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.TRA.02-01 | 命中 | 原文反例：impl Into<StringWrapper> for String<br>`cases/guideline/g-tra-02/g-tra-02-01` | `clippy::from_over_into` 1→1 | 可检出（style，默认 warn）。 | PASS |
| G.TRA.02-02 | 命中 | 泛型 Into 实现同样命中<br>`cases/guideline/g-tra-02/g-tra-02-02` | `clippy::from_over_into` 1→1 | 泛型场景同样覆盖；未发现漏报或误报场景。 | PASS |

### G.ERR.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.ERR.01-01 | 命中 | unwrap() 被 unwrap_used 命中<br>`cases/guideline/g-err-01/g-err-01-01` | `clippy::unwrap_used` 1→1 | 可检出（restriction，需显式开启）。 | PASS |
| G.ERR.01-02 | 漏报 | expect() 不在 unwrap_used 范围内<br>`cases/guideline/g-err-01/g-err-01-02` | `clippy::unwrap_used` 0→0<br>`clippy::expect_used` 1→1 | 原文只列 unwrap_used，expect 同样会 panic，需要同时开启 expect_used。 | PASS |
| G.ERR.01-03 | 漏报 | unwrap_or_else(\|e\| panic!(..)) 绕过 unwrap/expect 检查<br>`cases/guideline/g-err-01/g-err-01-03` | `clippy::unwrap_used` 0→0<br>`clippy::expect_used` 0→0<br>`clippy::panic` 1→1 | 原文把 unwrap_or_else 列为合规处理方式，但闭包中直接 panic 与 unwrap 等价。需 clippy::panic 兜底，并在描述中加以限定。 | PASS |
| G.ERR.01-04 | 误报 | 条款允许的「已提前校验」场景仍被报<br>`cases/guideline/g-err-01/g-err-01-04` | `clippy::unwrap_used` 1→1 | lint 无法理解前置校验，例外场景需用 #[expect(clippy::unwrap_used, reason = …)] 局部豁免并写明理由。 | PASS |
| G.ERR.01-05 | 误报 | 测试代码中的 unwrap 默认被报<br>`cases/guideline/g-err-01/g-err-01-05` | `clippy::unwrap_used` 1→1 | 默认 allow-unwrap-in-tests = false，测试代码也会报。建议在 clippy.toml 中设置 allow-unwrap-in-tests / allow-expect-in-tests = true。 | PASS |
| G.ERR.01-06 | 示例校验 | 修订后的正例可编译且零告警<br>`cases/guideline/g-err-01/g-err-01-06` | `*` 0→0 | 原文正例缺少 `use std::fs` 与 CONFIG_PATH 定义；修订稿补齐。 | PASS |

### G.MOD.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.MOD.01-01 | 命中 | 原文反例 `use std::ptr::*`<br>`cases/guideline/g-mod-01/g-mod-01-01` | `clippy::wildcard_imports` 1→1 | 可检出（pedantic，需显式开启）。 | PASS |
| G.MOD.01-02 | 边界 | prelude::* 与 pub use 再导出默认不报<br>`cases/guideline/g-mod-01/g-mod-01-02` | `clippy::wildcard_imports` 0→0 | 与条款中的 prelude 例外一致；pub use 再导出默认豁免（warn-on-all-wildcard-imports 可收紧）。 | PASS |
| G.MOD.01-03 | 漏报 | 测试模块内的通配导入全部不报<br>`cases/guideline/g-mod-01/g-mod-01-03` | `clippy::wildcard_imports` 0→0 | wildcard_imports 在 test crate（cfg(test) 编译）中整体跳过，不只豁免 `use super::*`，`use std::collections::*` 也不报。条款若不打算豁免测试代码，这里是漏报。 | PASS |
| G.MOD.01-04 | 命中 | 枚举变体通配导入归 enum_glob_use<br>`cases/guideline/g-mod-01/g-mod-01-04` | `clippy::wildcard_imports` 0→0<br>`clippy::enum_glob_use` 1→1 | `use Enum::*` 由 enum_glob_use 负责，只开 wildcard_imports 会漏掉。 | PASS |

### G.MAC.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.MAC.01-01 | 漏报 | 原文 make_safe!（私有宏）默认不报<br>`cases/guideline/g-mac-01/g-mac-01-01` | `clippy::macro_metavars_in_unsafe` 0→0 | 原文所列 unsafe_block_in_proc_macro 在 1.89 的 rustc 与 Clippy 中均不存在。最接近的 clippy::macro_metavars_in_unsafe 默认只检查导出宏，原文反例是私有宏，因此不报。 | PASS |
| G.MAC.01-02 | 命中 | 开启 warn-unsafe-macro-metavars-in-private-macros 后命中<br>`cases/guideline/g-mac-01/g-mac-01-02` | `clippy::macro_metavars_in_unsafe` 1→1 | 在 clippy.toml 打开私有宏检查后命中。 | PASS |
| G.MAC.01-03 | 漏报 | 宏内硬编码 unsafe 调用（不经元变量）不报<br>`cases/guideline/g-mac-01/g-mac-01-03` | `clippy::macro_metavars_in_unsafe` 0→0 | lint 只检查「元变量是否在 unsafe 块内展开」；宏把固定的 unsafe 调用包装成 safe fn 同样是伪装，但不报。 | PASS |
| G.MAC.01-04 | 漏报 | 过程宏把调用方表达式放进 unsafe 块：调用方无需 unsafe 即可执行不安全操作<br>`cases/guideline/g-mac-01/g-mac-01-04` | `clippy::macro_metavars_in_unsafe` 0→0<br>输出：`got=7` | 与原文过程宏反例同构。编译、运行均通过且无任何告警：Clippy 对过程宏生成的 unsafe 无检测能力。 | PASS |
| G.MAC.01-05 | 示例校验 | 原文【例外】示例在 edition 2024 下告警<br>`cases/guideline/g-mac-01/g-mac-01-05` | `E0133` 1→1 | 例外示例存在三个问题：名为 safe_function 却声明为 unsafe fn；仅判空不足以保证指针有效（悬垂、未对齐同样是 UB）；且 2024 版次下 unsafe fn 体内的不安全操作必须放进 unsafe 块。修订稿改写了该示例。 | PASS |
| G.MAC.01-06 | 示例校验 | 修订稿【例外】示例：元变量在 unsafe 外求值且前置条件完整校验<br>`cases/guideline/g-mac-01/g-mac-01-06` | `clippy::macro_metavars_in_unsafe` 0→0<br>`clippy::undocumented_unsafe_blocks` 0→0<br>输出：`Some(20) None` | 即使开启私有宏检查，修订后的例外示例也不报，行为正确。 | PASS |

### P.MAC.DCL.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| P.MAC.DCL.01-01 | 示例校验 | 宏内硬编码生命周期 'a：对 Bar<'b> 编译失败<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-01` | 编译失败：use of undeclared lifetime name `'b` | 原文描述属实：Foo<'a> 能编译，Bar<'b> 报 E0261 undeclared lifetime。 | PASS |
| P.MAC.DCL.01-02 | 示例校验 | 跨 crate：宏内调用另一个宏（不用 $crate）<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-02` | 编译失败：cannot find macro `helper` in this scope | 原文描述属实：crate b 中报 cannot find macro `helper` in this scope。 | PASS |
| P.MAC.DCL.01-03 | 示例校验 | 跨 crate：宏内调用另一个宏（用 $crate）<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-03` | 编译通过 | 使用 $crate::helper!() 后可正常编译。 | PASS |
| P.MAC.DCL.01-04 | 命中 | 导出宏中写 crate:: 被 crate_in_macro_def 命中；裸路径不报<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-04` | `clippy::crate_in_macro_def` 1→1 | clippy::crate_in_macro_def（suspicious，默认 warn）能检出导出宏里误用 `crate::`（应为 $crate::），可部分覆盖本原则；裸路径 helper() 不报。 | PASS |
| P.MAC.DCL.01-05 | 示例校验 | 宏引用第三方 crate 的 item：直接写 ::crate名<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-05` | 编译失败：failed to resolve: could not find `helper_dep` in the list of imported crates | 调用方只依赖宏所在的 crate、没有直接依赖 helper_dep 时编译失败。原文「用 crate 名来引用」只在调用方也直接依赖该 crate 时成立。 | PASS |
| P.MAC.DCL.01-06 | 示例校验 | 宏引用第三方 crate 的 item：经 $crate 再导出<br>`cases/guideline/p-mac-dcl-01/p-mac-dcl-01-06` | 编译通过 | 在宏所在 crate 中 `pub use` 依赖，并通过 `$crate::` 引用，调用方无需额外依赖。 | PASS |

### G.MAC.DCL.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| G.MAC.DCL.01-01 | 语义验证 | 宽规则在前时后续规则永不匹配，且无任何 lint<br>`cases/guideline/g-mac-dcl-01/g-mac-dcl-01-01` | `*` 0→0<br>输出：`got something else,got something else,got something else` | 原文描述属实；rustc / Clippy 对「被遮蔽的宏规则」均无告警，本条无 lint 支持。 | PASS |
| G.MAC.DCL.01-02 | 语义验证 | 片段解析一旦开始就不回溯：`$e:expr` 在前时 `m!(1 +)` 直接报错<br>`cases/guideline/g-mac-dcl-01/g-mac-dcl-01-02` | 编译失败：expected expression, found end of macro arguments | 规则顺序还影响能否编译：前面的规则已开始解析 expr 片段并失败时，编译器直接报错，不会尝试后续 tt 规则。修订稿在【说明】中补充这一点。 | PASS |

### P.MAC.PRO.01

| ID | 类别 | 场景 | 预期 → 实测 | 结论 | 状态 |
| --- | --- | --- | --- | --- | --- |
| P.MAC.PRO.01-01 | 语义验证 | call_site 卫生：宏读写调用方变量<br>`cases/guideline/p-mac-pro-01/p-mac-pro-01-01` | 编译通过<br>输出：`x=999 local="hello"` | 原文反例属实：quote! 默认使用 Span::call_site()，生成的标识符与调用方同名即相互可见。 | PASS |
| P.MAC.PRO.01-02 | 语义验证 | Span::mixed_site()：宏内局部变量不再泄漏到调用方<br>`cases/guideline/p-mac-pro-01/p-mac-pro-01-02` | 编译通过<br>输出：`local=""` | 用 Span::mixed_site()（1.45 起稳定）生成局部变量，可获得与 macro_rules 相同的局部变量卫生性，比约定 __ 前缀更可靠。修订稿补充为首选方法。 | PASS |

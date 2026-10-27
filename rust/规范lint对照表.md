# 规范条款与 lint 对照表

- 基线：rustc / Clippy 1.89.0。分组、默认级别、引入版本均取自 rust-lang/rust@1.89.0 与 rust-clippy@rust-1.89.0 源码。
- Clippy 的默认级别由分组决定：correctness 为 **deny**；suspicious、style、complexity、perf 为 **warn**；pedantic、restriction、nursery 为 **allow**（不显式开启就不检查）。以上只在运行 `cargo clippy` 时生效，`cargo build` / `cargo check` 不运行 Clippy lint。
- rustc lint 的默认级别为编译器内置，`cargo build` / `cargo check` 即生效。
- 「需显式开启」：默认 allow，需要 `-W <lint>` 或在 Cargo.toml 的 `[lints]` 中配置。

| 条款 | lint | 来源 | 分组 | 默认级别 | 引入版本 | 检查行为 | 配置 / 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G.CTF.01 | `clippy::unnecessary_unwrap` | Clippy | complexity | warn | 1.29 前 | 先用 `is_some()` / `is_ok()` 判断、再调用 `unwrap()` | 1.89 只识别局部变量，结构体字段不报（1.97 起支持） |
| G.CTF.02 | — | — | — | — | — | 无对应 lint | — |
| G.CTF.03 | `clippy::infinite_loop` | Clippy | restriction | allow | 1.76 | 没有 `break` / `return` 等退出路径的 `loop` | 需显式开启；函数返回 `!` 时豁免；panic、process::exit 被视为出口 |
| G.CTF.03 | `clippy::while_immutable_condition` | Clippy | correctness | deny | 1.29 前 | `while` 条件依赖的变量在循环体内从不改变 | — |
| G.CTF.03 | `unconditional_recursion` | rustc | — | warn | — | 所有执行路径都会递归调用自身、无法正常返回 | 有终止分支但不可达时不报 |
| G.EXP.01 | `clippy::bad_bit_mask` | Clippy | correctness | deny | 1.29 前 | 位掩码与常量比较的结果恒真或恒假，如 `(x & 1) == 2` | 掩码为配置生成的 0 时也会报 |
| G.EXP.01 | `clippy::overly_complex_bool_expr` | Clippy | correctness | deny | 1.29 前 | 布尔表达式中含可直接消去的项，如 `(x < y) && false` | 1.97 起降为 pedantic（allow），升级后需显式开启 |
| G.EXP.01 | `clippy::impossible_comparisons` | Clippy | correctness | deny | 1.73 | 同一变量的多个比较不可能同时成立，如 `x > 10 && x < 5` | — |
| G.EXP.01 | `clippy::absurd_extreme_comparisons` | Clippy | correctness | deny | 1.29 前 | 与类型最小值 / 最大值的无意义比较，如 `u32 >= 0` | 与 `unused_comparisons` 有重叠 |
| G.EXP.01 | `unused_comparisons` | rustc | — | warn | — | 因类型取值范围而恒真 / 恒假的比较 | — |
| G.EXP.01 | `clippy::eq_op` | Clippy | correctness | deny | 1.29 前 | 比较或运算两侧是同一表达式，如 `x == x` | — |
| G.EXP.02 | `clippy::precedence` | Clippy | complexity | warn | 1.29 前 | 算术运算与位移 / 位运算混用且缺少括号，如 `1 << 2 + 3` | 不检查一元负号、`&&`/`||` 混用 |
| G.EXP.02 | `clippy::precedence_bits` | Clippy | restriction | allow | 1.86 | 位运算与移位混用且缺少括号，如 `x & 0xF0 >> 4` | 需显式开启 |
| G.EXP.02 | `ambiguous_negative_literals` | rustc | — | allow | — | 负号字面量后接方法调用，如 `-1i32.abs()` | 需显式开启；可能误报 `-1.hour()` 这类领域写法 |
| G.FUD.01 | `clippy::large_types_passed_by_value` | Clippy | pedantic | allow | 1.49 | 按值传入、且大小超过阈值的 **Copy** 类型参数 | 需显式开启；阈值 `pass-by-value-size-limit`（默认 256 字节）；默认跳过 pub 函数，需 `avoid-breaking-exported-api = false` |
| G.FUD.01 | `clippy::needless_pass_by_value` | Clippy | pedantic | allow | 1.29 前 | 按值接收非 Copy 参数，但函数体并未消费它 | 需显式开启；同样受 `avoid-breaking-exported-api` 影响 |
| G.FUD.02 | `unused_must_use` | rustc | — | warn | — | 调用方直接忽略 `#[must_use]` 函数、类型或 `Result` 的返回值 | `let _ =`、`.ok();`、`Option<MustUse>` 不报，需人工评审 |
| G.TRA.01 | `clippy::derived_hash_with_manual_eq` | Clippy | correctness | deny | 1.29 前 | derive(Hash) 与手写 PartialEq 混用 | 两边都手写时不检查 |
| G.TRA.01 | `clippy::derive_ord_xor_partial_ord` | Clippy | correctness | deny | 1.47 | Ord 与 PartialOrd 一个 derive、一个手写 | 不检查排序与相等性是否一致 |
| G.TRA.01 | `clippy::non_canonical_partial_ord_impl` | Clippy | suspicious | warn | 1.73 | 同时实现 Ord 时，`partial_cmp` 未写成 `Some(self.cmp(other))` | — |
| G.TRA.01 | `clippy::impl_hash_borrow_with_str_and_bytes` | Clippy | correctness | deny | 1.76 | 同时实现 `Borrow<str>` 与 `Borrow<[u8]>` 时 Hash 不一致 | 只覆盖 Borrow 约束中的这一特例 |
| G.TRA.02 | `clippy::from_over_into` | Clippy | style | warn | 1.51 | 直接实现 `Into` 而不是 `From` | — |
| G.ERR.01 | `clippy::unwrap_used` | Clippy | restriction | allow | 1.45 | 对 Option / Result 调用 `unwrap()` | 需显式开启；测试代码豁免需 `allow-unwrap-in-tests = true` |
| G.ERR.01 | `clippy::expect_used` | Clippy | restriction | allow | 1.45 | 对 Option / Result 调用 `expect()` | 需显式开启；测试代码豁免需 `allow-expect-in-tests = true` |
| G.ERR.01 | `clippy::panic` | Clippy | restriction | allow | 1.40 | 代码中出现 `panic!` | 需显式开启；可选，范围大于本条 |
| G.MOD.01 | `clippy::wildcard_imports` | Clippy | pedantic | allow | 1.43 | `use module::*` 通配导入 | 需显式开启；默认豁免 `prelude::*`、`pub use` 与测试代码，`warn-on-all-wildcard-imports = true` 可取消 |
| G.MOD.01 | `clippy::enum_glob_use` | Clippy | pedantic | allow | 1.29 前 | `use Enum::*` 枚举变体通配导入 | 需显式开启 |
| G.MAC.01 | `clippy::macro_metavars_in_unsafe` | Clippy | suspicious | warn | 1.80 | 声明宏的元变量在 unsafe 块内展开 | 默认只查导出宏，私有宏需 `warn-unsafe-macro-metavars-in-private-macros = true`；不覆盖过程宏 |
| G.MAC.01 | `clippy::undocumented_unsafe_blocks` | Clippy | restriction | allow | 1.58 | unsafe 块缺少 `// SAFETY:` 注释 | 需显式开启；可选，范围大于本条 |
| P.MAC.DCL.01 | `clippy::crate_in_macro_def` | Clippy | suspicious | warn | 1.62 | 导出宏定义中使用 `crate::`（应为 `$crate::`） | 只查 `#[macro_export]` 宏；裸路径不报 |
| G.MAC.DCL.01 | — | — | — | — | — | 无对应 lint | — |
| P.MAC.PRO.01 | — | — | — | — | — | 无对应 lint | — |

## 汇总

| 默认级别 | 数量 | lint |
| --- | :---: | --- |
| deny（Clippy correctness） | 9 | while_immutable_condition、bad_bit_mask、overly_complex_bool_expr、impossible_comparisons、absurd_extreme_comparisons、eq_op、derived_hash_with_manual_eq、derive_ord_xor_partial_ord、impl_hash_borrow_with_str_and_bytes |
| warn | 9 | Clippy：unnecessary_unwrap、precedence、non_canonical_partial_ord_impl、from_over_into、macro_metavars_in_unsafe、crate_in_macro_def；rustc：unconditional_recursion、unused_comparisons、unused_must_use |
| allow（需显式开启） | 11 | Clippy：infinite_loop、precedence_bits、large_types_passed_by_value、needless_pass_by_value、unwrap_used、expect_used、panic、wildcard_imports、enum_glob_use、undocumented_unsafe_blocks；rustc：ambiguous_negative_literals |

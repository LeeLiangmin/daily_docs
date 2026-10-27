# 1 概述

## 1.1 背景

为了帮助开发者高效安全的使用 Rust 语言进行开发，保证 Rust 代码质量，特制定 Rust 编程规范。

## 1.2 目标与适用范围

**本规范的目标如下：**

- 遵循 Rust 语言特性，提高代码的可读性、可维护性、健壮性和可移植性。
- 提高 Unsafe Rust 代码编写的规范性和安全性。
- 编程规范条款力求系统化、易应用、易检查，帮助开发者提升开发效率。

**适用范围：**

本规范适用于公司使用 Rust 语言（Rust 1.68.0+）编写的自研代码。

## 1.3 总体原则

程序需要在保证功能正确的前提下，满足可读、可维护、安全、可靠、可测试、高效、可移植的特征要求，详见《华为Clean Code指导书》。

## 1.4 条款组织方式

每个条款一般包含标题、级别、描述等组成部分。

**规范条款分为原则和规则两个类别**：

- **原则**：可以评价规则内容制定的好坏并引导规则进行相应的调整（从规范架构和功能上说，指导规则的制定以及代码/框架/功能的设计）。工具不检测原则类条目。
- **规则**：是需要遵从或参考的实践。工具会检测规则类条目。

**标题**

概括本条款的要求或建议。

通过标题前的编号标识出条款的类别为原则或规则：标题前的编号规则参见《安全工程规范内容总纲》，其中'P'为单词Principle首字母，'G'为单词Guideline的首字母。

- 标识 `P` 为原则。编号方式为 `P.Element.Number`。
- 标识 `G` 为规则。编号方式为 `G.Element.Number`。
- 当有子目录时，编号方式为 `P.Element.SubElement.Number` 或 `G.Element.SubElement.Number`。

其中 `Element` 为领域知识中关键元素（本规范中对应的二级目录）的 3 英文字母缩略语。`Number` 是从 1 开始递增的两位阿拉伯数字，不足两位时高位补 0。

（术语参考： [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard) ）


| Element      | 解释       | Element | 解释         |
| ------- | ------ | ------- | -------- |
| NAM     | 命名 (Naming)   | CMT     | 注释 (Comment)    |
| FMT     | 格式 (Format)   | TYP     | 数据类型 (Data Type) |
| CNS     | 常量 (Const)   | PTR     | 指针  (Pointer)  |
| EXP     | 表达式 (Expression) | CTF     | 控制流程 (Control Flow) |
| STR     | 字符串 (String) | INT     | 整数 (Integer)    |
| MOD     | 模块  (Module) | MEM     | 内存 (Memory) |
| MAC     | 宏  (Macro)   | FUD     | 函数设计 (Function Design) |
| ASY     | 异步 (Async) | TRA     | Trait |
| ERR     | 错误处理 (Error Handle)  | UNS | 非安全 (Unsafe Rust) |
| MTH     | 多线程 (Multi Threads) | FFI | 外部函数调用接口 ( Foreign Function Interface ) |
| SLC     | 切片类型 (Slice) | BOL | 布尔 (Bool) |
| CHR     | 字符类型 (Char) |  FLT | 浮点数 (Float) |
| SCT     | 结构体 (Struct) |  SAF | 内存安全 (Safety)  |
| DCL     | 声明宏 (Declarative)  | PRO  |  过程宏 (Procedural) |
| OTH     | 其它 (Others) | | |


**级别**

规则类条款分为两个级别：

- 要求：表示产品原则上应该遵从，但可以按照具体产品版本计划和节奏分期实现。
- 建议：表示该条款属于优秀的编程实践，有助于进一步消解风险，产品可结合业务情况考虑是否纳入，但要保证实施一致的代码风格。

**描述**

对条款的进一步描述，描述条款的原理，配合正确和错误的代码例子作为示范。有的条款还包含一些规则不适用的例外场景。

**说明**

对条款中的名词、背景、原理等进行补充说明。

# 2 代码风格

代码风格一般包含标识符的命名风格、排版与格式风格，注释风格。一致的编码习惯与风格，会使代码更易阅读、更易理解、更易维护。

## 2.1 命名

### P.NAM.01 标识符命名应符合阅读习惯

**【描述】**

标识符的命名要清晰、明了，有明确含义，容易理解。符合英文阅读习惯的命名将明显提高代码可读性。

**【说明】**

一些好的实践包括但不限于：

- 使用正确的英文单词并符合英文语法，不要使用拼音。
- 仅使用常见或领域内通用的单词缩写。
- 布尔型变量或函数避免使用否定形式。

### G.NAM.01 应使用统一的命名风格

**【级别】** 建议

**【描述】**

应在代码中遵循统一的 Rust 命名风格。

- 通常在 类型、trait、枚举体 等语言项使用大驼峰（`UpperCamelCase`） 命名风格，在 变量名、函数名 等语言项使用蛇形（`snake_case`）命名风格。

- 为 Cargo Feature 命名应该避免出现： `no_` 或 `not_` 之类的否定前缀； `use_` 或 `with_` 之类的多余前缀；`_support` 之类的多余后缀。

**【说明】**

下面是汇总信息：

| Item                                | 规范                                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------- |
| 包（Crates）                        | [通常使用 `snake_case` ](https://github.com/rust-lang/api-guidelines/issues/29) |
| 模块（Modules）                     | `snake_case`                                                                    |
| 类型（Types）                       | `UpperCamelCase`                                                                |
| Trait                               | `UpperCamelCase`                                                                |
| 枚举体                              | `UpperCamelCase`                                                                |
| 枚举体成员（Enum variants）         | `UpperCamelCase`                                                                |
| 结构体（Structs）                   | `UpperCamelCase`                                                                |
| 结构体/联合体成员                   | `snake_case`                                                                    |
| 函数（Functions）                   | `snake_case`                                                                    |
| 方法（Methods）                     | `snake_case`                                                                    |
| 构造函数（General constructors）    | `new` 或者 `with_more_details`                                                  |
| 转换函数（Conversion constructors） | `from_some_other_type`                                                          |
| 宏（Macros）                        | `snake_case`                                                                    |
| 本地变量（Local variables）         | `snake_case`                                                                    |
| 静态变量（Statics）                 | `SCREAMING_SNAKE_CASE`                                                          |
| 常量（Constants）                   | `SCREAMING_SNAKE_CASE`                                                          |
| 类型参数（Type parameters）         | 简明的 `UpperCamelCase`，通常使用单个大写字母： `T`                             |
| 生存期（Lifetimes）                 | 简短的 `lowercase`，通常使用单个小写字母 `'a`, `'de`, `'src`, 尽量保持语义      |
| 特性（Features）                    | `snake_case`                                                                    |

补充解释:

- `UpperCamelCase`: 每个单词的首字母都是大写的，其余部分小写，没有分隔符。由首字母缩写组成的缩略语和复合词的缩写，算作单个词。比如，应该使用 `Uuid` 而非 `UUID`，使用 `Stdin` 而不是 `StdIn`。
- `snake_case`: 每个单词都是小写的，使用下划线作为分隔符， 如 `is_xid_start`。
- `SCREAMING_SNAKE_CASE`: 每个单词都是大写的，使用下划线作为分隔符。
- 在 `snake_case` 或者 `SCREAMING_SNAKE_CASE` 情况下，每个词不应该由单个字母组成——除非这个字母是最后一个词。比如，使用 `btree_map` 而不使用 `b_tree_map`，使用 `PI_2` 而不使用 `PI2`。
- 通用构造函数的 `with_more_details` 形式是指推荐用户使用如: `with_capacity`, `with_file_name` 等函数名（注意不与上文 Cargo Feature 命名规范混淆）。
- 转换构造函数的 `from_some_other_type` 形式是指推荐用户使用如: `from_bytes`, `from_str`, `from_array` 等函数名。

关于包命名：

- 由于历史问题，包名有两种形式 `snake_case` 或 `kebab-case`，但实际在代码中需要引入包名的时候，Rust 只能识别 `snake_case`，也会自动将 `kebab-case` 识别为  `kebab_case`。所以建议使用`snake_case`。
- Crate 的名称通常不应该使用 `-rs` 或者 `-rust` 作为后缀或者前缀。但是有些情况下，比如是其他语言移植的同名 Rust 实现，则可以使用 `-rs` 后缀来表明这是 Rust 实现的版本。

### G.NAM.02 类型转换函数命名宜遵循所有权语义

**【级别】** 建议

**【描述】**

Rust 语言依赖所有权来管理内存，所以在命名上遵循所有权语义，可以提升代码可读性和透明性，以便从代码命名中发现内存使用的代价。

**【说明】**

进行特定类型转换的方法名应该包含以下前缀：

| 名称前缀 | 内存代价 | 参数 -> 返回值所有权情况 | 标准库示例 |
| ------ | ---- | --------- | ------------------ |
| `as_` | 无代价 | borrowed -\> borrowed | [`str::as_bytes()`](https://doc.rust-lang.org/std/primitive.str.html#method.as_bytes)<br>[`str::as_bytes_mut()`](https://doc.rust-lang.org/std/primitive.str.html#method.as_bytes_mut) |
| `to_` | 代价昂贵 | borrowed -\> borrowed<br>borrowed -\> owned (适用于 non-copy 类型转换)<br>owned -\> owned (适用于 copy 类型转换) | [`Path::to_str()`](https://doc.rust-lang.org/stable/std/path/struct.Path.html#method.to_str)<br>[`str::to_lowercase()`](https://doc.rust-lang.org/std/primitive.str.html#method.to_lowercase) |
| `into_` | 看情况 | owned -\> owned (适用于 non-copy 类型转换) | [`String::into_bytes()`](https://doc.rust-lang.org/std/string/struct.String.html#method.into_bytes) |

以 `as_` 和 `into_` 作为前缀的类型转换通常是 *降低抽象层次*，要么是查看背后的数据 (`as`)，要么是解构 (deconstruct) 背后的数据 (`into`) 。
相对来说，以 `to_` 作为前缀的类型转换处于同一个抽象层次，但是底层会做更多工作，比如多了内存拷贝等操作。

当一个类型用更高级别的语义 (higher-level semantics) 封装 (wraps) 一个内部类型时，应该使用 `into_inner()` 方法名来取出被封装类型的值。

**【反例】**

```rust
fn main() {
    struct X();
    static S: &str = "str";

    impl X {
        // 不符合：as_ 命名的方法不应获取 self 的所有权
        fn as_str(self) -> &'static str {
            S
        }
        // 不符合：当返回值不是借用，to_ 命名的方法不应使用 &mut self 作为参数
        fn to_my_string(&mut self) -> String {
            S.to_string()
        }
        // 不符合：into_ 通常需要获取 self 的所有权
        fn into_my_string(&self) -> String {
            S.to_string()
        }
    }
}
```

**【正例】**

```rust
fn main() {
    struct X();
    static S: &str = "str";

    impl X {
        // 符合：as_ 命名的方法只借用 self
        fn as_str(&self) -> &'static str {
            S
        }
        // 符合：返回值不是借用，且 self 对应的类型不支持 Copy 时，to_ 命名的方法则使用 &self 作为参数
        fn to_my_string(&self) -> String {
            S.to_string()
        }
        // 符合：into_ 命名的方法获取了 self 的所有权
        fn into_my_string(self) -> String {
            S.to_string()
        }
    }
}
```

## 2.2 格式与注释

### P.CMT.01 注释跟代码一样重要，应按需注释

**【描述】**

一般应通过清晰的软件架构，良好的符号命名来提高代码可读性；在需要的时候，才辅以注释说明。

注释是为了帮助阅读者快速读懂代码，所以要从读者的角度出发，**按需注释。**

注释内容要简洁、明了、无歧义，信息全面且不冗余。

需要注释的地方没有注释，代码则难以被读懂；而包含无用、重复信息的冗余注释不仅浪费维护成本，还会弱化真正有用的注释，最终让所有注释都不可信。

**注释跟代码一样重要。**

写注释时要换位思考，用注释去表达此时读者真正需要的信息。在代码的功能、意图层次上进行注释，即注释解释代码难以表达的意图，不要重复代码信息。

修改代码时，也要保证其相关注释的一致性。只改代码，不改注释是一种不文明行为，破坏了代码与注释的一致性，让阅读者迷惑、费解，甚至误解。

使用流利的中文或英文进行注释。
为降低沟通成本，应使用团队内最擅长、沟通效率最高的语言写注释；注释语言由开发团队统一决定。

### P.FMT.01 代码格式应保持统一

**【描述】**

代码应该保持统一的格式，这样可以增强代码可读性和可维护性，利于团队协作。

统一的代码格式应遵循以下规范：

- 缩进：使用四个空格（space）而非制表符（tab），文档代码同等对待。
- 换行：统一大括号换行风格；多行表达式操作时，操作符应该置于行首。
- 行间：如果需要留空，则最多空一行。
- 行宽：不超过 120 个字符（注：rustfmt 缺省宽度（max_width）为 100，因此需要在 rustfmt 模板中明确配置）。

应该总是使用代码自动格式化工具，比如 `rustfmt`，来达成这一目标。

**【说明】**

`rustfmt` 支持各团队按需定制代码风格。

参考 [附录A Rustfmt 配置与模板](../../Appendix/templates/rustfmt.toml.md)

### G.CMT.01 公开的 API 需要文档注释

**【级别】** 建议

**【描述】**

- 公开 API 如需返回 `Result` 类型的函数，则相应文档中需增加 `Error` 注释：

    解释什么场景下会返回什么样的错误类型，便于调用者处理错误。

- 公开 API 如有发生 `Panic` 的可能，则相应文档中需增加 `Panic` 注释：

    解释在什么条件下会发生 `Panic`，便于调用者进行预处理。

- 公开 API 中的 `Unsafe` 函数或 `trait`，文档中需添加 `Safety` 注释和相关说明：

    解释该函数接口的安全边界，便于调用者安全地使用。

    在函数内部的 unsafe 代码块（即 `unsafe {...}`）上方，不统一要求，但是建议添加 `SAFETY` 注释，提升代码的可维护性。

    `Safety` 文档注释建议包含以下内容（如果适用）：

    - 前提条件（例如，参数的有效状态是什么？）。
    - 失败处理（例如，什么值应该被释放？）。
    - 成功处理（例如，什么值被创建或消耗？）。

**【正例】**

```rust
use std::io;
// 符合：增加了规范的 Errors 文档注释
/// ...
/// # Errors
///
/// Will return `Err` if `filename` does not exist or the user does not have
/// permission to read it.
pub fn read(filename: &str) -> io::Result<String> {
    // ...
}

// 符合：增加了规范的 Panic 注释
/// ...
/// # Panics
///
/// Will panic if y is 0
pub fn divide_by(x: i32, y: i32) -> i32 {
    if y == 0 {
        panic!("Cannot divide by 0")
    } else {
        x / y
    }
}

// 符合：增加了 unsafe 下的 Safety 注释
/// ...
/// # Safety
///
/// The bytes passed in must be valid UTF-8.
/// ...
pub const unsafe fn from_utf8_unchecked(v: &[u8]) -> &str {
    // SAFETY: the caller must guarantee that the bytes `v` are valid UTF-8.
    // Also relies on `&str` and `&[u8]` having the same layout.
    unsafe { mem::transmute(v) }
}
```

### G.CMT.02 文件头注释应包含版权说明

**【级别】** 建议

**【描述】**

文件头注释应首先包含版权说明。

如果文件头注释需要增加其他内容，可以后面补充。
比如：文件功能说明，作者、创建日期、注意事项等等。

版权许可内容及格式必须如下：
中文：`版权所有 (c) 华为技术有限公司 2012-2018`
或英文：`Copyright (c) Huawei Technologies Co., Ltd. 2012-2018. All rights reserved.`

版权许可内容解释如下：

- 2012-2018 根据实际需要可以修改。

    2012 是文件首次创建年份，而 2018 是最后文件修改年份。
    对文件有重大修改时，必须更新后面年份，如特性扩展，重大重构等。

- 可以只写一个创建年份，后续文件修改则不用更新版权声明。
    
    如：`版权所有 (c) 华为技术有限公司 2018`

- 版权说明可以使用华为子公司，如：

    中文：`版权所有 (c) 海思半导体 2012-2018`
    
    或英文：`Copyright (c) Hisilicon Technologies Co., Ltd. 2012-2018. All rights   reserved.`

- 英文中的 'All rights reserved.' 目前不具有强制法律效力，可省略或根据习惯继续沿用。

举例：

```rust
/*
 * 版权所有 (c) 华为技术有限公司 2012-2018
 * XX 功能实现
 * 注意：
 *      - 注意点 1
 *      - 注意点 2
 */
```

编写版权注释时注意事项：

- 文件头注释应该从文件顶头开始。

    如果包含“关键资产说明”类注释，则应紧随其后。

- 保持统一格式。

    具体格式由项目或更大范围统一制定。格式可参考上面举例。

- 保持版面工整，若内容过长，超出行宽要求，换行时应注意对齐。

    对齐可参考上述例子 '注意点'。

- 首先包含“版权许可”，然后包含其他可先选内容。

    其他选项按需添加，并保持格式统一。

- 不要空有格式，无内容。

    如上述例子，如果 '注意：' 后面无内容，不应编写。

# 3 编程实践

## 3.1 常量

### G.CNS.01 常量类型不应具有内部可变性

**【级别】** 要求

**【描述】**

内部可变性类型包括：`atomics`, `Cell`, `RefCell`, `UnsafeCell`, `Mutex`, `RwLock`, `OnceLock` 等，对 const 变量的修改是无效的，有可能跟程序语义预期结果不符。

**【说明】**

所有 `atomics` 类型可参考: https://doc.rust-lang.org/std/sync/atomic/index.html#structs

**【反例】**

```rust
use std::sync::atomic::{AtomicUsize, Ordering::SeqCst};

// 不符合
const CONST_ATOM: AtomicUsize = AtomicUsize::new(12);

CONST_ATOM.store(6, SeqCst); // 对 const 变量值修改实际是无效的
assert_eq!(CONST_ATOM.load(SeqCst), 12); // 仍为 12
```

**【反例】**

```rust
use core::cell::Cell;

// 不符合
const VAL: Cell<i32> = Cell::new(100);

VAL.set(1);
assert_eq!(VAL.get(), 100); // 仍为原来的数值 100
```

**【反例】**

```rust
use std::sync::Mutex;
use std::sync::RwLock;
use std::sync::OnceLock;

// 不符合
const M: Mutex<u8> = Mutex::new(5);
const R: RwLock<u8> = RwLock::new(5);
const O: OnceLock<u8> = OnceLock::new();

fn main() {
    *M.lock().unwrap() = 10;
    println!("{:?}", M);

    *R.write().unwrap() = 10;
    println!("{:?}", R);

    O.set(10).unwrap();
    println!("{:?}", O);
}
```

### G.CNS.02 宜使用标准库中的预定义常量

**【级别】** 建议

**【描述】**

Rust 中提供了一些特殊常量的定义（例如 [std::f32::consts](https://doc.rust-lang.org/stable/std/f32/consts/index.html)），其精确度通常会比开发者自行定义的高，所以若考虑数值精确度时，宜使用标准库预定义的特殊常量。

**【反例】**

```rust
let min: i8 = -128;
let max: u16 = 65535;

// 不符合
let x = 3.14_f64;
let y = 1_f64 / x;
```

**【正例】**

```rust
let min: i8 = i8::MIN;
let max: u16 = u16::MAX;

let x = std::f64::consts::PI;
let y = std::f64::consts::FRAC_1_PI;

let inf = f32::INFINITY;
let neg_inf = f32::NEG_INFINITY;
```

## 3.2 数据类型

### P.TYP.01 合理选择算术转换方式

**【描述】**

关键字 as 只用于有损转换无法避免时，否则尽可能利用 `From::from` 或 `TryFrom::try_from` 实现无损转换。

**【正例】**

- 考虑是否必须要做有损的算术转换，如非必要，应使用相同类型来避免转换。

```rust
let a: f64 = 64.0;

let b: f64 = a; // 符合
```

**【正例】**

- 在将数据转换为同符号的更宽类型时，建议使用 `from` 转换，代表无损转换：

```rust
let c: u16 = 512;

let p = u64::from(c); // 符合
```

**【正例】**

- 在必须做数据有损的算术转换但不希望数据截断的情况下，使用 `try_from` 保证数据准确性：

```rust
let b: isize = 512;

let y: Result<i8, _> = i8::try_from(b); // 符合
```

**【例外】**

- 在必须做数据有损的算术转换但业务场景允许数据截断，或无法通过 `from` / `try_from` 显式转换时，可继续使用类型强转：

```rust
let a: f64 = 64.0;
let b: i64 = 100000;

let _: f32 = a as f32;
let _: i16 = b as i16;
let _ = 100_u16 as u64;
```

### G.TYP.01 定义局部变量初始化为数值字面量时，应添加明确的类型标识

**【级别】** 要求

**【描述】**

在定义一个局部变量时，如果仅将其初始化为一个数值字面量而不指定具体类型，那么单靠类型推导，整数类型会被默认绑定为 `i32` 类型，而浮点数则默认绑定为 `f64` 类型。这可能导致某些运行时的意外，比如因为类型预期错误，导致应该在编译期发现的问题遗留到运行时，比如导致数据计算溢出等问题。

**【反例】**

```rust
// 期望是 u64 类型，用于统计数据，不考虑溢出问题
let mut count = 0;

while (/*...*/) {
    // 每秒执行一次网络流量统计
    let bytes: i32 = /* get packet size */
    // 不符合： u64 不会溢出，而 i32 可能会溢出。此处本应该编译报错。
    count += bytes;
}
```

**【反例】**

```rust
// 不符合
let i = 10; // i32
let f = 1.23; // f64
```

**【正例】**

```rust
// 符合
let i: u32 = 10;
let f: f32 = 1.23;
// 符合
let i = 10u32;
let f = 1.23f32;
```

### 3.2.1 布尔

#### G.TYP.BOL.01 不宜使用块表达式作为控制表达式

**【级别】** 要求

**【描述】**

使用块表达式作为控制表达式，易引入带副作用的函数调用，导致程序运行逻辑和预期不符，代码的可读性也同步变差。

Rust中的控制表达式包括：

- if语句。
- while语句。
- match语句。

**【反例】**

```rust
// 不符合：可读性差，条件表达式容易被误认为是执行分支
if {
    let file_name = get_input_from_user();
    let cur_dir = std::env::current_dir().unwrap();
    let file_path = cur_dir.join(file_name);
    std::fs::OpenOptions::new()
        .create_new(true)
        .open(file_path)
        .is_ok()
} {
    // ...
}
```

**【正例】**

```rust
fn create_new_user_file() -> bool {
    let file_name = get_input_from_user();
    let cur_dir = std::env::current_dir().unwrap();
    let file_path = cur_dir.join(file_name);
    std::fs::OpenOptions::new()
        .create_new(true)
        .open(file_path)
        .is_ok()
}

// 符合
if create_new_user_file() {
    // ...
}
```

**【反例】**

```rust
fn main() {
    // 不符合：使用块表达式
    match {
        println!("side effect");
        std::env::var("PATH")
    } {
        Ok(_) => (),
        _ => (),
    }
}
```

**【正例】**

```rust
fn main() {
    // 符合
    match std::env::var("PATH") {
        Ok(_) => (),
        _ => (),
    }
}
```

#### G.TYP.BOL.02 不宜将布尔变量和布尔字面量进行比较

**【级别】** 建议

**【描述】**

条件表达式中类似 `x == true`, `x != true`, `x < true`, `x > false` 等是非必要的表达方式，宜直接使用布尔变量, 如 `x`, `!x`。

**【反例】**

```rust
// 不符合
if x == true {}
if y == false {}

assert_eq!("a".is_empty(), false);
assert_ne!("a".is_empty(), true);
```

**【正例】**

```rust
// 符合
if x {}
if !y {}

assert!(!"a".is_empty());
```

#### G.TYP.BOL.03 && 和 || 操作符的右侧操作中不应包含副作用

**【级别】** 建议

**【描述】**

逻辑与（&&）、逻辑或（||）表达式中的右侧操作是否被执行，取决于左操作的求值结果，当左操作的求值结果可以得出整个逻辑表达式的结果时，不会再计算右操作的结果。
如果右操作包含副作用，则不能确定是否确实发生了副作用。

**【说明】**

副作用是指对执行状态产生影响，包括：修改对象、修改文件等。在某些情况下副作用会给程序带来不必要的麻烦，降低程序的可读性，其产生的错误也难以查找。

**【反例】**

```rust
// 不符合
if flag > 0 || fs::remove_file("example.txt").is_ok() {
    // ...
}
```

**【正例】**

```rust
// 符合
if flag > 0 {
    // ...
} else {
    let removed = fs::remove_file("example.txt").is_ok();
    if removed {
        // ...
    }
}
```

### 3.2.2 字符

#### G.TYP.CHR.01 整数到字符的类型转换应注意有效范围

**【级别】** 建议

**【描述】**

在 Rust 中，字符类型 `char` 本质上是一个 `Unicode` 码点(标量值)，4 个字节大小。`char` 码点的有效范围为 `[0, 0xD7FF]` 和 `[0xE000, 0x10FFFF]`。

`u8` 类型可以直接转换为 `char`，而 `u32` 类型转换为 `char` 是可能失败的。 

**【反例】**

```rust
// 不符合
let _: char = unsafe { std::mem::transmute(0x110000) };

// 不符合
let _: char = unsafe { std::mem::transmute(0xDE01) };
```

**【正例】**

```rust
let c = char::from(97u8); // 符合
assert_eq!(c, 'a');

let c = char::from_u32(0x2764); // 符合
assert_eq!(c, Some('❤'));
```

### 3.2.3 数字

#### G.TYP.INT.01 整数类型的算数运算，宜使用 `checked_`, `saturating_`, `overflowing_`, `wrapping_` 为前缀的方法

**【级别】** 建议

**【描述】**

使用整数计算时需结合场景和业务考虑，如发生溢出、回绕或截断时，会产生未定义行为或不符合预期的结果，比如在计算时间或数组索引时发生整数溢出会导致错误结果或 Panic。

在 Rust 标准库中，提供 `add` / `checked_add` / ` saturating_add` / `overflowing_add` / `wrapping_add` 等系列方法，可结合场合选择合适的方法：

- `checked_*` 系列函数返回 `Option`，一旦发生溢出则返回 None。
- `saturating_*` 系列函数返回类型是整数，如果溢出，则给出该类型可表示范围的“最大/最小”值。
- `wrapping_*` 系列函数则是直接抛弃已经溢出的最高位，将剩下的部分返回。即返回二进制补码结果。
- `overflowing_*` 系列函数返回二进制补码结果以及指示是否发生溢出的布尔值。

**【说明】**

Rust 整数溢出和回绕情况补充说明：

- 缺省情况下 Rust 编译器生成的代码在整数溢出时会导致程序 `panic`，用户可以通过显式设置编译选项 `-C overflow-checks=false` 来关闭此行为，使其行为等价于 `wrapping_` 系列方法的行为。 此外编译优化选项 `-C opt-level` 取值不为 0 时，也会自动设置 `-C overflow-checks=false`。

- 在使用 `Cargo` 来构建程序时，`Cargo` 提供了 `Debug` 和 `Release` 两种构建模式，这两种模式对应不同的编译选项，其中 `Release` 模式下缺省会设置编译选项 `-C opt-level=2`，因此对于`Cargo` 的用户体现出 `Debug` 模式下整数溢出会导致 `panic`，而 `Release` 模式下整数溢出等同 `wrapping_` 系列方法这种差异。

- 整数溢出（Overflow）：是指在计算机中使用固定位数的二进制来表示整数时，当进行加减乘等运算时，如果得到的结果超出了该类型的范围，发生溢出现象。例如，如果使用 u8 类型的整数表示范围为 0 - 255 的无符号整数，当进行加法运算时，如果两个加数之和超过了 255，就会发生溢出现象，结果会变为 0 - 254 范围内的某个值，而不是正确的结果。

- 整数回绕（Wraparound）：是指当一个整数超出了其类型的取值范围时，其值会被回绕到类型的取值范围内的最小值或最大值。例如，在使用 u8 类型表示无符号整数时，如果对一个值为 255 的整数进行加 1 操作，得到的结果会变为 0，因为 0 是 u8 类型的最小值，此时发生了回绕现象。

**【反例】**

```rust
// 不符合
assert_eq!((-5i32).abs(), 5);
assert_eq!(100i32+1, 101);

// -C opt-level=0 或 -C overflow-checks=true 或 未设置这些选项都会因为整数溢出导致panic
// -C opt-level=1 或 -C overflow-checks=false 会等同wrapping_add的结果
fn test_integer_overflow() {
    let x = || { 255_u8 };
    println!("x={}", x() + 1);
}
```

**【正例】**

```rust
// 符合
assert_eq!((-5i32).checked_abs(), Some(5));
assert_eq!(100i32.saturating_add(1), 101);

fn test_integer_overflow() {
    let x = || { 255_u8 };
    // 符合：输出 x = 0
    println!("x={}", x().wrapping_add(1));
    // 符合：输出 x = 255
    println!("x={}", x().saturating_add(1));
}
```

### 3.2.4 数组

#### G.TYP.SLC.01 宜使用迭代器而非下标遍历切片和数组

**【级别】** 建议

**【描述】**

在 for 循环中使用索引下标访问有可能导致边界错误。

遍历切片和数组时，宜使用迭代器来避免索引访问。

**【反例】**

```rust
let list: &[&str] = &["aa", "bb", "cc"];

// 不符合：人工计算长度选择范围很可能会出错
for i in 0..list.len() {
  let item = list[i];
  // ...
}
```

**【正例】**

```rust
let list: &[&str] = &["aa", "bb", "cc"];

// 符合
for item in list {
  // ...
}
```

#### G.TYP.SLC.02 应保证数组索引在有效范围内

**【级别】** 要求

**【描述】**

Rust 的数组/切片越界访问不会出现内存被越界读写的后果，但会导致 panic。使用索引访问数组的时候需要保证索引值在有效范围。

建议：

- 如果基于单个索引获取数组元素，需提前校验索引有效；或者使用 `get` 方法，越界时返回 `None`。
- 如果需要获取一个切片，需要保证切片的起始索引地址在有效范围内，否则会导致 panic。

**【反例】**

```rust
fn main() {
    let v = vec![1, 2, 3, 4, 5];
    // 不符合：越界访问，Panic
    let does_not_exist = &v[100];

    use std::ops::Index;
    // 不符合：越界访问，Panic
    let does_not_exist = v.index(100);
}
```

**【正例】**

```rust
fn main() {
    fn get_index() -> usize {
        5
    }

    let arr = [1, 2, 3, 4, 5];
    let index = get_index();
    // 符合：校验索引是否越界
    if index >= arr.len() {
        // 错误处理示例，此处产品应根据业务场景，选择合适的处理方式
        panic!("index out of bounds");
    }

    let _ = arr[index]; 
}
```

### 3.2.5 字符串

#### G.TYP.STR.01 在实现 `Display` trait 时不应调用 `to_string()` 方法

**【级别】** 要求

**【描述】**

对某一类型实现 [`Display`](https://doc.rust-lang.org/std/fmt/trait.Display.html) trait 的同时会自动为其实现 `ToString` trait。此时若调用 `to_string` 的话，将会造成无限递归以及栈溢出。

**【反例】**

```rust
use std::fmt;

struct Structure(i32);
impl fmt::Display for Structure {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.to_string()) // 不符合
    }
}
```

**【正例】**

```rust
use std::fmt;

struct Structure(i32);
impl fmt::Display for Structure {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0) // 符合
    }
}
```

### 3.2.6 智能指针

#### G.TYP.PTR.01 `Rc`、`Arc`、`Box` 不宜直接相互嵌套使用

**【级别】** 建议

**【描述】**

不合理的智能指针嵌套使用容易造成多级指针引用，导致内存访问效率不佳。

建议使用 `Rc<T>` 和 `Arc<T>` 来替代 `Rc<Box<T>>` 和 `Arc<Box<T>>` 类型。

例外：本条规则不限制使用复杂数据结构导致的间接指针嵌套。

**【反例】**

```rust
use std::rc::Rc;
fn main() {
    let val = Rc::new(Box::new(0i32)); // 不符合
    println!("{val:?}");
}
```

**【正例】**

```rust
use std::rc::Rc;
fn main() {
    let val = Rc::new(0i32); // 符合
    println!("{val:?}");
}
```

**【例外】**

```rust
use std::sync::Arc;

struct Node {
    value: i32,
    next: Option<Box<Node>>,
}

fn main() {
    // 符合：使用复杂数据结构导致的间接指针嵌套
    let node = Arc::new(Node {
        value: 1,
        next: Some(Box::new(Node {
            value: 2,
            next: None,
        })),
    });
}
```

## 3.3 表达式与流程控制

### G.CTF.01 宜优先使用模式匹配而非判断后再取值

**【级别】** 建议

**【描述】**

使用 Rust 语言的模式匹配特性会让代码更优雅和简洁，在解构数据结构时，宜使用模式匹配方式，而不是通过 `if` 判断后再取值。

**【反例】**

 ```rust
let opt: Option<i32> = Some(2);
// 不符合
if opt.is_some() {
    let value = opt.unwrap();
    // ...
}

let list: &[f32] = &[1.23];
// 不符合
if !list.is_empty() {
    let first = list[0];
    // ...
}
 ```

**【正例】**

```rust
// 符合
if let Some(value) = opt {
    // ...
}
// 符合
if let [first, ..] = list {
    // ...
}
// 符合：index 为任意 usize 下标
if let Some(val) = list.get(index) {
    // ...
}
```

### G.CTF.02 在 Match 分支的 Guard 语句中不宜使用带有副作用的条件表达式

**【级别】** 建议

**【描述】**

Guard 的条件表达式不应该携带副作用。当分支使用 `|` 组合多个模式时，Guard 会针对每个匹配成功的子模式各执行一次，直到某次返回 `true` 为止，因此同一个 Guard 可能被执行多次。

**【说明】**

副作用是指对执行状态产生影响，包括：修改对象、修改文件等。在某些情况下副作用会给程序带来不必要的麻烦，其产生的错误十分难以查找，并降低程序的可读性。

**【反例】**

```rust
use std::cell::Cell;
fn main() {
    let i: Cell<i32> = Cell::new(0);
    let opt = Some(1);
    // 不符合：代码最终会输出两次 "add 1"
    match opt {
        // 这个条件表达式带有副作用：打印并修改了变量 i 内部的值。
        // Some(1) 与 Some(_) 两个子模式都匹配，Guard 返回 `false`，因此执行两次
        Some(1) | Some(_) if condition(&i) => {}
        _ => {}
    }
    assert_eq!(i.get(), 2);
}

// 带有副作用，匹配时多次执行可能会出现预想不到的逻辑问题
fn condition(i: &Cell<i32>) -> bool {
    println!("add 1");
    i.set(i.get() + 1); // 如果函数被执行两次，这里也会被设置两次
    false
}
```

**【正例】**

```rust
use std::cell::Cell;
fn main() {
    let i: Cell<i32> = Cell::new(0);
    let opt = Some(1);
    // 符合：代码最终输出一次 "add 1"
    match opt {
        // 注意有副作用的函数被移动到了Guard语句之后调用以作判断 
        Some(1) => if condition(&i) {}
        Some(_) => if condition(&i) {}
        _ => {}
    }
    assert_eq!(i.get(), 1);
}

// 带有副作用，匹配时多次执行可能会出现预想不到的逻辑问题
fn condition(i: &Cell<i32>) -> bool {
    println!("add 1");
    i.set(i.get() + 1); // 如果函数被执行两次，这里也会被设置两次
    false
}
```

### G.CTF.03 宜确保循环或递归能够安全退出

**【级别】** 建议

**【描述】**

在应用程序中，一个重复提供服务的逻辑循环，应当包含相应的退出机制，并且将资源正确释放后安全退出。

循环应能安全退出，递归也应能安全结束。

- 有意常驻、不会返回的循环（如服务主循环），应将所在函数的返回类型声明为 `!`，明确表达意图；需要支持停机时，应提供退出信号（如关闭标志、通道关闭）并在退出前释放资源。
- `panic!`、`std::process::exit` 不属于安全退出：后者不会执行对象的析构。

**【反例】**

```rust
fn main() {
    let mut counter = 0;

    loop {
        counter += 1;
        // 不符合：循环无退出条件
    }
}
```

```rust
// 不符合：递归没有终止条件
fn depth(n: u64) -> u64 {
    depth(n + 1)
}
```

**【正例】**

```rust
fn main() {
    let mut counter = 0;

    loop {
        counter += 1;
        // 符合：循环包含退出条件
        if should_exit(counter) {
            break;
        }
    }
}

fn should_exit(count: u32) -> bool {
    count >= 5
}
```

```rust
// 符合：每次递归 n 都减小，最终到达终止条件 n == 0
fn depth(n: u64) -> u64 {
    if n == 0 {
        return 0;
    }
    1 + depth(n - 1)
}
```

```rust
// 符合：有意常驻的服务循环，用 `!` 返回类型显式声明不会返回
fn serve(listener: std::net::TcpListener) -> ! {
    loop {
        if let Ok((stream, _)) = listener.accept() {
            handle(stream);
        }
    }
}

fn handle(_stream: std::net::TcpStream) {
    // ...
}
```

### G.EXP.01 避免条件表达式永远为 `true` 或 `false`

**【级别】** 建议

**【描述】**

条件表达式永远为 `true` 或 `false` 通常是因为代码编写错误。

**【反例】**

```rust
let x = 2;
if (x & 1) == 2 { // 不符合：该表达式会永远是 false
     // ...
}

if (x & 3) < 4 { // 不符合：判断表达式结果永远为 true
     // ...
}

let y = 0;
if (x < y) && false { // 不符合：判断表达式结果永远为 false
    // ...
}

if x > 10 && x < 5 { // 不符合：区间矛盾，永远为 `false`
    // ...
}
```

**【正例】**

```rust
let x = 2;
// 符合
if x == 2 {
    // ...
}
```

### G.EXP.02 用括号明确表达式的操作顺序，避免过分依赖默认优先级

**【级别】** 建议

**【描述】**

宜使用括号强调表达式的优先级顺序，增加可读性，防止开发者因不熟悉默认的优先级而导致错误。

**【反例】**

```rust
1 << 2 + 3 // 不符合
-1i32.abs() // 不符合
```

**【正例】**

```rust
(1 << 2) + 3  // 符合
(-1i32).abs() // 符合
```

## 3.4 函数与闭包

### G.FUD.01 内存拷贝代价大的参数应按地址传递

**【级别】** 建议

**【描述】**

Rust 中按值传递参数（包括所有权转移）时，语义上会按位拷贝该类型自身大小的内存，不包括其指向的堆数据；编译器可能消除该拷贝，但不作保证。因此需要考虑内存拷贝的代价，设计合理的参数类型：

- 对于输入参数，拷贝代价小的类型使用值传递，拷贝代价大的类型传递只读引用。类型大小可通过 `std::mem::size_of::<T>()` 获取，超过 256 字节的类型可视为拷贝代价大。
- 对于返回类型，如果拷贝代价大，宜设计传递可写借用参数并返回它。

**【反例】**

对于输入参数：

```rust
// 不符合
fn func(val: [i32; 1000]);
```

**【正例】**

对于输入参数：

```rust
// 符合
fn func(val: &[i32]); 
```

**【反例】**

对于返回类型：

```rust
// 不符合：`Self` 拷贝代价大时，每次调用都可能拷贝整个 `Self`
fn set_property(self, name: &str, value: &str) -> Self; 
```

**【正例】**

对于返回类型：

```rust
// 符合：传递可写借用参数并返回它，适合链式调用的场景
fn set_property(&mut self, name: &str, value: &str) -> &mut Self;
```

### G.FUD.02 宜合理使用 Result 类型或 must_use 修饰，保证用户有效处理返回值

**【级别】** 建议

**【描述】**

Rust 中有以下方法可以在用户忽略函数返回值的时候出现编译告警：

- 返回值类型是 `Result`。
- 函数定义增加 #[must_use] 修饰。
- 函数返回的专有数据类型增加 #[must_use] 修饰。

**【说明】**

以下写法会使上述告警失效：

- `let _ = f();` 显式丢弃返回值；
- `f().ok();` 把 `Result` 转为 `Option` 后丢弃；
- 类型上的 `#[must_use]` 只在函数直接返回该类型时生效；返回 `Option<T>` 等包装类型时不生效，此时宜在函数上标注 `#[must_use]`。

**【反例】**

```rust
// 定义方：foo1 已标注 #[must_use]
#[must_use]
fn foo1() -> i32 {
    0
}

fn caller() {
    // 不符合（调用方）：用 let _ = 显式丢弃了 must_use 返回值，编译器不再告警
    let _ = foo1();
}
```

**【正例】**

```rust
// 符合（定义方）：函数标注 #[must_use]，调用方忽略返回值时编译器会告警
#[must_use]
fn foo1() -> i32 {
    // ...
    0
}

// 符合（定义方）：返回的专有类型标注 #[must_use]
#[must_use]
struct MyError(i32, i32);

fn foo2() -> MyError {
    // ...
    MyError(0, 0)
}

fn caller() {
    // 符合（调用方）：接收并使用了 foo1 的返回值
    let value = foo1();
    println!("value: {value}");
}
```

## 3.5 泛型 与 trait

### G.TRA.01 在实现相等性、排序和散列类 trait 时，应保证一致性

**【级别】** 要求

**【描述】**

`PartialEq`、`Eq`、`Hash`、`PartialOrd`、`Ord` 手写时必须同时满足：

1. `a == b ⇒ hash(a) == hash(b)`（`PartialEq`/`Eq` 与 `Hash`；仅单向，哈希允许碰撞）
2. `a.partial_cmp(&b) == Some(a.cmp(&b))`（`PartialOrd` 与 `Ord`；同时实现时，宜将 `partial_cmp` 写为 `Some(self.cmp(other))`）
3. `a == b ⇔ a.partial_cmp(&b) == Some(Ordering::Equal)`（`PartialEq` 与 `PartialOrd`）；实现了 `Ord` 时，同样要求 `a == b ⇔ a.cmp(&b) == Ordering::Equal`（`Eq` 与 `Ord`）
4. 若类型实现了 `Borrow`（例如 `String` 可借用为 `str`），则借用前后必须表现一致，即把 `x` 换成 `x.borrow()` 后：相等结论不变（`x == y` 与 `x.borrow() == y.borrow()` 同真同假）；排序结论不变（`x.cmp(&y)` 与 `x.borrow().cmp(y.borrow())` 相同）；哈希值不变（`hash(x)` 与 `hash(x.borrow())` 相同）。否则 `HashMap<String, V>` 这类容器无法用 `&str` 正确查找

通常情况下，可以通过 `derive` 属性宏来自动实现这些 traits。但相等性，排序和散列在不同应用场景可能存在不同的定义，又或是因为依赖的某种类型未实现其中一个 trait 而不能使用 `derive` 时，就需要开发者手动实现以上 traits，这时就要注意保持一致性。

一旦不一致，可能导致出现非预期的函数行为，例如 `HashMap` / `HashSet` 查找失败，`BTreeMap` / `BTreeSet` 把不相等的元素当作同一元素丢弃。

**【反例】**

```rust
// 不符合：雇员(`Employee`)类型包括 uid 及 name，通过宏自动实现的 `Hash` 会同时考虑所有成员变量，
// 但是手动实现的 `PartialEq` trait 仅考虑到了 uid，这将会导致结果不一致。
// 因为当两个雇员(假设为 a 和 b)的 name 不同，但 uid 相同时, `a == b` 为 true, 但 `hash(a)` 不等于 `hash(b)`
#[derive(Hash, Eq)]
struct Employee {
    uid: u32,
    name: String,
}

impl PartialEq for Employee {
    fn eq(&self, other: &Self) -> bool {
        self.uid == other.uid
    }
}
```

**【正例】**

```rust
// 符合：都使用 `derive` 自动实现
#[derive(Hash, PartialEq, Eq)]
struct Employee {
    uid: u32,
    name: String,
}
```

或

```rust
use std::hash::{Hash, Hasher};

#[derive(Eq)]
struct Employee {
    uid: u32,
    name: String,
}

// 符合：都使用手动实现的方式且保证一致性，
// 与 `hash` 一样都使用 uid 作为唯一条件
impl PartialEq for Employee {
    fn eq(&self, other: &Self) -> bool {
        self.uid == other.uid
    }
}

impl Hash for Employee {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.uid.hash(state)
    }
}
```

**【反例】**

```rust
use std::cmp::Ordering;

#[derive(Ord, PartialEq, Eq)]
struct Employee {
    uid: u32,
    name: String,
}

// 不符合：`Ord` 和 `PartialOrd` 的实现不一致
impl PartialOrd for Employee {
    fn partial_cmp(&self, other: &Employee) -> Option<Ordering> {
       Some(self.uid.cmp(&other.uid))
    }
}
```

```rust
use std::cmp::Ordering;

// 不符合：derive 的 `PartialEq`/`Eq` 比较全部字段，而 `Ord` 只比较 uid。
// uid 相同、name 不同时 a != b，但 a.cmp(&b) == Ordering::Equal，
// 放入 `BTreeSet` 时其中一个会被当作重复元素丢弃
#[derive(PartialEq, Eq)]
struct Employee {
    uid: u32,
    name: String,
}

impl PartialOrd for Employee {
    fn partial_cmp(&self, other: &Employee) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Employee {
    fn cmp(&self, other: &Self) -> Ordering {
        self.uid.cmp(&other.uid)
    }
}
```

**【正例】**

```rust
// 符合：都使用 `derive` 自动实现
#[derive(PartialOrd, Ord, PartialEq, Eq)]
struct Employee {
    uid: u32,
    name: String,
}
```

或

```rust
use std::cmp::Ordering;

#[derive(Eq)]
struct Employee {
    uid: u32,
    name: String,
}

// 符合：相等性与排序都只以 uid 为准，且 `partial_cmp` 复用 `cmp`
impl PartialEq for Employee {
    fn eq(&self, other: &Self) -> bool {
        self.uid == other.uid
    }
}

impl PartialOrd for Employee {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Employee {
    fn cmp(&self, other: &Self) -> Ordering {
        self.uid.cmp(&other.uid)
    }
}
```

### G.TRA.02 宜实现 `From` 而不是 `Into`

**【级别】** 建议

**【描述】**

优先为类型实现 `From` 而非 `Into`。因为实现了 `From`，`Into` 也会被自动实现。并且在错误处理的时候，`?` 操作符会通过调用 `From` 实现自动进行错误类型转换。
但是在泛型限定上，优先 `Into` 。

**【反例】**

```rust
struct StringWrapper(String);
// 不符合
impl Into<StringWrapper> for String {
    fn into(self) -> StringWrapper {
        StringWrapper(self)
    }
}
```

**【正例】**

```rust
struct StringWrapper(String);
// 符合
impl From<String> for StringWrapper {
    fn from(s: String) -> StringWrapper {
        StringWrapper(s)
    }
}
```

## 3.6 错误处理

### G.ERR.01 应正确处理返回类型 `Option` 和 `Result`

**【级别】** 建议

**【描述】**

对于返回类型为 `Option` 或 `Result` 的函数，应使用不会导致 panic 的方法显式处理返回的 `None` / `Err` 值。

处理方法包括但不限于：

- 使用 `match` 语句。
- 使用 `unwrap_or` / `unwrap_or_else` / `unwrap_or_default` 等函数（传入的闭包本身不应 panic）。
- 在当前函数返回值同为`Option`或`Result`类型时，使用 `?` 语法糖。

例外：如下两种场景可直接调用 `unwrap` / `expect`，宜优先使用 `expect` 并在消息中说明为何不会失败：

- 调用返回 `Option` / `Result` 函数之前通过输入参数的提前校验，可以保证返回值一定不会是 `None` / `Err`。
- 业务模块的设计要求对于返回 `None` / `Err` 的情况 panic，依赖更高层的可靠性机制检测故障并实现故障恢复。

**【反例】**

```rust
use std::fs;

const CONFIG_PATH: &str = "/etc/app/config.toml";

pub fn main() {
    // 不符合：配置文件缺失或无权限时直接 panic，无法区分错误原因
    let config_content = fs::read_to_string(CONFIG_PATH).unwrap();
    // ...
}
```

**【正例】**

```rust
use std::fs;
use std::io::ErrorKind;

const CONFIG_PATH: &str = "/etc/app/config.toml";

pub fn main() {
    // 符合：针对不同情况做出应对措施，有利于定位错误
    let config_content = match fs::read_to_string(CONFIG_PATH) {
        Ok(content) => content,
        Err(e) => {
            match e.kind() {
                ErrorKind::NotFound => {
                    // 处理文件找不到的情况
                }
                ErrorKind::PermissionDenied => {
                    // 处理文件权限不够的情况
                }
                _ => {
                    // 处理其它错误情况
                }
            }
            return;
        }
    };

    // ...
}
```

## 3.7 模块

### G.MOD.01 导入模块中的类型或函数时，应避免直接使用通配符

**【级别】** 建议

**【描述】**

使用通配符导入会污染命名空间，比如导入相同命名的函数或类型。为了避免这种情况，使用导入的类型或函数时需要带模块名前缀。有两个例外：当一个 crate 提供了 prelude 时，可以用 `prelude::*`；测试模块中可以用 `use super::*` 导入被测模块。

对于标准库中，很多人都熟知的类型 ，比如 `Arc/ Rc/ Cell/ HashMap` 等 ， 可以导入它们直接使用。

但是对于可能引起困惑的函数，比如 `std::ptr::replace` 和 `std::mem::replace` ，在使用它们的时候，就必须得带上模块前缀。

使用一些第三方库中定义的类型或函数，也建议带上 crate 或模块前缀。如果太长的话，可以考虑使用 `as` 或 `type` 来定义别名。

以上考虑都是为了增强代码的可读性、可维护性。

**【反例】**

```rust
use std::sync::Arc;
use std::mem::*;
use std::ptr::*;

fn main() {
    let foo = Arc::new(vec![1.0, 2.0, 3.0]); // 直接使用 Arc
    let a = foo.clone();

    let mut rust = vec!['b', 'u', 's', 't'];
    
    let b = unsafe {
        // 不符合：std::mem 与 std::ptr 都有 replace，通配导入后名字冲突，
        // 直接调用 replace 会编译报错（E0659：`replace` is ambiguous）
        replace(&mut rust[0], 'r')
    };
}
```

**【正例】**

```rust
use std::sync::Arc;
use std::{mem, ptr};

fn main() {
    let foo = Arc::new(vec![1.0, 2.0, 3.0]); // 直接使用 Arc
    let a = foo.clone();

    
    let mut rust = vec!['b', 'u', 's', 't'];
    
    let b = unsafe {
        // 符合
        // 需要带上 ptr 前缀，因为 `std::mem::replace` 也有同样的效果
        ptr::replace(&mut rust[0], 'r')
    };
    // 符合：mem::replace 同样带上 mem 前缀
    let c = mem::replace(&mut rust[1], 'U');
}
```

## 3.8 宏

### G.MAC.01 不应通过宏将 unsafe 代码伪装为 safe 代码

**【级别】** 要求

**【描述】**

不应通过宏将 unsafe 代码伪装为 safe 代码，以此来规避 Rust 静态分析检查。

宏展开后的代码运行在调用方的上下文中。如果宏内部的 unsafe 块没有自行保证其安全前提，调用方就可以不写 unsafe 而执行不安全操作。常见情形例如：

- 把调用方传入的代码（声明宏的元变量、过程宏的输入）直接展开在 unsafe 块内，传入的任意表达式都会在 unsafe 上下文中执行。应先在 unsafe 块外求值并绑定到局部变量，再在 unsafe 块内使用。
- 把 unsafe 调用包装成 safe 函数，却没有校验该调用的前置条件。

**【反例】**

```rust
// 不符合：用 Rust 的过程宏封装 libc 的函数 printf 来打印一个 C 字符串
// 这个宏的输入参数必须是一个有效的 C 字符串指针，整个宏的使用是不安全的，
// 但是因为过程宏中包括了 unsafe，导致调用过程宏 rprintf 被伪装为 safe 操作
//
// rprintf!(b"hello\0" as *const u8);

#[proc_macro]
pub fn rprintf(input: TokenStream) -> TokenStream {
    let expr = parse_macro_input!(input as syn::Expr);
    // 这里包括 unsafe 代码，这样整个宏可以在 safe 代码中使用
    quote!({
    	unsafe {
            printf(b"%s\n\0" as *const _ as *const u8, #expr);
        }
    }).into()
}
```

**【正例】**

```rust
// 符合：用 Rust 的过程宏封装 libc 的函数 printf 来打印一个 C 字符串
// 这个宏的输入参数必须是一个有效的 C 字符串指针，同时也是调用外部函数，
// 因此必须在 unsafe 代码块中使用
//
// unsafe { rprintf!(b"hello\0" as *const u8) };

#[proc_macro]
pub fn rprintf(input: TokenStream) -> TokenStream {
    let expr = parse_macro_input!(input as syn::Expr);
    // 这里不能包括 unsafe 代码，而是要求整个宏在 unsafe 代码块中使用
    quote!({
       printf(b"%s\n\0" as *const _ as *const u8, #expr);
    }).into()
}
```

**【反例】**

```rust
// 定义声明宏，不经过任何安全检查，将 unsafe 函数伪装为 safe 函数
macro_rules! make_safe {
    ($safe_name:ident, $unsafe_fn:expr) => {
        fn $safe_name() {
            unsafe {
                $unsafe_fn();
            }
        }
    };
}

// 不安全函数，解引用空指针
unsafe fn dangerous_function() {
    let ptr: *const i32 = std::ptr::null();
    println!("value: {}", unsafe { *ptr }); // 解引用空指针，导致未定义行为
}

// 不符合：使用声明宏将 unsafe 函数伪装为 safe 函数
make_safe!(safe_function, dangerous_function);
```

**【例外】**

如果宏（或宏生成的函数）在执行 unsafe 操作前完整校验了它的全部前置条件，并用 `// SAFETY:` 注释说明理由，则可以对外提供 safe 接口：

```rust
macro_rules! checked_get {
    ($slice:expr, $idx:expr) => {{
        // 符合：元变量先在 unsafe 块外求值，调用方传入的表达式仍受正常的安全检查
        let slice: &[_] = $slice;
        let idx: usize = $idx;
        if idx < slice.len() {
            // SAFETY: 上一行已确认 idx < slice.len()，下标在界内
            Some(unsafe { *slice.get_unchecked(idx) })
        } else {
            None
        }
    }};
}
```

**【相关讨论】**

- [RUSTSEC-2020-0011](https://rustsec.org/advisories/RUSTSEC-2020-0011.html)
- [https://github.com/RustSec/advisory-db/issues/275](https://github.com/RustSec/advisory-db/issues/275)
- [https://github.com/rust-lang/unsafe-code-guidelines/issues/278](https://github.com/rust-lang/unsafe-code-guidelines/issues/278)

### 3.8.1 声明宏

#### P.MAC.DCL.01 定义和使用声明宏时，应保证卫生性

**【描述】**

- 标识符（包括变量、泛型、生命周期名称）建议作为宏的参数传递，而不是在宏定义时硬编码，这样可以在提升代码可维护性的同时，让宏的适用范围更广泛。

- 在宏内引用宏外部的 [item](https://doc.rust-lang.org/reference/items.html)，如函数或宏时应使用绝对路径：

    1. 当宏定义和宏内引用的 item 在同一个 crate 中定义时，应该使用 `$crate` 元变量来指代当前被调用宏的路径。
    2. 当宏内引用的 item 在其他 crate 中定义时，宜在宏所在的 crate 中再导出该 crate（如 `#[doc(hidden)] pub use dep as __dep;`），宏内通过 `$crate::__dep::item` 引用。直接写 `::dep::item` 要求调用方也直接依赖该 crate。

**【说明】**

声明宏是半卫生宏，变量标识符在宏内外是隔离的，不会产生命名冲突，符合卫生性。但是在宏内定义的泛型及生命周期标识符的做法是不卫生的。

> 卫生宏定义请参考 [卫生宏 WiKi](https://zh.wikipedia.org/zh-hans/%E5%8D%AB%E7%94%9F%E5%AE%8F) 。

**【反例】**

```rust
// 使用宏为带生命周期的类型实现 impl
macro_rules! impl_for {
    ($name:ty) => {
        // 不符合：这里使用的 'a 是宏内部定义
        impl<'a> $name { 
            fn get(&self) -> i32 {
                *self.0
            }    
        }
    };
}

struct Foo<'a>(&'a i32);
// 程序能正常编译运行，但宏内外的 'a 被共用，不卫生，也不利于可维护性
impl_for!(Foo<'a>);
// ...

struct Bar<'b>(&'b i32);
// 但如果要用相同的宏为生命周期为 'b 的类型实现 impl 时,
// 编译会失败: use of undeclared lifetime name `'b`
impl_for!(Bar<'b>);
```

**【正例】**

```rust
// 使用宏为带生命周期的类型实现 impl
macro_rules! impl_for {
    // 符合：这里不直接使用宏内部定义的 'a ，而是通过 $lifetime 从外部传入的，
    // 从而避免因宏不卫生引发的问题
    ($name:ty, $lifetime:tt) => {
        impl<$lifetime> $name { 
            fn get(&self) -> i32 {
                *self.0
            }    
        }
    };
}

struct Foo<'a>(&'a i32);
impl_for!(Foo<'a>, 'a); // 这里的 'a 是从宏外部传入到宏内

struct Bar<'b>(&'b i32);
impl_for!(Bar<'b>, 'b); // 同时，宏的适用范围更加广泛
```

**【反例】**

```rust
// 宏定义在 crate a（包名 helper_macro）中
#[macro_export]
macro_rules! helped {
    () => { helper!() } // This might lead to an error due to 'helper' not being in scope.
}

#[macro_export]
macro_rules! helper {
    () => { () }
}

// 在 crate b 中使用 crate a 的两个宏
// 注意：`helper_macro::helper` 并没有导入进来
use helper_macro::helped;

fn unit() {
   // Error! 这个宏会出现问题，因为 helped 宏内部调用的 helper 宏的路径会被编译器认为是在当前的 crate b 中
   helped!();
}
```

**【正例】**

```rust
// 宏定义在 crate a（包名 helper_macro）中
#[macro_export]
macro_rules! helped {
    () => { $crate::helper!() }
}

#[macro_export]
macro_rules! helper {
    () => { () }
}

// 在crate b 中使用 crate a 的两个宏
// 注意：`helper_macro::helper` 并没有导入进来
use helper_macro::helped;

fn unit() {
   // OK! 这个宏能运行通过，因为 `$crate` 正确地展开成 `helper_macro` 所在的 crate a 的路径（而不是使用者 crate b 的路径）
   helped!();
}
```

**【反例】**

```rust
// 宏定义在 crate a（包名 helper_macro）中，helper_macro 依赖 crate helper_dep
#[macro_export]
macro_rules! answer {
    // 不符合：::helper_dep 按调用方的依赖解析
    () => { ::helper_dep::value() };
}

// crate b 只依赖 helper_macro，没有直接依赖 helper_dep
pub fn use_it() -> i32 {
    // Error! 编译失败：could not find `helper_dep` in the list of imported crates
    helper_macro::answer!()
}
```

**【正例】**

```rust
// 宏定义在 crate a（包名 helper_macro）中，helper_macro 依赖 crate helper_dep
// 符合：在 helper_macro 中再导出 helper_dep，宏内通过 $crate 引用
#[doc(hidden)]
pub use helper_dep as __dep;

#[macro_export]
macro_rules! answer {
    () => { $crate::__dep::value() };
}

// crate b 只依赖 helper_macro
pub fn use_it() -> i32 {
    // OK! $crate::__dep 总能解析到 helper_macro 再导出的 helper_dep，调用方无需直接依赖它
    helper_macro::answer!()
}
```

#### G.MAC.DCL.01 编写宏匹配规则时，宜遵从匹配范围从小至大的顺序

**【级别】** 建议

**【描述】**

因为声明宏中，是按规则的编写顺序来匹配的。当第一个规则被匹配到，后面的规则将永远不会匹配到。
所以，编写声明宏规则时，需要先写匹配范围最小的，最具体的规则，然后逐步编写匹配范围更广泛的规则。

参考 [The Little Book of Rust Macros](https://danielkeep.github.io/tlborm/book/mbe-min-captures-and-expansion-redux.html)。

**【反例】**

```rust
// 不符合：`$($other:tt)*` 匹配条件在这个宏定义中匹配范围最大却放在了第一位。
macro_rules! match_tokens {
    // 可能会导致调用时代码被错误地匹配到了这一条规则。
    ($($other:tt)*) => {"got something else"};

    ($a:tt + $b:tt) => {"got an addition"};

    ($i:ident) => {"got an identifier"};
}

// 以下的三种语法：`caravan`, `3 + 6`, `5` 均被匹配为该宏的同一条规则
assert_eq!(
    format!("{},{},{}",
        match_tokens!(caravan),
        match_tokens!(3 + 6),
        match_tokens!(5)
    ),
    "got something else,got something else,got something else"
);
```

**【正例】**

```rust
// 符合：匹配范围从小到大
macro_rules! match_tokens {
    ($a:tt + $b:tt) => {"got an addition"};

    ($i:ident) => {"got an identifier"};

    ($($other:tt)*) => {"got something else"};
}

// 匹配合理，宏将 `caravan` 识别为 identifier, `3 + 6` 识别为 addition, `5` 识别为 something else
assert_eq!(
    format!("{},{},{}",
        match_tokens!(caravan),
        match_tokens!(3 + 6),
        match_tokens!(5)
    ),
    "got an identifier,got an addition,got something else"
);
```

### 3.8.2 过程宏

#### P.MAC.PRO.01 定义和使用过程宏时，应保证卫生性

**【描述】**

过程宏在展开时，有时可能会直接引用输入代码中的标识符（变量、函数名等）。如果过程宏引入了与周围代码冲突的标识符，就会导致不卫生的情况。

要避免不卫生的情况，包括以下常用方法：

- 宏内部使用的局部变量，用 `Span::mixed_site()` 生成标识符（如 `quote_spanned!(Span::mixed_site()=> ...)`），获得与声明宏相同的局部变量卫生性。
- 无法使用 `mixed_site` 时，确保宏生成代码的符号与外部有差异，如增加 `__` 前缀。
- 对库中程序项使用绝对路径。

**【反例】**

```rust
// crate guide
#[proc_macro]
pub fn my_macro(input: TokenStream) -> TokenStream {
    let expanded = quote! {
        // 不符合：直接使用外部的变量 x
        x = 999;
        // 不符合: 宏内定义的变量 local 被外部使用
        let local = "hello";

        // ...
    };
    expanded.into()
}

// crate b
fn main() {
    let mut x = 0;
    let local = "";

    guide::my_macro!();

    assert_eq!(x, 999);
    assert_eq!(local, "hello");
}
```

**【正例】**

```rust
use proc_macro2::{Span, TokenStream as TokenStream2};
use quote::quote_spanned;

#[proc_macro]
pub fn my_macro(input: TokenStream) -> TokenStream {
    // 调用方传入的标识符保留调用方的 span，仍然指向调用方的变量
    let target: TokenStream2 = input.into();
    let expanded = quote_spanned! {Span::mixed_site()=>
        // 符合：宏要修改的变量由调用方显式传入；若在这里直接写 x = 999;，
        // mixed_site 下的 x 找不到调用方的 x，编译报错（E0425）
        #target = 999;
        // 符合：mixed_site 生成的局部变量对调用方不可见，也不会遮蔽调用方的同名变量
        let local = "hello";

        // ...
    };
    expanded.into()
}

// crate b
fn main() {
    let mut x = 0;
    let local = "";

    guide::my_macro!(x); // 显式把 x 交给宏

    assert_eq!(x, 999);  // 修改是调用方明确要求的
    assert_eq!(local, ""); // 宏内的 local 没有泄漏
}
```

## 3.9 其他

### G.OTH.01 禁止代码中包含公网地址

**【级别】** 要求

**【描述】**

对产品发布的软件（包含软件包/补丁包）中包含的公网地址（包括公网IP地址、公网 URL 地址/域名、邮箱地址）要求如下：

1. 禁止包含用户界面不可见、或产品资料未描述的未公开的公网地址。
2. 已公开的公网地址禁止写在代码或者脚本中，可以存储在配置文件或数据库中。

对于开源/第三方软件自带的公网地址必须至少满足上述第 1 条公开性要求。

**【例外】**

对于标准协议中必须指定公网地址的场景可例外，如 soap 协议中函数的命名空间必须指定的一个组装的公网 URL、http 页面中包含 w3.org 网址等。

### G.OTH.02 禁止在用户界面、日志中暴露不必要信息

**【级别】** 要求

**【描述】**

如果攻击者获取了系统所涉及操作系统、中间件、应用程序、实现细节（如函数调用栈、SQL语句等）、密钥、银行账号、会话标识等信息，则会根据这些信息进行有针对性的漏洞分析或直接窃取有价值信息，
因此，我们要尽量避免将系统上的信息暴露给任何潜在的攻击者。具体而言：

- 禁止在未经认证的用户界面明文显示软件信息。
- 禁止在用户界面、日志中明文显示或打印会话标识、敏感个人信息。
- 禁止在用户界面、日志中明文、密文显示或打印认证凭据（口令/私钥/预共享密钥）。若因为特殊原因必须要显示或记录的，可用固定长度的星号（*）替换全部的认证凭据。

下表列出了已识别的数据类型（其中“用户界面”包括操作界面、控制台等）：

| 类别 | 对象 | 用户界面（认证前） | 用户界面（认证后） | 日志 |
| --- | --- | --- | --- | --- |
| 软件信息 | 产品安装和使用的软件和冷热补丁名称和版本号（含后台软件） | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 软件版本号（如apache、tomcat版本号） | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 操作系统及版本号 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 单板名称 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 内存布局 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 处理器类型 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 二进制文件名 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 设备架构 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 进程名称 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 文件结构 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 服务器物理绝对路径 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 设备文件结构 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 函数调用痕迹（含函数调用栈、函数调用） | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 主机列表 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | SQL语句 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 数据库名/表名 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | 堆栈 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 软件信息 | SAL指令 | 禁止 | 业务必须的信息，允许按最小化原则显示 | 问题定位等业务必须的场景，允许按最小化原则打印 |
| 业务信息 | 会话标识 | 禁止 | 禁止 | 禁止 |
| 业务信息 | 认证凭据(密钥、口令、证书） | 禁止 | 禁止 | 禁止 |
| 业务信息 | 敏感个人数据（如银行账号、身份证号、行踪轨迹、生物信息等） | 禁止 | 禁止 | 禁止 |


**注**：

1. 用户界面主要指人与软件系统进行交互界面，常见的有web页面、APP界面、软件的操作界面、控制台等。
2. 网络安全红线中要求：禁止明文打印“认证凭据（口令/私钥/预共享密钥）、敏感个人信息（如银行账号、身份证号、行踪轨迹、生物信息等）”。

**【例外】**

1. 针对日志中禁止打印的信息中，黑匣子日志、OS/DB原生审计日志可以例外。
2. 针对用户界面中禁止显示的信息中，以下场景可以例外：

    1. 符合业界惯例的场景例外，包括终端类设备通过串口输出，在用户界面上显示的“软件组件”和“系统配置”信息；设备启动过程中，通过串口显示芯片版本等信息。
    2. 对于遵循业界通用实践的标准协议，在交互过程中的报文中包含的软件名称或协议版本例外。
    3. 网络安全红线中，针对打印认证凭据类信息，以下场景可以例外：

        1. 消费者终端类产品可根据业界惯例可选明文显示。
        2. wifi ap接入口令，可根据业界惯例可选明文显示。
        3. SNMP v1/v2的团体字在界面中可以明文显示。
        4. 一次性认证凭据可例外。
        5. 自动生成认证凭据的场景（如云平台AK/SK的生成），仅允许在首次生成时一次性查看/下载认证凭据的明文，一旦页面关闭，后续不可再次明文查询，如果遗忘认证凭据只能通过重新生成方式更新。
        6. 对于云平台第三方开发者登录管理portal，查看曾创建的认证凭据，允许界面查询认证凭据明文（如AWS租户）。
        7. 对于浏览器密码保存功能（即在用户授权后浏览器保存访问第三方的账号口令），如已经过身份验证后（包括口令、指纹等），浏览器可以将明文密码显示给用户。

**【相关软件CWE编号】** CWE-200，CWE-209, CWE-359

# 4 安全实践

## 4.1 Unsafe 函数和 trait

### P.SAF.UNS.01 Unsafe 代码应仅在需要的场景下使用

**【描述】**

- 不要为了逃避编译器安全检查而随便滥用 Unsafe Rust，否则很可能引起未定义行为（UB）。
- 不要为了提升性能而盲目使用 Unsafe Rust。
- 要尽量缩小使用 `unsafe` 块的范围，而不要将多余的代码都包入 `unsafe` 块中。
- 对于 Unsafe 函数，应该显式地标记 `unsafe`，不要试图通过宏等技巧打破 Unsafe 传播链条。
- 不要通过 Unsafe 将不可变引用/指针手工转换为可变引用/指针。这类场景考虑使用内部可变性容器 `Cell<T>` 或 `RefCell<T>`。

**【反例】**

```rust
// 不符合：该函数为滥用 unsafe 来跳过 Rust 借用检查
// 强行返回本地变量的引用，最终引起未定义行为
fn abuse_unsafe_return_local_ref<'a>() -> &'a String {
    let s = "hello".to_string();
    let ptr_s_addr = &s as *const String as usize;
    unsafe { &*(ptr_s_addr as *const String) }
}

fn main() {
    let s = abuse_unsafe_return_local_ref(); // error: Undefined Behavior: encountered a dangling reference (use-after-free)
}
```

**【反例】**

```rust
// 不符合：使用 unsafe 通过不可变借用修改变量
fn main() {
    unsafe fn increase_num(r: &i32) {
        *(r as *const i32 as *mut i32) += 1;
    }

    let num = 0;
    unsafe {
        increase_num(&num);
    }
    println!("{num}");
}
```

### G.SAF.UNS.01 禁止将外部数据作为加载动态库的参数

**【级别】** 要求

**【描述】**

禁止将从外部获取的数据作为加载动态库的参数，否则可能加载攻击者事先预制的模块。

如果要加载动态库，可以采用如下措施之一：

- 使用白名单机制，确保加载函数的参数不受任何外来数据的影响。
- 使用数字签名机制保护要加载的动态库，充分保证其完整性。
- 在设备本地加载的动态库通过权限与访问控制措施保证了本身安全性后，通过特定目录自动被程序加载。
- 在设备本地的配置文件通过权限与访问控制措施保证了本身安全性后，自动加载配置文件中指定的动态库。

**【反例】**

示例参考：[rust_libloading 例子](https://github.com/nagisa/rust_libloading/blob/master/tests/windows.rs)。

```rust
// 不符合
extern crate libloading;
use std::io::Read;

fn main() {
    let mut f = std::fs::File::open("tests/nagisa64.txt").unwrap();
    let mut name = String::new();
    // 不符合：从不受信任的文件读取用于加载的动态库名称
    f.read_to_string(&mut name).unwrap();

    unsafe {
        let lib = libloading::Library::new(&name);
        if lib.is_err() {
            println!("can't open {}", name);
        }
    }
}
```

**【正例】**

```rust
extern crate libloading;
use std::ffi::OsStr;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    fn whitelist_verify<P: AsRef<OsStr>>(lib_path: P) -> Result<bool, String> {
        // 符合：检查传入路径是否在白名单内
        // ...
        return Result::Ok(false);
    }

    let name = "nagisa64.dll";
    if whitelist_verify(name).is_ok() {
        return;
    }
    unsafe {
        let lib = libloading::Library::new(name);
        if lib.is_err() {
            println!("can't open {}", name);
        }
    }
}
```

### G.SAF.UNS.02 定义函数签名时，当输入参数全部为不可变借用时，输出不宜包含可变借用

**【级别】** 建议

**【描述】**

将某个包含 Unsafe 代码的函数安全抽象为 Safe 函数的时候，要注意符合规则中描述的签名约定：当输入参数全部为不可变借用时，输出不宜包含可变借用，这是违反 Rust 安全准则的。

对于需要内部可变性的场景可以使用 Safe Rust 提供的 `Cell/RefCell`。

**【反例】**

来自 Rust 官方的一个[示例](https://github.com/rust-lang/rust/issues/39465)，该函数签名导致 Rust 出现了一个严重 bug：

```rust
// 不符合：函数签名违反了本条规则
pub fn as_mut_slice(&self) -> &mut [T] {
    unsafe {
        slice::from_raw_parts_mut(self.ptr as *mut T, self.len())
    }
}    
```

**【正例】**

```rust
// 符合：
pub fn as_mut_slice(&mut self) -> &mut [T] {
    unsafe {
        slice::from_raw_parts_mut(self.ptr as *mut T, self.len())
    }
} 
```

## 4.2 FFI

### P.SAF.FFI.01 在 FFI 边界上传递数据应注意内存安全管理

**【描述】**

在 FFI 边界上传递数据要遵循 “内存由创建方来负责释放” 的基本原则来保证内存的安全管理。

否则可能会遇到以下问题：

- 所有权问题：Rust 使用所有权系统管理内存，而 C 函数通常不了解 Rust 的所有权规则。如果将 Rust 字符串传递给 C 函数，需要确保内存管理的正确性，防止出现悬垂指针或者内存泄漏等问题。可以使用合适的 Rust-C 绑定库或者 FFI（Foreign Function Interface）来处理内存管理问题。

- 生命周期问题：Rust 字符串的生命周期通常是由 Rust 的借用规则确定的。如果需要将字符串传递给 C 函数，并且 C 函数需要长时间持有字符串的引用，需要谨慎处理生命周期的问题，以避免引用无效或悬垂引用的情况。

### P.SAF.FFI.02 应正确处理 FFI 调用的返回值和输出参数

**【描述】**

在 FFI 调用场景下，应该对函数调用结果的错误异常进行正确处理。错误异常的常见形式有错误码返回值和空指针。

**【反例】**

```rust
// 如下函数定义在 C 语言侧，它会动态分配一块堆内存，并返回一个指针
// Edition2024需添加 unsafe 标注
extern "C" {
    fn alloc_huge_space() -> *mut libc::c_int;
}

fn foo() -> *mut libc::c_int {
    let x = unsafe { alloc_huge_space() };
    // 不符合：返回的指针 `x` 可能为空，直接使用空指针将导致程序异常
    let v = unsafe { std::slice::from_raw_parts_mut(x, 100) };
    v[0] = 100;
    x
}
```

**【正例】**

```rust
// 如下函数定义在 C 语言侧，它会动态分配一块堆内存，并返回一个指针
// Edition2024需添加 unsafe 标注
extern "C" {
    fn alloc_huge_space() -> *mut libc::c_int;
}

fn foo() -> *mut libc::c_int {
    let x = unsafe { alloc_huge_space() };
    // 符合：指针 `x` 为空时，则不会使用空指针
    if !x.is_null() {
        let v = unsafe { std::slice::from_raw_parts_mut(x, 100) };
        v[0] = 100;
    }
    x
}
```

### P.SAF.FFI.03 应优先选用 RAII 方式管理外部资源

**【描述】**

FFI 编程中关于资源管理，遵循着 “谁申请谁释放” 的原则。因此在 Rust 中调用 FFI 函数创建的资源，也应该调用相应的 FFI 函数来释放资源。常见的资源类型包括：堆内存、文件、硬件接口等。

使用 RAII 方式管理外部资源，可以有效避免忘记释放或重复释放问题。

**【说明】**

RAII 是指 resource acquisition is initialization，通过对象的构造函数获取资源，并在对象的析构函数释放资源。

**【正例】**

```rust
// Edition2024需添加 unsafe 标注
extern "C" {
    fn new_resource() -> *mut Resource;
    fn process_resource(resource: *mut Resource);
    fn free_resource(resource: *mut Resource);
}

#[repr(C)]
struct CResource(*mut Resource);

impl CResource {
    fn new() -> Self {
        unsafe { Self(new_resource()) }
    }
    fn process(&self) {
        unsafe { process_resource(self.0) }
    }
}

impl Drop for CResource {
    fn drop(&mut self) {
        unsafe { free_resource(self.0) }
    }
}

fn main() {
    let mut res = CResource::new();
    res.process();
}
```

### G.SAF.FFI.01 FFI 边界应确保字符串参数正确传递和使用

**【级别】** 要求

**【描述】**

Rust 中字符串的表示采取了与 C 语言不同的方式。Rust 字符串指针为宽指针，其中包含了字符串的起始地址指针和字符串长度；而 C 语言中字符串指针为窄指针，仅包含起始地址，且字符串必须以 `\0` 结尾。因此，不能直接使用 Rust 的 `String` 和 `&str` 类型与 FFI C 函数进行交互。

Rust标准库提供了两种与 C 语言字符串兼容的字符串类型：`CString` 和 `CStr`。从 Rust 向 C 函数传递字符串时应当向将字符串转换为 `CString` 类型，再用 `.as_ptr()` 方法获取 C 字符串指针。而在 Rust 中读取 C 函数返回的字符串指针，应该通过 `CStr::from_ptr()` 函数将其转换为 `CStr` 类型再读取。

`CString` 和 `CStr` 类型也提供了与 `String` 和 `&str` 类型之间的相互转换函数。

**【正例】**

```rust
use std::ffi::CString;
use std::os::raw::c_char;

// Edition2024需添加 unsafe 标注
extern "C" { fn greet(name: *const c_char); }

fn main() {
    let name = "Rust";
    let name = CString::new(name).unwrap();
    unsafe { greet(name.as_ptr()) };
}
```

### G.SAF.FFI.02 在 FFI 调用的场景下，应确保跨边界数据的内存布局兼容

**【级别】** 要求

**【描述】**

FFI 函数传递的任何数据类型，需要保证内存布局一致。对于结构体、枚举和联合体，应该通过添加 `#[repr(C)]` 属性，来避免字段顺序重排，以保证内存布局的兼容。

在处理网络消息收发场景中，常见 1 字节对齐内存布局方式。在 Rust 中可以使用 `#[repr(packed)]` 表示对应的数据。

**【正例】**

```rust
#[repr(C)]
struct Foo {
    a: libc::c_short,
    b: libc::c_int,
    c: libc::c_char,
    d: libc::c_long,
}

// Edition2024需添加 unsafe 标注
#[link(name = "bar")]
extern "C" {
    fn bar(foo: *const Foo);
}

fn main() {
    let foo = Foo {
        a: 1234,
        b: 12345,
        c: 123,
        d: 123456,
    };
    unsafe {
        bar(&foo as *const Foo);
    }
}
```
```c
// C侧代码
#pragma pack(1)
typedef struct Foo {
    char a;
    int b;
    long long c;
} Foo;
#pragma pack()

struct Foo new_foo() {
    struct Foo foo = {'c', 1234, 123456789};
    return foo;
}
```

**【正例】**

```rust
#[repr(packed)]
#[derive(Debug)]
struct Foo {
    a: libc::c_char,
    b: libc::c_int,
    c: libc::c_longlong,
}

// Edition2024需添加 unsafe 标注
extern "C" {
    fn new_foo() -> Foo;
}

let foo = unsafe { new_foo() };
println!("{foo:?}");
```

```c
// C侧代码
#pragma pack(1)
typedef struct Foo {
    char a;
    int b;
    long long c;
} Foo;
#pragma pack()

struct Foo new_foo() {
    struct Foo foo = {'c', 1234, 123456789};
    return foo;
}
```

### G.SAF.FFI.03 禁止调用 C 不可重入函数

**【级别】** 要求

**【描述】**

在多线程条件下调用外部不可重入函数时，有可能会因竞争条件而导致意外的系统状态和不可预测的结果，或导致拒绝服务和任意代码执行等内存安全问题。

C 语言标准库中常见的不可重入函数包括：
`getenv()`, `strtok()`, `strerror()`, `asctime()`, `ctime()`, `localtime()`, `gmtime()`, `setlocale()`, `localeconv()`, `syslog()`, `getlogin()` 等。

开发者能在 Unsafe Rust 下直接使用 `extern "C"` 或 libc 库调用这些函数。

一般情况下，开发者可将这些函数替换为其可重入版本，否则需要根据情况解决或预防因竞争而产生的问题。

详情可参考 C 语言规范的相关条目 *G.FUU.20 使用库函数时避免竞争条件*。

### G.SAF.FFI.04 禁止使用外部内存不安全函数

**【级别】** 要求

**【描述】**

C 语言标准函数库中，存在一些不安全函数（见下）。使用不当容易造成缓冲区溢出等安全漏洞。Rust FFI 编程中禁止调用外部 C 不安全函数。

以下列出了部分内存操作类不安全函数：

- 内存拷贝函数：`memcpy`, `wmemcpy`, `memmove`, `wmemmove`。
- 内存初始化函数：`memset`。
- 字符串拷贝函数：`strcpy`, `wcscpy`, `strncpy`, `wcsncpy`。
- 字符串拼接函数：`strcat`, `wcscat`, `strncat`, `wcsncat`。
- 字符串格式化输出函数：`sprintf`, `swprintf`, `vsprintf`, `vswprintf`, `snprintf`, `vsnprintf`。
- 字符串格式化输入函数：`scanf`, `wscanf`, `vscanf`, `vwscanf`, `fscanf`, `fwscanf`, `vfscanf`, `vfwscanf`, `sscanf`, `swscanf`, `vsscanf`, `vswscanf`。
- stdin流输入函数：`gets`。

开发者能在 Unsafe Rust 下直接使用 `extern "C"` 或 libc 库调用这些函数。

详情可参考 C 语言规范的相关条目 *G.FUU.21 禁止使用内存操作类不安全函数*。

对于上面这些不安全函数，在 Rust 中，一般有功能相同的安全函数可供使用。比如：

- 对于内存拷贝和初始化，可以使用 `std::mem` 模块提供的函数进行处理。
- 对于字符串拼接和格式化输出，可以使用标准库提供的 `format!` 或 `println!` 等宏函数。
- 对于标准输入流读取，可以使用 `std::io::stdin()` 对象的相关方法来处理。

### G.SAF.FFI.05 `extern` 外部函数应显式指定 ABI 标识

**【级别】** 要求

**【描述】**

当使用 `extern` 指定外部函数时，应显式指定 [`ABI` 标识](https://doc.rust-lang.org/reference/items/external-blocks.html#abi)，否则默认为 `C-ABI`。

显式指定 ABI 标识是 Rust 语言的一种约定俗成，有利于代码健壮性。

**【反例】**

```rust
use std::os::raw::c_char;
// 不符合：不要省略 C-ABI 指定
// Edition2024需添加 unsafe 标注
extern {
    fn strlen(s: *const c_char) -> i32;
}
```

**【正例】**

```rust
use std::os::raw::c_char;
// 符合
// Edition2024需添加 unsafe 标注
extern "C" {
    fn strlen(s: *const c_char) -> i32;
}
```

## 4.3 并发并行

### P.SAF.MTH.01 通过原子类型使用无锁编程时，应确保原子操作内存序正确

**【描述】**

在 Rust 多线程开发中，通过原子类型使用无锁编程时，应正确使用内存顺序避免数据竞争。

**【正例】**

- 无锁编程示例:

```rust
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

fn main() {
    let lock = Arc::new(AtomicBool::new(false)); // 这个原子类型的值用来表示 "是否获取到锁"
    let data = Arc::new(AtomicUsize::new(0));

    let rlock = lock.clone();
    let rdata = data.clone();
    let rd_thr = thread::spawn(move || {
        // 读线程等待 lock 变为 true 之后才读取 data 的数据
        // Acquire 内存序确保内存读取 data 值的指令一定在 compare_exchange_weak 返回成功之后才执行
        // 和写线程的 Release 内存序配合可以确保读线程一定获取到最新的 data 值
        // data 读写的内存序不影响功能正确性，使用对性能最优的 Relaxed 内存序即可
        // compare_exchange_weak 失败后不会读取其他任何内存数据，
        // 因此可以将最后一个参数，失败后的内存序设置为对性能最优的 Relaxed
        while let Err(_) =
            rlock.compare_exchange_weak(true, false, Ordering::Acquire, Ordering::Relaxed)
        {}
        let num = rdata.load(Ordering::Relaxed);
        // 一定会输出最新的数据 1，如果读写线程中针对 lock 操作的内存序没有正确实现 Acquire / Release，则可能输出 0
        println!("num = {}", num);
    });

    let wlock = lock.clone();
    let wdata = data.clone();
    let wr_thr = thread::spawn(move || {
        // 写线程写完数据之后再将 lock 变为 true，通知读线程读取数据
        // Release 内存序确保 `1` 写入 data 的指令一定在 `true` 写入 lock 之前已经完成
        // 和读线程的 Acquire 内存序配合可以确保读线程一定获取到最新的 data 值
        // data 读写的内存序不影响功能正确性，使用对性能最优的 Relaxed 内存序即可
        wdata.store(1, Ordering::Relaxed);
        wlock.store(true, Ordering::Release);
    });

    let _ = rd_thr.join();
    let _ = wr_thr.join();
}
```

**【反例】**

- 多线程通过 unsafe 修改静态变量

```rust
// 不符合：存在数据竞争
static mut SHARED_STATE: u8 = 0;

thread::spawn(move || unsafe { SHARED_STATE = 1 };);
thread::spawn(move || unsafe { SHARED_STATE = 2 };);
```

**【正例】**

- 多线程通过 unsafe 修改静态变量

```rust
// 符合
static SHARED_STATE: AtomicU8 = AtomicU8::new(0);

thread::spawn(move || SHARED_STATE.store(1, Ordering::SeqCst));
thread::spawn(move || SHARED_STATE.store(2, Ordering::SeqCst));
```

### P.SAF.MTH.02 为自定义类型实现 `Sync` 或 `Send` trait 时，应确保无数据竞争风险

**【描述】**

通过 Unsafe Rust 手工为自定义类型实现 `Sync` 或 `Send` trait 时，自定义类型必须满足以下约束，且需开发者自行判断，如果在不符合条件的情况下实现了 `Sync` 和 `Send`，则会造成数据竞争风险：

- Send：表明自定义类型可以在线程间安全的传递其所有权。
- Sync：表明自定义类型可以在线程间通过引用安全的共享。

**【反例】**

- 在 Unsafe Rust 中手动为自定义类型实现 `Sync` 的反例：

```rust
fn main() {
    use std::cell::Cell;
    use std::marker::Sync;
    use std::sync::Arc;

    struct Counter {
        val: Cell<usize>,
    }

    // 不符合：Counter 在多线程共享不是安全的
    // 错误的使用 unsafe impl Sync
    unsafe impl Sync for Counter {}

    impl Counter {
        fn new() -> Counter {
            Counter { val: Cell::new(0) }
        }

        fn increment(&self) {
            self.val.set(self.val.get() + 1);
        }

        fn get_count(&self) -> usize {
            self.val.get()
        }
    }

    let counter = Arc::new(Counter::new());
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = std::thread::spawn(move || {
            for _ in 0..100 {
                counter.increment();
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Counter value: {}", counter.get_count());
}
```

**【正例】**

- 在 Unsafe Rust 中手动为自定义类型实现 `Sync` 的正例：

```rust
fn main() {
    use std::marker::Sync;
    use std::sync::{Arc, Mutex};

    struct Counter {
        count: Mutex<usize>,
    }

    // 符合：Counter 在多线程共享是安全的
    unsafe impl Sync for Counter {}

    impl Counter {
        fn new() -> Counter {
            Counter {
                count: Mutex::new(0),
            }
        }

        fn increment(&self) {
            let mut count = self.count.lock().unwrap();
            *count += 1;
        }

        fn get_count(&self) -> usize {
            *self.count.lock().unwrap()
        }
    }

    let counter = Arc::new(Counter::new());
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = std::thread::spawn(move || {
            for _ in 0..100 {
                counter.increment();
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Counter value: {}", counter.get_count());
}
```

### G.SAF.ASY.01 避免在异步处理过程中包含阻塞操作

**【级别】** 建议

**【描述】**

避免在异步编程中使用阻塞操作。

**【反例】**

不要在异步流程中使用阻塞操作函数：

```rust
async fn read_file() {
    std::thread::sleep(std::time::Duration::from_secs(5)); // 不符合
}
```

**【正例】**

使用异步运行时，如 tokio 提供的非阻塞函数：

```rust
async fn read_file() {
    tokio::time::sleep(std::time::Duration::from_secs(5)).await; // 符合
    Ok(())
}
```

### G.SAF.MTH.01 多线程场景下，对于共享的标量类型数据，宜使用对应的原子类型

**【级别】** 建议

**【描述】**

在多线程场景下，对于需要共享的类型数据，如布尔、整型和指针类型，建议使用原子类型，而非使用互斥锁进行封装。使用原子类型性能更好。

**【反例】**

```rust
// 不符合
let x = Mutex::new(false);
```

**【正例】**

```rust
// 符合
let x = AtomicBool::new(false);
```

## 4.4 内存与指针

### G.SAF.MEM.01 应校验内存申请函数的输入参数和返回值

**【级别】** 要求

**【描述】**

涉及内存分配的函数调用，应注意：

- **申请前应校验申请大小**

    当申请内存大小由程序外部输入时，内存申请前，要求对申请内存大小进行合法性校验，防止申请 0 长度内存，或过多地、非法地申请内存。

- **申请后应校验是否成功**

    当申请内存的数值过大（可能一次就申请了非常大的超预期的内存；也可能循环中多次申请内存），可能会造成内存申请失败，返回空指针。

**【反例】**

申请前应校验申请大小：

```rust
// CWE-789
fn get_untrusted_size() -> usize {
    // 返回外部函数确定的大小
    unsafe { other_lib_get_size() }
}

fn main() {
    let size = get_untrusted_size();
    // 不符合：内存分配 size 由外部传入，没有检查其值是否过大
    let buffer: Vec<u8> = Vec::with_capacity(size);
    // 使用 buffer 接收外部数据
    // ...
}
```

**【正例】**

申请前应校验申请大小

```rust
fn get_untrusted_size() -> usize {
    // 返回外部函数确定的大小
    unsafe { other_lib_get_size() }
}

fn main() {
    const BUF_MAX_SIZE: usize = 2_usize.pow(8);
    let size = BUF_MAX_SIZE.min(get_untrusted_size());
    // 符合：给外部传入的内存分配 size 值设定了一个上限
    let buffer: Vec<u8> = Vec::with_capacity(size);
    // 使用 buffer 接收外部数据
    // ...
}
```

**【反例】**

申请后应校验是否成功

```rust
fn func() {
    let malloc_size = || usize::MAX;
    // 不符合：未校验内存分配函数的参数
    let ptr = unsafe { libc::malloc(malloc_size()) };
    // 使用 ptr 进行内存操作
    // ...
    unsafe { libc::free(ptr) };
}
```

**【正例】**

申请后应校验是否成功

```rust
fn func() {
    let malloc_size = || usize::MAX;
    let ptr = unsafe { libc::malloc(malloc_size()) };
    if !ptr.is_null() {
        // 使用 ptr 进行内存操作
        // ...
        unsafe { libc::free(ptr) };
    }
}
```

### G.SAF.MEM.02 Unsafe 模式下，使用指针及内存地址时应确保有效性

**【级别】** 要求

**【描述】**

在 Unsafe Rust 中，通过裸指针方式申请分配内存应注意：

- **指针解引用前应确保指向的内存已初始化**
 
    访问未初始化内存会导致未定义行为。

- **FFI函数调用返回的指针应先检查是否为空再使用**
 
    解引用空指针会导致程序崩溃。

- **分配在栈上的局部变量和函数参数的地址都不应返回到函数作用域之外**
 
    栈内存会在函数返回后被回收，访问会导致未定义行为。

- **指针指向的内存释放后禁止继续访问**

    指针指向的内存释放后，继续通过指针访问会导致未定义行为。

**【反例】**

禁止使用未初始化的指针：

```rust
#[derive(Debug)]
struct Foo(i32);

fn main() {
    // 模拟一个未初始化的指针
    let foo_ptr: *mut Foo = std::ptr::null_mut();
    // 不符合：禁止使用未初始化的指针
    unsafe { println!("{:?}", (*foo_ptr).0); }
}
```

**【正例】**

禁止使用未初始化的指针：

```rust
#[derive(Debug)]
struct Foo(i32);

fn main() {
    // 模拟一个已正确初始化的指针
    let foo_ptr: *mut Foo = Box::into_raw(Box::new(Foo(1)));
    if foo_ptr.is_null() {
        return;
    }

    // 符合：使用已初始化的指针
    unsafe {
        println!("{:?}", (*foo_ptr).0);
    }

    // 模拟释放内存操作
    unsafe {
        let _: Box<Foo> = Box::from_raw(foo_ptr);
    }
}
```

**【反例】**

分配在栈上的局部变量的地址不应返回到函数作用域之外：

```rust
fn main() {
    let p = return_stack_address();
    unsafe { println!("{}", *p); }
}

fn return_stack_address() -> *const i32 {
    let value = 123_i32;
    // 不符合：禁止将局部变量的地址返回到作用域之外
    &value as *const i32
}
```

**【反例】**

禁止释放指针后继续使用：

```rust
const BUF_SIZE: usize = 100;

unsafe {
    let buf = malloc(BUF_SIZE) as *mut libc::c_char;

    // 操作指针, 写入数据
    // ...

    free(buf as *mut libc::c_void);

    // 不符合：free 内存后数据还在，`buf` 变成悬挂指针且不为空。
    // 因此仍然会解引用指针
    if !buf.is_null() {
        println!("{:?}", *buf);
    }
}
```

**【正例】**

```rust
const BUF_SIZE: usize = 100;

unsafe {
    let mut buf = malloc(BUF_SIZE) as *mut libc::c_char;

    // 操作指针, 写入数据
    // ...

    // 符合：释放内存后将指针设置为 null
    free(buf as *mut c_void);
    buf = std::ptr::null_mut();

    // 符合：`ptr` 为空，判断式不成立所以不会解引用。
    if !buf.is_null() {
        println!("{:?}", *buf);
    }
}
```

### G.SAF.MEM.03 Unsafe 模式下，应正确释放申请的内存

**【级别】** 要求

**【描述】**

当动态分配内存不再使用时应予以释放，否则会发生内存泄漏。如果攻击者可以有意触发该漏洞，则内存资源可能被耗尽，造成拒绝服务。

优先推荐使用 RAII 模式进行内存释放，避免内存泄漏和重复释放的风险。

内存释放后，对应的指针变成悬空指针，建议重置为空指针，一旦错误访问，可以立即得到反馈，避免悬空指针的未定义行为（内存可能被其他业务模块重新分配，悬空指针的使用可能无意间修改了其他业务模块的数据）。

**【反例】**

双重释放：

```rust
const BUF_SIZE: usize = 100;

unsafe {
    let buf = malloc(BUF_SIZE) as *mut libc::c_char;

    // 操作指针, 写入数据
    // ...

    // 不符合：释放内存，但是指针没有设置为空
    free(buf as *mut libc::c_void);

    // ...
    
    // 不符合：free 内存后，指针不是空，会导致双重释放错误
    free(buf as *mut libc::c_void);
}
```

**【正例】**

双重释放：

```rust
const BUF_SIZE: usize = 100;

unsafe {
    let mut buf = malloc(BUF_SIZE) as *mut libc::c_char;

    // 操作指针, 写入数据
    // ...

    // 符合：释放内存后将指针设置为 null
    if !buf.is_null() {
        free(buf as *mut c_void);
        buf = std::ptr::null_mut();
    }

    // ...
    
    // 符合：`ptr` 为空，不会造成双重释放错误
    if !buf.is_null() {
        free(buf as *mut c_void);
        buf = std::ptr::null_mut();
    }
}
```

**【反例】**

忘记释放：

```rust
const BUF_SIZE: usize = 100;

unsafe {
    let buf = malloc(BUF_SIZE) as *mut libc::c_char;

    // 操作指针, 写入数据
    // ...
   
    // 不符合：忘记释放内存
}
```

### G.SAF.MEM.04 内存中的敏感信息使用完毕后应立即清零

**【级别】** 要求

**【描述】**

内存中的口令、密钥等敏感信息使用完毕后应立即清零，避免被攻击者获取。

为防止内存清零操作被编译优化，推荐使用 [std::ptr::write_volatile](https://doc.rust-lang.org/std/ptr/fn.write_volatile.html) 函数。

**【正例】**

```rust
struct Buffer {
    password: [u8; 16],
}

impl Buffer {
    fn new() -> Self {
        Self { password: [1; 16] } // 初始化缓冲区
    }
}

impl Drop for Buffer {
    fn drop(&mut self) {
        unsafe {
            // 符合：调用 write_volatile 清零密钥
            std::ptr::write_volatile(
                &mut self.password.as_slice(),
                vec![0; self.password.len()].as_slice(),
            );
        }
    }
}

fn main() {
    let _buffer = Buffer::new(); // 创建缓冲区实例

    // ...
    // 当 buffer 离开作用域时，会自动调用其 drop 函数清空内存
}
```

# 5 附录

## 附录A Rustfmt 配置与模板

公司内开发者可参考以下 Rustfmt 模板。

模板内容可以放到 `rustfmt.toml` 或 `.rustfmt.toml` 文件中。使用 `cargo fmt` 执行。

很多选项可直接使用默认值，因此无需配置。以下配置针对使用非默认值的情况。

**【只包含 Stable 的选项】**

```toml
# 使用 rustfmt 2.0 时需指定
version = "Two"

# 统一管理宽度设置，但不包含 comment_width
use_small_heuristics="MAX"
# 在 match 分支中，如果包含了块，也需加逗号以示分隔
match_block_trailing_comma=true
# 如果项目只在 Unix 平台下跑，可以设置该项为 Unix，表示换行符只依赖 Unix
newline_style="Unix" 
# 不将多个 Derive 宏合并为同一行
merge_derives = false
# 设置行长度
max_width = 120

# 指定 fmt 忽略的目录
ignore = [
     "src/test",
     "test",
     "docs",
]
```

## 附录B Clippy 配置与模板

Clippy 当中存在部分 lint 可由用户按需配置，如果在执行 `cargo clippy` 时不想依靠默认值，可以在源码目录下创建 `clippy.toml` 文件来进行设置。

```toml
# for `disallowed_method`:
# https://rust-lang.github.io/rust-clippy/master/index.html#disallowed_method
disallowed-methods = []

# 函数参数最长不要超过5个
too-many-arguments-threshold=5

# G.FUD.01：公开 API 也检查拷贝代价大的按值传参（large_types_passed_by_value 等）
avoid-breaking-exported-api = false

# G.ERR.01：单元测试中允许 unwrap，生产代码仍由 unwrap_used 约束
allow-unwrap-in-tests = true

# G.MAC.01：私有 macro_rules! 也检查元变量是否被展开在 unsafe 块内
warn-unsafe-macro-metavars-in-private-macros = true
```

**Lint 级别配置示例** 

Rust 支持配置 lint 的检测级别，一般涉及以下几种设置：

- `allow`: 用于允许检测项，即跳过规则检查。
- `warn`: 用于告警所触及的检查规则，最终结果以 `warning` 形式呈现。
- `deny`: 与 `warn` 相似，但更为严格，并且最终结果由 `error` (错误) 表示且执行命令会返回错误码。
- `forbid`: 严格禁止触犯某条检查规则，不允许在其它任何地方改变相应 lint 的级别, 结果上与 `deny` 相同，都以 `error` 形式呈现。

当用户希望针对某些代码段进行屏蔽，或针对全局屏蔽代码检查可以使用以下方法：

**方法1: 模块内配置**

**生效范围**: 模块

```rust
// 参考： https://github.com/serde-rs/serde/blob/master/serde/src/lib.rs
#![allow(unknown_lints, bare_trait_objects, deprecated)]
// Ignored clippy and clippy_pedantic lints
#![allow(
    // clippy bug: https://github.com/rust-lang/rust-clippy/issues/5704
    clippy::unnested_or_patterns,
    // clippy bug: https://github.com/rust-lang/rust-clippy/issues/7768
    clippy::semicolon_if_nothing_returned,
    // not available in our oldest supported compiler
    clippy::empty_enum,
    clippy::type_repetition_in_bounds, // https://github.com/rust-lang/rust-clippy/issues/8772
    // integer and float ser/de requires these sorts of casts
    clippy::cast_possible_truncation,
    clippy::cast_possible_wrap,
    clippy::cast_sign_loss,
    // things are often more readable this way
    clippy::cast_lossless,
    clippy::module_name_repetitions,
    clippy::single_match_else,
    clippy::type_complexity,
    clippy::use_self,
    clippy::zero_prefixed_literal,
    // correctly used
    clippy::derive_partial_eq_without_eq,
    clippy::enum_glob_use,
    clippy::explicit_auto_deref,
    clippy::let_underscore_untyped,
    clippy::map_err_ignore,
    clippy::new_without_default,
    clippy::result_unit_err,
    clippy::wildcard_imports,
    // not practical
    clippy::needless_pass_by_value,
    clippy::similar_names,
    clippy::too_many_lines,
    // preference
    clippy::doc_markdown,
    clippy::unseparated_literal_suffix,
    // false positive
    clippy::needless_doctest_main,
    // noisy
    clippy::missing_errors_doc,
    clippy::must_use_candidate,
)]
// Restrictions
#![deny(clippy::question_mark_used)]
// Rustc lints.
#![deny(missing_docs, unused_imports)]
```

**方法2: 代码上方配置**

**生效范围**: 代码段/块

```rust
#[allow(clippy::default_numeric_fallback)]
let x = 0;
```

**方法3: 编译选项配置**

**生效范围**: crate/workspace/项目/环境

生效范围最广的一种配置方式。原理是通过创建 cargo 的 config.toml 文件来配置 rust 编译选项，进而配置 lint 级别。(生效范围取决于 .cargo/config.toml 文件的路径)

配置文件的放置路径参考 [Cargo 相关文档](https://doc.rust-lang.org/cargo/reference/config.html#hierarchical-structure)

若路径为源码目录下的 `.cargo/config.toml`，则配置对整个项目生效。
若路径为环境下的 cargo 安装目录，如 `~/.cargo/config.toml`，则配置对整个环境生效（除非被项目配置文件覆盖）。

目前针对编程规范的配置模板如下：

```toml
[target.'cfg(all())']
rustflags = [
   # rustc lints
   "-Wmissing_debug_implementations",
   "-Wnon_camel_case_types",
   "-Wnon_snake_case",
   "-Wnon_upper_case_globals",
   "-Wunused_must_use",
   # 规范评审条款新增
   "-Wunconditional_recursion",
   "-Wunused_comparisons",
   "-Wambiguous_negative_literals",
   # clippy lints
   "-Wclippy::approx_constant",
   "-Wclippy::arithmetic_side_effects",
   "-Wclippy::bad_bit_mask",
   "-Wclippy::bool_assert_comparison",
   "-Wclippy::bool_comparison",
   "-Wclippy::borrow_interior_mutable_const",
   "-Wclippy::blocks_in_conditions",
   "-Wclippy::declare_interior_mutable_const",
   "-Wclippy::default_numeric_fallback",
   "-Wclippy::derived_hash_with_manual_eq",
   "-Wclippy::derive_ord_xor_partial_ord",
   "-Wclippy::from_over_into",
   "-Wclippy::large_types_passed_by_value",
   "-Wclippy::mut_from_ref",
   "-Wclippy::mutex_atomic",
   "-Wclippy::mutex_integer",
   "-Wclippy::missing_errors_doc",
   "-Wclippy::missing_panics_doc",
   "-Wclippy::missing_safety_doc",
   "-Wclippy::negative_feature_names",
   "-Wclippy::needless_range_loop",
   "-Wclippy::precedence",
   "-Wclippy::recursive_format_impl",
   "-Wclippy::redundant_allocation",
   "-Wclippy::redundant_feature_names",
   "-Wclippy::undocumented_unsafe_blocks",
   "-Wclippy::unwrap_used",
   "-Wclippy::wildcard_imports",
   "-Wclippy::wrong_self_convention",
   # 规范评审条款新增
   "-Wclippy::unnecessary_unwrap",
   "-Wclippy::infinite_loop",
   "-Wclippy::while_immutable_condition",
   "-Wclippy::overly_complex_bool_expr",
   "-Wclippy::impossible_comparisons",
   "-Wclippy::absurd_extreme_comparisons",
   "-Wclippy::eq_op",
   "-Wclippy::precedence_bits",
   "-Wclippy::needless_pass_by_value",
   "-Wclippy::non_canonical_partial_ord_impl",
   "-Wclippy::enum_glob_use",
   "-Wclippy::macro_metavars_in_unsafe",
   "-Wclippy::crate_in_macro_def",
]
```

**方法4: (rust 1.74.0+) 通过 Cargo.toml 配置**

**生效范围**: crate

Cargo 1.74.0 新增 lint 级别配置功能，可在项目的 Cargo.toml 文件中配置 rustc/clippy 的 lint 级别。

> 注：[workspace](https://doc.rust-lang.org/cargo/reference/workspaces.html#virtual-workspace) 的配置方式与普通 crate 的配置方式略有不同。

- 普通 crate 中，使用 `[lints.rust]` 及 `[lints.clippy]` 配置即可。
- 在 workspace 中，需要使用 `[workspace.lints.rust]` 及 `[workspace.lints.clippy]` 配置，并且子成员需要额外使用：
    ```toml
    [lints]
    workspace = true
    ```
    才能使其在当前成员中生效，详情参考 [lints table 介绍](https://doc.rust-lang.org/cargo/reference/workspaces.html#the-lints-table)。

目前针对编程规范的配置模板示例如下：

**配置示例 (crate)**

```toml
[package]
# ...

[lints.rust]
missing_debug_implementations = "warn"
non_camel_case_types = "warn"
non_snake_case = "warn"
non_upper_case_globals = "warn"
unused_must_use = "warn"
# 规范评审条款新增
unconditional_recursion = "warn"
unused_comparisons = "warn"
ambiguous_negative_literals = "warn"

[lints.clippy]
approx_constant = "warn"
arithmetic_side_effects = "warn"
bad_bit_mask = "warn"
bool_assert_comparison = "warn"
bool_comparison = "warn"
borrow_interior_mutable_const = "warn"
blocks_in_conditions = "warn"
declare_interior_mutable_const = "warn"
default_numeric_fallback = "warn"
derived_hash_with_manual_eq = "warn"
derive_ord_xor_partial_ord = "warn"
from_over_into = "warn"
large_types_passed_by_value = "warn"
mut_from_ref = "warn"
mutex_atomic = "warn"
mutex_integer = "warn"
missing_errors_doc = "warn"
missing_panics_doc = "warn"
missing_safety_doc = "warn"
negative_feature_names = "warn"
needless_range_loop = "warn"
precedence = "warn"
recursive_format_impl = "warn"
redundant_allocation = "warn"
redundant_feature_names = "warn"
undocumented_unsafe_blocks = "warn"
unwrap_used = "warn"
wildcard_imports = "warn"
wrong_self_convention = "warn"
# 规范评审条款新增
unnecessary_unwrap = "warn"
infinite_loop = "warn"
while_immutable_condition = "warn"
overly_complex_bool_expr = "warn"
impossible_comparisons = "warn"
absurd_extreme_comparisons = "warn"
eq_op = "warn"
precedence_bits = "warn"
needless_pass_by_value = "warn"
non_canonical_partial_ord_impl = "warn"
enum_glob_use = "warn"
macro_metavars_in_unsafe = "warn"
crate_in_macro_def = "warn"
```

**配置示例 (workspace)**

在 workspace 的 Cargo.toml 中：

```toml
# project/Cargo.toml
[workspace]
members = [
    "foo",
    # ...
]

[workspace.lints.rust]
missing_debug_implementations = "warn"
# ...

[workspace.lints.clippy]
approx_constant = "warn"
# ...
```

在 workspace 子成员 `foo` 的 Cargo.toml 中：

```toml
# project/foo/Cargo.toml
[package]
name = "foo"
# ...

[lints]
workspace = true
```

##  参考资料

1. [官方｜Rust API 编写指南](https://rust-lang.github.io/api-guidelines/about.html)
2. [官方 | Rust Style Guide](https://github.com/rust-dev-tools/fmt-rfcs/blob/master/guide/guide.md)
3. [Rust's Unsafe Code Guidelines Reference](https://rust-lang.github.io/unsafe-code-guidelines/)
4. [法国国家信息安全局 | Rust 安全（Security）规范](https://anssi-fr.github.io/rust-guide)
5. [Facebook Diem 项目 Rust 编码规范](https://developers.diem.com/docs/core/coding-guidelines/)
6. [Apache Teaclave 安全计算平台 | Rust 开发规范](https://teaclave.apache.org/docs/rust-guildeline/)
7. [PingCAP | 编码风格指南（包括 Rust 和 Go 等）](https://github.com/pingcap/style-guide)
8. [Google Fuchsia 操作系统 Rust 开发指南](https://fuchsia.dev/fuchsia-src/development/languages/rust)
9. [RustAnalyzer 编码风格指南](https://github.com/rust-analyzer/rust-analyzer/blob/master/docs/dev/style.md)
10. [使用 Rust 设计优雅的 API](https://deterministic.space/elegant-apis-in-rust.html)
11. [Rust FFI 指南](https://michael-f-bryan.github.io/rust-ffi-guide/)
12. [大约 478 条 Clippy lint](https://rust-lang.github.io/rust-clippy/master/index.html)
13. [lints in the rustc book](https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html)
14. [Dtolnay 对 crates.io 中 clippy lint 应用统计](https://github.com/dtolnay/noisy-clippy)
15. [华为C语言编程规范](https://w3.huawei.com/tsl/#/standard/standardDetail?standardId=152657)

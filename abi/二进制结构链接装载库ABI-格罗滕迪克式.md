# 二进制的结构、链接、装载、库与 ABI
## 从指称语义到操作语义的完整映射

---

## 前言：这篇文章在做什么

本文不从"编译器做什么"或"有哪些坑"开始。

它从一个问题开始：**一个程序究竟是什么？**

不是"程序做什么"（功能），不是"程序由什么组成"（结构的枚举），而是：在所有的具体形式（源代码、目标文件、共享库、运行中的进程）之下，程序是什么数学对象？这些具体形式之间的关系是什么？

这个问题的答案构成本文的地基。所有的机制——符号、重定位、段、动态链接、ABI、运行时库——都是从这个地基自然生长出来的，而不是需要分别记忆的独立事实。

---

## 第零章：两个世界与一座桥

### 0.1 两种存在方式

程序同时存在于两个世界，这两个世界的性质根本不同：

**指称世界**（denotational world）：程序作为数学对象存在。它有内在结构，可以被完整检查，可以被静态分析，可以被复制和传输。磁盘上的 ELF 文件、目标文件、共享库——这些都是程序在指称世界里的存在形式。这个世界是**逻辑时间**里的世界：结构存在，但没有"现在"这个概念。

**操作世界**（operational world）：程序作为运行中的计算过程存在。它有状态，状态随物理时间变化，在任何给定时刻只有一个横截面可以被观察。进程、调用栈、堆的当前状态——这些是程序在操作世界里的存在形式。这个世界是**物理时间**里的世界：一个展开中的过程。

这两个世界之间**没有自然的、保持结构的双射**。

从指称到操作的映射是一个解释函数：

```
⟦·⟧ : ELF × Environment → Process
```

它不是单射（同一个 ELF 在不同 Environment 下产生不同的 Process）；不是满射（不是所有合法的 Process 状态都对应某个 ELF 的解释）；它是一个偏函数（在某些 Environment 下无定义）。

**工具链的全部工作，是构造和管理这两个世界之间的桥梁。** 链接、加载、ABI、运行时库——每一个机制都是这座桥的一部分。

### 0.2 自由变量：连接两个世界的核心概念

指称世界里的程序包含**自由变量**：符号引用、重定位记录、动态链接条目。这些自由变量是"尚未被绑定的值"——地址在编译时不可知，库的具体实现在链接时不可知，某些符号的最终目标在加载时才确定。

工具链的每个阶段是一次**部分绑定**：消除一些自由变量，可能引入新的自由变量（动态链接引入运行时才解析的符号），最终在进程启动时完成所有绑定，完成从指称到操作的跃迁。

这个框架是理解全部内容的钥匙：

| 阶段 | 操作 | 消除的自由变量 | 引入的自由变量 |
|------|------|--------------|--------------|
| 编译 | 翻译源码为目标文件 | 局部名字绑定 | 外部符号引用、重定位记录 |
| 静态链接 | 合并目标文件 | 跨 TU 符号引用、相对地址 | 动态符号引用（若有） |
| 加载 | `mmap` + 重定位填写 | 虚拟地址、静态符号引用 | 动态符号（PLT thunk） |
| 运行时绑定 | PLT resolve / `dlopen` | 动态符号引用 | — |

自由变量的逐步消除，就是程序从纯粹的指称对象向操作对象逐步具体化的过程。

---

## 第一章：ELF——指称世界的编码格式

### 1.1 ELF 是什么的编码

ELF（Executable and Linkable Format）不是一个简单的"二进制格式"。它是**带自由变量的程序指称语义的标准编码**。

理解这一点需要看清 ELF 的两套视图及其关系：

**链接视图**（linking view）：以节（section）为单位组织。节是链接器操作的逻辑单元，有语义类型（`.text` 是代码、`.data` 是初始化数据、`.bss` 是未初始化数据、`.rodata` 是只读数据、`.rela.text` 是代码段的重定位记录）。节是程序在指称世界里的**代数结构**。

**执行视图**（execution view）：以段（segment/program header）为单位组织。段是加载器操作的内存映射单元，有权限属性（可读、可写、可执行）和加载地址。段是程序向操作世界跃迁时的**拓扑结构**。

同一字节序列同时属于某个节和某个段——节和段是同一数据的两种分组方式，服务于两个不同的消费者（链接器 vs 加载器）。

```
ELF 文件结构：

ELF Header
    ├── e_type: ET_REL / ET_EXEC / ET_DYN / ET_CORE
    ├── e_entry: 入口点虚拟地址（操作世界的起点）
    ├── e_phoff: Program Header Table 偏移（执行视图）
    └── e_shoff: Section Header Table 偏移（链接视图）

Section Header Table（链接视图）
    ├── .text        [SHT_PROGBITS, SHF_ALLOC|SHF_EXECINSTR]
    ├── .rodata      [SHT_PROGBITS, SHF_ALLOC]
    ├── .data        [SHT_PROGBITS, SHF_ALLOC|SHF_WRITE]
    ├── .bss         [SHT_NOBITS,   SHF_ALLOC|SHF_WRITE]  ← 不占文件空间
    ├── .symtab      [SHT_SYMTAB]  ← 符号表（静态，可被 strip）
    ├── .dynsym      [SHT_DYNSYM]  ← 动态符号表（运行时必须存在）
    ├── .rela.text   [SHT_RELA]    ← .text 的重定位记录
    ├── .dynamic     [SHT_DYNAMIC] ← 动态链接元数据
    └── .gnu.version [SHT_GNU_versym] ← 符号版本

Program Header Table（执行视图）
    ├── PT_LOAD [R-X]: .text + .rodata → 代码段（只读可执行）
    ├── PT_LOAD [RW-]: .data + .bss   → 数据段（可读写）
    ├── PT_DYNAMIC:    .dynamic        → 动态链接器入口
    ├── PT_INTERP:     ld.so 路径      → 解释器（操作世界的引导者）
    ├── PT_GNU_RELRO:  需要在重定位后变只读的区域
    └── PT_TLS:        线程局部存储模板
```

### 1.2 `.bss` 的本质

`.bss` 是最能说明指称/操作世界分离的节：它在 ELF 文件里**不占任何字节**（SHT_NOBITS），只记录大小和对齐。

在指称世界里，"一块值全为零的内存"不需要被显式存储——零是默认值，只需声明大小。在操作世界里，这块内存必须真实存在。加载器在 `mmap` 时用匿名映射（内核保证零初始化）实现这个跃迁。

这是指称语义（声明存在）到操作语义（实际分配）的最简单的例子。

### 1.3 符号表的精确结构

符号（symbol）是指称世界里的基本对象。形式上，每个符号是一个六元组：

```
Symbol = (name, value, size, type, binding, visibility)
```

其中：
- `name`：字符串，在字符串表（`.strtab` / `.dynstr`）里的偏移
- `value`：在当前具体化层次下的绑定值——可重定位目标文件里是节内偏移，可执行文件/共享库里是虚拟地址
- `size`：实体的字节大小
- `type ∈ {NOTYPE, OBJECT, FUNC, SECTION, FILE, COMMON, TLS, IFUNC}`
- `binding ∈ {LOCAL, GLOBAL, WEAK}`：决定跨 TU 可见性和链接语义
- `visibility ∈ {DEFAULT, PROTECTED, HIDDEN, INTERNAL}`：决定动态链接可见性

`binding` 和 `visibility` 共同构成符号的**作用域语义**：

```
LOCAL   + 任何 visibility → 不跨目标文件，nm 显示小写
GLOBAL  + DEFAULT        → 可被其他模块引用，可被插入（interposed）
GLOBAL  + HIDDEN         → 可跨 TU 链接，但不进动态符号表
GLOBAL  + PROTECTED      → 进动态符号表，但不可被插入
WEAK    + DEFAULT        → 可被同名 GLOBAL 覆盖，用于提供可替换的默认实现
```

符号的 `value` 字段在链接过程中单调地向完全定义移动，这是一个偏序关系：

```
UNDEFINED < 节内偏移（可重定位） < 虚拟地址（链接后） < 运行时地址（加载后）
```

### 1.4 COMMON 符号：历史的遗产

`type = COMMON` 的符号是 C 语言 tentative definition（`int g;`，无初始化）的历史编码。COMMON 符号不属于任何节，只有大小和对齐约束。

链接器对多个同名 COMMON 符号的处理：取最大 size，合并为一个 `.bss` 条目。这是 FORTRAN 的 COMMON block 语义在 C 里的残留。

GCC 10 起默认 `-fno-common`，COMMON 符号退出历史舞台，所有 tentative definition 进 `.bss`，重复定义变成链接错误。

### 1.5 IFUNC：在操作世界里完成的指称绑定

`type = IFUNC`（GNU 扩展）是一种特殊机制：符号的最终值不是编译时确定的，而是通过一个**解析函数**在运行时动态确定。

```c
// 解析函数：根据 CPU 特性选择最优实现
static void* resolve_memcpy(void) {
    if (cpu_has_avx512()) return memcpy_avx512;
    if (cpu_has_avx2())   return memcpy_avx2;
    return memcpy_generic;
}
// 声明 IFUNC 符号
void* memcpy(void*, const void*, size_t)
    __attribute__((ifunc("resolve_memcpy")));
```

IFUNC 是"指称绑定推迟到操作世界"的极端形式：符号名（`memcpy`）在指称世界里存在，但其实际绑定（哪个实现）只有在进程启动后探测 CPU 特性时才能确定。glibc 大量使用 IFUNC 实现 CPU 特性分发（`memcpy`、`memset`、`strcmp` 等）。

---

## 第二章：重定位——自由变量的延迟求值

### 2.1 重定位的形式语义

重定位记录是指称世界里**自由变量的占位符**。形式上，每条重定位记录是一个四元组：

```
Relocation = (offset, type, symbol, addend)
```

语义：在地址 `offset` 处，填写值 `f(type)(S, A, P, GOT, PLT)` 的计算结果，其中：
- `S` = 符号 `symbol` 的运行时地址
- `A` = addend（常数调整量）
- `P` = 被修改位置的地址（place）
- `GOT` = Global Offset Table 的地址
- `PLT` = Procedure Linkage Table 的地址

不同的 `type` 对应不同的公式 `f`：

```
R_X86_64_64:      S + A              （绝对 64 位地址）
R_X86_64_PC32:    S + A - P          （相对 32 位偏移，用于 call/jmp）
R_X86_64_GOT32:   G + A              （GOT 条目的偏移）
R_X86_64_PLT32:   L + A - P          （PLT 条目的相对偏移）
R_X86_64_GOTPCREL: G + GOT + A - P  （GOT 条目的 PC 相对地址）
R_X86_64_COPY:    在可执行文件里为数据符号预留空间
R_X86_64_GLOB_DAT: S                 （初始化 GOT 条目）
R_X86_64_JUMP_SLOT: S                （初始化 PLT/GOT 条目，运行时填写）
R_X86_64_RELATIVE: B + A             （位置无关代码的基址重定位）
R_X86_64_TPOFF32: S + A - tp        （TLS，相对于线程指针的偏移）
```

这些不是需要记忆的魔法数字，而是同一个"自由变量求值"框架在不同场景下的实例：绝对地址、相对地址、间接地址（通过 GOT）、惰性地址（通过 PLT）。

### 2.2 两类重定位节

`.rela.text`（或 `.rel.text`）：链接时处理的重定位。链接器在合并目标文件时解析这些记录，填写节内的符号引用，生成可执行文件或共享库。完成后这些记录消失（不进运行时）。

`.rela.dyn` 和 `.rela.plt`：加载时处理的重定位。`ld.so` 在加载共享库时处理这些记录。`.rela.dyn` 处理数据引用（填写 GOT 条目）；`.rela.plt` 处理函数引用（初始化 PLT 的 GOT 条目）。

这个区分映射到自由变量消除的时机：链接时消除 vs 加载时消除。

### 2.3 位置无关代码（PIC）的本质

共享库必须是位置无关的——它可以被加载到虚拟地址空间的任意位置。这个要求的形式语义：库内所有绝对地址引用都必须在运行时修正，或者完全避免绝对地址引用。

`-fPIC` 的实现策略：把所有需要运行时地址的引用通过 GOT（Global Offset Table）间接化。

```
GOT：一个指针数组，存放全局符号的运行时地址。
     GOT 本身的地址相对于 .text 是已知的（PC 相对），
     GOT 的内容在加载时由 ld.so 填写。
```

GOT 是指称世界和操作世界之间的**接缝**：它在指称世界里有固定的结构（一个指针数组），在操作世界里有运行时才确定的内容。

PIC 代码访问全局变量的汇编：
```asm
; 访问全局变量 g
movq    g@GOTPCREL(%rip), %rax    ; 把 g 的 GOT 条目地址加载到 rax
; 这条指令的重定位：R_X86_64_GOTPCREL，链接时填写 GOT 条目的 PC 相对偏移
movl    (%rax), %eax              ; 从 GOT 条目里读取 g 的运行时地址
; 运行时：ld.so 已经把 g 的实际地址写进了 GOT
```

非 PIC 代码（可执行文件）可以使用绝对地址（链接时地址已知），或者通过 `R_X86_64_COPY` 把共享库里的数据符号复制到可执行文件的数据段。`COPY` 重定位是一个历史遗产，它破坏了数据符号的单一实例语义——真正理解它的人不多。

### 2.4 `R_X86_64_COPY` 的深层问题

当可执行文件（non-PIC）引用共享库里的全局变量时，链接器生成 `COPY` 重定位：

1. 在可执行文件的 `.bss` 里为该变量预留空间
2. 生成 `R_X86_64_COPY` 记录，指示 `ld.so` 在加载时把共享库里的初始值**复制**过来
3. 可执行文件和所有其他库都通过符号解析（因为可执行文件的符号优先级最高）访问可执行文件里的副本

结果：变量实际上存在于可执行文件的 `.bss`，共享库里的那份地址从来不被使用。这是"指称语义里有两个实体"（库里的原始定义 + 可执行文件里的副本），但"操作语义里只有一个"的微妙情形。若共享库内部用 `-Bsymbolic` 绑死了对该变量的引用，库内访问和库外访问就会指向不同的内存——这是 COPY 重定位被视为历史遗产的原因。

---

## 第三章：链接——指称世界的代数运算

### 3.1 链接的形式语义

链接是一个**代数运算**：把多个带自由变量的程序表示合并为一个自由变量更少的程序表示。

形式上，设 `M₁, M₂, ..., Mₙ` 是 n 个目标文件，每个 `Mᵢ` 包含：
- 定义符号集合 `Def(Mᵢ)`
- 未定义符号集合 `Undef(Mᵢ)`
- 节集合和重定位记录

链接的核心操作是求解方程组：

```
∀s ∈ Undef(Mᵢ): s 必须在某个 Def(Mⱼ) 中有唯一的（或弱的）定义
```

静态链接的结果是一个 `Undef` 为空的 ELF（可执行文件），或允许部分 `Undef` 的 ELF（共享库，`-Wl,--no-undefined` 要求即便共享库也必须全部解析）。

### 3.2 符号解析的偏序语义

当多个目标文件对同一符号有定义时，链接器按以下偏序选择：

```
GLOBAL 定义 > WEAK 定义 > COMMON 符号 > UNDEFINED
```

在同一优先级内，选择规则是：
- 两个 `GLOBAL` 定义同名 → 链接错误（multiple definition）
- 一个 `GLOBAL` + 一个 `WEAK` → 选 GLOBAL
- 两个 `WEAK` → 任选其一（实践中选先遇到的）
- `WEAK` + `COMMON` → 选 WEAK（COMMON 被忽略）
- 两个 `COMMON` → 合并（取较大 size）

这个偏序是链接语义的完整规范。任何"奇怪的链接行为"都可以通过这个偏序精确解释。

### 3.3 静态库的操作语义：单遍归档抽取

静态库（`.a`）是目标文件的归档（archive），由 `ar` 工具创建，包含一个符号索引（`ar -t` 可见）。

链接器处理静态库的算法：

```
pending = {所有当前未定义符号}
for each archive A (按命令行顺序):
    repeat:
        found = false
        for each member M in A:
            if Def(M) ∩ pending ≠ ∅:
                纳入 M
                pending = (pending - Def(M)) ∪ Undef(M)
                found = true
        until not found
// 关闭 A，继续下一个，不回头
```

这个算法的性质：
- **单调性**：`pending` 集合单调变化（解析减少，新引入增加）
- **顺序敏感性**：先遇到的 archive 先被扫描，后遇到的 archive 里的新 `Undef` 无法回头到前面的 archive 解析
- **不动点终止**：在每个 archive 内部反复扫描直到 `pending` 不变

`--start-group / --end-group` 把多个 archive 合并为一个虚拟 archive，在组内反复扫描直到全局不动点。这解决了 archive 间的循环依赖，代价是 O(n²) 的扫描复杂度。

### 3.4 链接脚本：地址空间的代数规范

链接脚本（linker script）是链接器的配置语言，它定义了输出 ELF 的**地址空间布局**：

```ld
SECTIONS {
    . = 0x400000;              /* 设置当前地址计数器 */

    .text : {
        *(.text.startup)       /* 启动代码优先 */
        *(.text .text.*)       /* 所有输入的 .text 节 */
    }

    . = ALIGN(4096);           /* 页对齐 */

    .rodata : { *(.rodata .rodata.*) }

    . = ALIGN(4096);

    .data : { *(.data .data.*) }

    .bss : {
        __bss_start = .;       /* 导出符号：bss 起始地址 */
        *(.bss .bss.*)
        *(COMMON)
        __bss_end = .;
    }
}
```

链接脚本做的事情，形式上是：把多个输入节（带相对偏移）映射到一个输出地址空间（带绝对虚拟地址）。这是从"指称世界的局部坐标系"到"操作世界的全局坐标系"的坐标变换。

每个 GNU/Linux 工具链都有一个默认链接脚本（`ld --verbose` 可查看）。嵌入式开发、操作系统内核开发必须理解和修改链接脚本，因为地址空间布局不能依赖默认值。

### 3.5 段合并与 COMDAT

C++ 的 `inline` 函数、模板实例化、虚函数表会在每个引用它们的 TU 里各自产生一份定义。链接器必须把这些"相同的"重复定义合并成一份。

COMDAT（Common Data）机制：把这类定义放进带标识符的 COMDAT 组（`.text._ZN3FooC1Ev` 这样的节名）。链接器对相同标识符的 COMDAT 组，选择其中一份纳入，丢弃其余。

选择策略：`GRP_COMDAT` 节组，链接器任选其一（实践中选最先遇到的）。这个"任选"是有前提的：所有副本必须语义等价。这个前提没有机制验证，只能通过约定保证（ODR）。

Windows PE 格式的等价机制是 COMDAT section，语义相同但实现不同。

### 3.6 符号可见性与动态符号表

静态链接完成后，ELF 里有两张符号表：

`.symtab`（静态符号表）：包含所有符号，供调试器使用。可被 `strip` 删除，不影响运行。

`.dynsym`（动态符号表）：只包含动态链接所需的符号——导出给其他库的符号，以及从其他库导入的未定义符号。不能被删除，是运行时必须的结构。

`-fvisibility=hidden` 的作用：把 ELF 里所有默认 DEFAULT visibility 的符号改为 HIDDEN。HIDDEN 符号不进 `.dynsym`，不参与动态链接的符号解析，对其他库不可见。这直接缩小了动态符号表，减少了符号冲突的机会，也允许链接器对库内调用做直接绑定优化（不走 PLT）。

---

## 第四章：装载——从指称世界到操作世界的跃迁

### 4.1 `execve`：一次本体论事件

`execve(path, argv, envp)` 是从指称到操作跃迁的触发点。它是一个系统调用，但它的语义不同于普通系统调用——它不是在当前进程里执行操作，而是**用一个新的操作世界实例替换当前进程**。

内核在 `execve` 里做的事：
1. 读取 ELF Header，确认魔数（`\x7fELF`）和架构
2. 解析 Program Headers，找到 `PT_INTERP`（动态链接器路径）
3. 为新进程建立虚拟地址空间（`mm_struct`）
4. 若有 `PT_INTERP`：把动态链接器（`ld.so`）映射进地址空间，控制权交给它；否则直接跳到 `e_entry`

`PT_INTERP` 的存在是关键：它意味着内核不直接执行 ELF，而是把执行权委托给用户态的 `ld.so`。动态链接器本身也是一个 ELF（`ET_DYN` 类型），内核必须能在不依赖任何动态链接的情况下加载它——因此 `ld.so` 本身是静态链接的，且完全位置无关。

静态链接的可执行文件（没有 `PT_INTERP`）：内核直接解析 PT_LOAD 段，`mmap` 进内存，跳到 `e_entry`（`_start` 的虚拟地址）。没有 `ld.so`，没有动态链接，一步跃迁完成。

### 4.2 `mmap`：指称到操作的物理桥梁

虚拟内存映射是跃迁的具体机制。`mmap` 系统调用建立从**虚拟地址区间**到**物理内容来源**的映射：

```c
mmap(addr,          // 虚拟地址（或 NULL 由内核选择）
     length,        // 区间长度
     prot,          // 权限：PROT_READ | PROT_WRITE | PROT_EXEC
     flags,         // MAP_PRIVATE | MAP_SHARED | MAP_ANONYMOUS | MAP_FIXED
     fd,            // 文件描述符（-1 表示匿名映射）
     offset)        // 文件内偏移
```

`ld.so` 对每个 `PT_LOAD` 段执行一次 `mmap`：

```
PT_LOAD [RE]: mmap(vaddr, filesz, PROT_READ|PROT_EXEC, MAP_PRIVATE|MAP_FIXED, fd, offset)
              → 建立从虚拟地址到 ELF 文件的只读执行映射
              → 内存页按需从磁盘加载（page fault 驱动）

PT_LOAD [RW]: mmap(vaddr, filesz, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED, fd, offset)
              → 可读写数据段（私有映射，写时复制）
              若 memsz > filesz：
              mmap(vaddr+filesz, memsz-filesz, PROT_READ|PROT_WRITE,
                   MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0)
              → .bss 部分：匿名映射，内核保证零初始化
```

`MAP_PRIVATE` 是写时复制（Copy-on-Write）语义：多个进程映射同一个文件时共享物理页；任何一个进程写入时，内核为该进程创建私有副本，其他进程不受影响。这是动态库共享物理内存的机制——`.text` 段在所有使用同一库的进程间共享同一组物理页，节省内存。

### 4.3 `ld.so`：操作世界的引导者

动态链接器（`/lib64/ld-linux-x86-64.so.2`）是整个跃迁过程的核心执行者。它的工作是一个精确定义的算法：

**阶段一：自举（bootstrap）**

`ld.so` 被内核加载时，它自身还没有被重定位（它的 GOT 条目还没被填写）。它必须在没有任何外部依赖的情况下完成自身的重定位——一个自举问题。

实现方式：`ld.so` 的入口点是位置无关的汇编，使用 PC 相对寻址找到自己的 `PT_DYNAMIC` 段，处理自身的 `R_X86_64_RELATIVE` 重定位（这类重定位只需要知道加载基址，不需要符号查找）。

**阶段二：依赖解析（dependency resolution）**

读取主 ELF 的 `.dynamic` 节，解析 `DT_NEEDED` 条目，递归加载所有依赖库。这是一个有向图的 BFS/DFS 遍历：

```
依赖图：
main → libfoo.so → libbar.so
     → libbaz.so → libbar.so（共享依赖，只加载一次）
```

共享库只被加载一次——`ld.so` 维护一个已加载库的 `link_map` 链表，通过 soname（`DT_SONAME`）去重。

**阶段三：库搜索（library search）**

对每个 `DT_NEEDED` 的库名，按以下顺序搜索：

```
1. DT_RPATH（若存在且无 DT_RUNPATH）：继承到整个依赖树
2. LD_LIBRARY_PATH：环境变量，安全机制会在 setuid 程序里忽略
3. DT_RUNPATH：只对直接依赖生效，不继承
4. /etc/ld.so.cache：ldconfig 构建的缓存，避免每次遍历文件系统
5. /lib, /usr/lib 等默认目录
```

`DT_RPATH` 和 `DT_RUNPATH` 的继承性差异是设计决策，不是 bug：`DT_RPATH` 的全局继承给了调用者过大的权力，`DT_RUNPATH` 的局部性更安全但要求每层库自己设置路径。

**阶段四：重定位（relocation processing）**

所有库加载完毕后，`ld.so` 处理 `.rela.dyn` 里的重定位记录。对每条记录，根据 `type` 和 `symbol` 计算值，写入目标地址。

符号查找算法（对 DEFAULT visibility 的全局符号）：

```
对于符号 s：
1. 在全局符号表（所有已加载库的 .dynsym 的并集）里查找
2. 按加载顺序，返回第一个定义 s 的库里的地址
3. 若未找到且重定位是强引用：报错退出
   若未找到且重定位是弱引用：填 0
```

"按加载顺序返回第一个"就是符号插入（interposition）的机制：`LD_PRELOAD` 的库最先加载，所以它的符号"赢"。

**阶段五：初始化（initialization）**

按依赖的逆拓扑序（叶节点先于父节点），执行每个库的 `.init_array` 里的函数指针。这些函数指针指向编译器为每个 TU 生成的 `_GLOBAL__sub_I_*` 函数（C++ 全局构造函数的实现），以及用 `__attribute__((constructor))` 标注的函数。

之后，控制权交给主 ELF 的入口点（`_start`）。

### 4.4 PLT/GOT 机制：惰性求值的实现

PLT（Procedure Linkage Table）和 GOT（Global Offset Table）实现了函数符号解析的**惰性求值**：第一次调用时才解析，之后缓存结果。

初始状态（加载完毕，`RTLD_LAZY` 模式）：

```
call foo          ; 汇编指令：调用 foo
    ↓
foo@plt:          ; PLT 条目（存在于 .plt 节）
    jmp *foo@GOT  ; 间接跳转到 GOT 里存的地址
                  ; 初始值：PLT 的下一条指令（不是 foo 的真实地址！）
    push $n       ; 压入重定位索引
    jmp PLT[0]    ; 跳到 PLT[0]

PLT[0]:           ; PLT 的第 0 个条目（特殊）
    push link_map ; 压入当前库的 link_map
    jmp *GOT[2]   ; 跳到 ld.so 的 _dl_runtime_resolve
```

第一次调用时：`_dl_runtime_resolve` 根据重定位索引和 `link_map` 找到符号名，执行符号查找，得到 `foo` 的真实地址，**写入 `foo@GOT`**，然后跳到 `foo`。

第二次调用时：`PLT` 里的 `jmp *foo@GOT` 直接跳到 `foo` 的真实地址，`_dl_runtime_resolve` 不再被调用。

`-z now`（`RTLD_NOW`）：加载时立即解析所有符号（处理所有 `.rela.plt` 里的 `JUMP_SLOT` 重定位），消除懒绑定。优点：确定性（不会在运行时中途报"符号未找到"），安全性（GOT 可以设为只读，配合 `-z relro`）。代价：启动时间增加（与动态符号数量成正比）。

`-z relro`（RELRO）：把一部分 GOT（非 PLT 部分，`.got`）在重定位完成后设为只读（`mprotect` 调用）。`-z now -z relro` 一起使用（Full RELRO），把整个 GOT（包括 `.got.plt`）都设为只读，消除 GOT 覆写攻击面。

### 4.5 虚拟地址空间的完整结构

一个典型的 x86-64 Linux 进程地址空间（`/proc/PID/maps` 的抽象）：

```
高地址（内核空间，用户不可访问）
────────────────────────────────────
[stack]          PROT_READ|WRITE, 向低地址增长
                 ← rsp（栈指针）当前位置
────────────────────────────────────
[mmap 区域]      共享库的映射（从高到低分配）
    libstdc++.so.6  [re] .text
                    [rw] .data/.bss
    libm.so.6       ...
    libc.so.6       ...
    ld-linux.so.2   ...
────────────────────────────────────
[heap]           PROT_READ|WRITE, 向高地址增长
                 ← brk（堆顶）当前位置
────────────────────────────────────
[BSS]            PROT_READ|WRITE（匿名映射）
[data]           PROT_READ|WRITE（文件私有映射）
[rodata]         PROT_READ（文件映射）
[text]           PROT_READ|EXEC（文件映射）
低地址
```

ASLR（地址空间布局随机化）：内核在每次 `execve` 时对栈、mmap 区域、堆的起始地址施加随机偏移。这是安全机制，代价是地址不可预测（因此无法使用硬编码地址，共享库的 PIC 要求因此有了安全维度之外的意义）。

---

## 第五章：ABI——跨越边界的类型系统同态

### 5.1 ABI 的形式定义

ABI 是两个模块在二进制接口上的**相容性条件**。形式上，模块 A 和模块 B 在接口 I 上 ABI 兼容，当且仅当存在一个**类型系统同态**：

```
φ: Types_A → Types_B
```

使得对接口 I 上出现的每个类型 T：
- `sizeof_A(T) = sizeof_B(φ(T))`（尺寸相同）
- `alignof_A(T) = alignof_B(φ(T))`（对齐相同）
- 对每个成员 `m`：`offsetof_A(T, m) = offsetof_B(φ(T), m)`（成员偏移相同）
- 函数调用约定相同（参数/返回值的寄存器分配方案）
- 名字修饰方案相同（`φ` 保持函数签名的编码）
- 异常处理协议相同（`_Unwind_*` 的调用约定）

这个同态条件在实践中从来不被显式验证——它隐含在"使用相同编译器版本、相同编译选项、相同标准库"的约定里。当约定被违反，同态条件静默失效，结果是未定义行为。

### 5.2 x86-64 System V psABI：调用约定的完整规范

x86-64 Linux 的平台 ABI（psABI）精确规定了函数调用的每个细节：

**寄存器用途分类**：

```
参数寄存器（整型/指针）：rdi, rsi, rdx, rcx, r8, r9（前6个参数）
参数寄存器（浮点）：xmm0–xmm7（前8个浮点参数）
返回值：rax（整型），rdx（第二个整型返回值），xmm0（浮点）
调用者保存（caller-saved）：rax, rcx, rdx, rsi, rdi, r8–r11, xmm0–xmm15
被调用者保存（callee-saved）：rbx, rbp, r12–r15
栈指针：rsp（调用时必须 16 字节对齐）
帧指针：rbp（可选，`-fomit-frame-pointer` 省略）
```

**参数传递的分类算法**：

对于 struct 类型的参数，psABI 定义了一个递归分类算法（`classify_argument`）：

```
对每个 eightbyte（8 字节块）：
    若该块全是整型/指针 → INTEGER 类
    若该块全是浮点     → SSE 类
    若 struct 总大小 > 64 字节 → MEMORY 类（通过栈传递，调用者分配）
    若有未对齐成员    → MEMORY 类
```

`MEMORY` 类的 struct 通过**隐式引用**传递：调用者在栈上分配空间，把指针作为隐藏的第一个参数传入。这是 C++ 中"返回 struct 的函数实际上有一个隐藏的输出指针参数"（NRVO/RVO 的实现基础）的原因。

**Red zone**：rsp 以下 128 字节是"红区"，信号处理器保证不使用这段空间。叶函数（不调用其他函数的函数）可以直接使用红区存放局部变量，无需调整 rsp——这是一个 psABI 赐予的小性能优化。

### 5.3 名字修饰（Name Mangling）：类型信息的编码

C++ name mangling 是把函数签名编码进符号名的方案，使得链接器能区分重载函数。Itanium C++ ABI 的 mangling 规则（Linux/macOS 通用）：

```
_Z <name> <type>

其中：
<name> 是函数的限定名编码：
    N ... E          带限定符（命名空间/类）
    数字 + 字符串    字面名字（如 3Foo = Foo）
    St               std::
    S_ / S0_ / ...  已编码实体的反引用（压缩）

<type> 是参数类型序列：
    i = int, l = long, d = double, v = void
    P = 指针（Pv = void*）
    R = 引用（Ri = int&）
    K = const
    数字 + 名字 = 用户定义类型
```

例：
```
void foo(int, double)        → _Z3fooid
Foo::bar(int) const          → _ZNK3Foo3barEi
std::vector<int>::push_back  → _ZNSt6vectorIiSaIiEE9push_backERKi
```

返回值不参与 mangling（重载不以返回类型区分）。`noexcept` 在 C++17 起成为函数类型的一部分，但 Itanium ABI 暂未把它编码进 mangling（这是一个已知的 ABI 漏洞：`noexcept` 版本和非 `noexcept` 版本有相同的 mangled name，但不同的类型）。

MSVC 有完全不同的 mangling 方案，且未公开规范（虽然已被逆向工程）。这是 Windows 上 MinGW 编译的 C++ 代码无法与 MSVC 编译的 C++ 代码互操作的根本原因。

### 5.4 C++ 对象模型：vtable 的精确结构

C++ 虚函数通过 vtable（虚函数表）实现运行时多态。vtable 是一个函数指针数组，每个含虚函数的类有一个 vtable，存放在只读数据段（`.rodata`）。

完整的 vtable 结构（Itanium ABI）：

```
vtable for Derived:
    [0]: offset to top（Derived 对象起始位置相对 vtable 指针的偏移，通常为 0）
    [1]: &typeinfo for Derived（RTTI 信息）
    [2]: &Derived::vfunc1（或 Base::vfunc1 若未重写）
    [3]: &Derived::vfunc2
    ...

若 Derived 多继承自 Base1 和 Base2：
vtable for Derived:
    ── Base1 的 vtable 部分 ──
    [0]: 0（offset to top，Base1 子对象就是 Derived 起始）
    [1]: &typeinfo for Derived
    [2]: &Derived::vfunc1
    ── Base2 的 vtable 部分（thunk 区）──
    [n]: -sizeof(Base1 part)（offset to top，负值）
    [n+1]: &typeinfo for Derived
    [n+2]: &thunk for Derived::vfunc1
           （thunk 调整 this 指针后跳到真实实现）
```

每个多态对象的第一个（隐藏的）成员是**vptr**，指向该类的 vtable 的第一个虚函数条目（即 `vtable[2]`）。

这个结构意味着：
- 在 vtable 中间插入虚函数会改变所有后续虚函数的索引 → ABI 破坏
- 在末尾追加虚函数，基类的 vtable 布局不变，派生类 vtable 需要扩展 → 若派生类在别的库里，那个库的 vtable 也需重建 → ABI 破坏
- 改变基类会改变派生类的 offset-to-top 值 → ABI 破坏

### 5.5 异常处理的二进制机制

C++ 异常的实现是零运行时开销（zero-cost exception）模型：正常执行路径没有任何开销，代价在于二进制大小（unwind 表）和异常路径的执行时间。

实现依赖两张表：

**`.eh_frame`（或 `.debug_frame`）**：DWARF CFI（Call Frame Information）表，记录在每个程序计数器位置，如何恢复调用者的寄存器（特别是如何恢复 `rsp` 和返回地址）。这是 unwinder 遍历调用栈的导航图。

**`.gcc_except_table`**（语言相关数据）：记录每个函数的 try 块范围、catch 块的类型和地址、需要调用析构函数的对象（cleanup）。

抛出异常的流程：

```
throw e;
    ↓
__cxa_throw(exception_object, typeinfo, destructor)
    ↓
_Unwind_RaiseException(exception)
    ↓
Phase 1（搜索阶段）：沿调用栈向上，对每个栈帧：
    1. 用 .eh_frame 找到当前帧的 LSDA（Language-Specific Data Area）
    2. 调用 __gxx_personality_v0（GCC 的 personality routine）
    3. personality routine 查询 .gcc_except_table：
       这个帧有没有能 catch 这个类型的 handler？
    4. 若有：_URC_HANDLER_FOUND，停止 Phase 1
    5. 若无：继续向上

Phase 2（清理阶段）：从当前帧重新向上，对每个帧：
    1. 再次调用 personality routine
    2. 运行 cleanup（析构函数）
    3. 直到 Phase 1 找到的 handler 帧
    4. 恢复寄存器，跳到 catch 块
```

`typeinfo`（RTTI）：异常类型匹配通过比较 `typeinfo` 对象的**指针**（不是内容）实现。同一类型必须有同一个 `typeinfo` 实例——这依赖于 `typeinfo` 符号的唯一性。若同一类型的 `typeinfo` 因 hidden visibility 在两个库里各有一份，指针比较失败，`catch` 块捕获不到。

---

## 第六章：动态库——指称世界的可组合单元

### 6.1 共享库的本质

共享库（`ET_DYN` 类型的 ELF）是**可以被多个进程同时映射的代码和数据的集合**，同时保持各进程数据的私有性。

这个看似简单的需求导致了一系列设计约束：

- **代码必须位置无关**（PIC）：多个进程把库映射到不同的虚拟地址，代码本身不能包含绝对地址，所有地址引用必须通过 GOT 间接化。

- **数据必须私有**：每个进程有自己的数据副本（`MAP_PRIVATE` + 写时复制）。`.text` 页在所有进程间共享同一物理页，`.data` 页在进程写入时被内核复制为私有页。

- **符号语义必须明确**：在多个库可能定义同名符号的环境里，必须有明确的解析规则（加载顺序优先）。

### 6.2 soname、real name 与链接名

共享库有三个"名字"，服务于三个不同的目的：

**real name**：实际文件名，含完整版本号。`libfoo.so.1.2.3`。存放在文件系统。

**soname**：编码在库的 `DT_SONAME` 字段里的名字，含主版本号。`libfoo.so.1`。`ld.so` 在运行时查找的是 soname，不是 real name。`/usr/lib/libfoo.so.1` 通常是指向 real name 的符号链接。

**链接名**：编译时 `-lfoo` 查找的名字。`libfoo.so`，不含版本号。通常是指向 soname 的符号链接。

这个三层命名方案实现了**主版本号兼容性的自动管理**：
- 应用程序的 `DT_NEEDED` 存的是 soname（`libfoo.so.1`）
- 只要主版本号不变（向后兼容的 ABI 演化），所有使用 `libfoo.so.1` 的应用无需重新编译
- 主版本号递增（ABI 破坏性变更）时，新库有新 soname，旧应用继续使用旧库，新应用链接新库

### 6.3 符号版本（Symbol Versioning）

glibc 实现了更细粒度的版本控制：**单个符号级别的版本**。

机制：`.gnu.version_d`（版本定义节）和 `.gnu.version_r`（版本需求节）和 `.gnu.version`（每个符号的版本索引）。

```
// glibc 里的声明：
__asm__(".symver memcpy_new, memcpy@@GLIBC_2.14");
__asm__(".symver memcpy_old, memcpy@GLIBC_2.2.5");
// @@ 表示默认版本（新链接时使用），@ 表示旧版本（向后兼容）
```

效果：`libfoo.so.6` 里可以同时存在 `memcpy@GLIBC_2.2.5` 和 `memcpy@GLIBC_2.14`，它们是不同的函数（可以有不同实现）。链接时的二进制记录它使用的是哪个版本（存在 `.gnu.version_r` 里）；运行时 `ld.so` 按版本匹配，而不仅仅按名字匹配。

这是 glibc 能在同一个 `.so.6` 里保持 20 年向后兼容性的核心机制。

### 6.4 命名空间与隔离：ELF 的设计权衡

ELF 的默认设计是**扁平全局符号命名空间**：所有 `DEFAULT` visibility 的符号混在一个池子里，按加载顺序解析。

这个设计有其内在逻辑：
- 允许符号插入（LD_PRELOAD、malloc 替换）
- 允许跨库的单例（全局 allocator、全局 locale）
- 简化调试（所有符号都可见）

代价是隔离性缺失。补偿手段形成一个从弱到强的谱：

```
DEFAULT visibility                → 全局可见，可被插入
PROTECTED visibility              → 全局可见，但本库内引用不可被插入
HIDDEN visibility                 → 不进 .dynsym，对其他库不可见
RTLD_LOCAL（dlopen 的 flag）     → 库的符号不加入全局命名空间
dlmopen（独立 link_map namespace）→ 完全独立的命名空间，如同另一个进程
```

`dlmopen` 是最强的隔离，但代价高昂：独立的命名空间意味着独立的 `libc`、独立的 TLS 区域、独立的 `malloc`（或需要特殊处理）。真正的库隔离需要的不只是命名空间，而是完整的运行时隔离——这在 Linux 进程模型里只有通过 `fork` + 进程间通信才能真正实现。

---

## 第七章：线程局部存储（TLS）——执行状态的结构化私有化

### 7.1 TLS 的本质问题

线程局部存储解决的问题：全局变量（指称世界里的单个实体）在操作世界里需要有**线程私有的实例**。

这是指称/操作世界分离的一个具体体现：在源代码层（指称世界），`thread_local int x;` 是一个单一的声明；在运行时（操作世界），每个线程有自己的 `x` 的副本。

### 7.2 四种 TLS 访问模型

TLS 变量的访问需要找到"当前线程的变量副本"。这个查找有四种模型，按速度从快到慢：

**Local Exec**（`-ftls-model=local-exec`）：只适用于可执行文件里定义的 TLS 变量。编译时已知相对于线程指针（`fs` 段寄存器指向的 TCB）的固定偏移，访问是单条指令：

```asm
movl %fs:offset, %eax    ; 直接用 fs 相对寻址，一条指令
```

**Initial Exec**（`-ftls-model=initial-exec`）：适用于启动时加载的库。偏移编译时未知（库可以加载到不同位置），但**启动时固定**。通过 GOT 条目（`R_X86_64_GOTTPOFF` 重定位）存放偏移值：

```asm
movq  x@GOTTPOFF(%rip), %rax   ; 从 GOT 读取 TLS 偏移
movl  %fs:(%rax), %eax          ; 用偏移访问 TLS
```

Initial Exec 模型的 TLS 变量需要在进程启动时预分配静态 TLS 空间（`PT_TLS` 段指定初始大小）。`dlopen` 一个使用 Initial Exec 的库时，若静态 TLS 空间已被其他库占满，就会失败（`cannot allocate memory in static TLS block`）。

**Local Dynamic**：适用于模块内定义、模块内使用的 TLS 变量。通过一次 `__tls_get_addr` 调用获取模块的 TLS 基址，然后加常量偏移访问各变量——多个 TLS 变量共享一次 `__tls_get_addr` 调用。

**Global Dynamic**（`-ftls-model=global-dynamic`）：最通用，适用于 `dlopen` 加载的库。每次访问调用 `__tls_get_addr(module_id, offset)`，运行时按 module_id 查找该模块的 TLS 块，加 offset：

```asm
leaq  x@tlsgd(%rip), %rdi     ; 加载 {module_id, offset} 对的地址
call  __tls_get_addr           ; 获取 &x（当前线程的副本）
```

`__tls_get_addr` 是 `ld.so` 提供的函数，它维护每个线程的 TLS DTV（Dynamic Thread Vector）——一个指针数组，每个元素指向一个模块的 TLS 块。新模块（`dlopen`）在 DTV 里分配新条目，动态扩展。

### 7.3 TLS 的初始化

`PT_TLS` 段定义了 TLS 的"模板"：它的内容是 TLS 变量的初始值（`.tdata`），大小包含未初始化部分（`.tbss`）。

每个新线程创建时，`pthread` 库为其分配 TLS 块，把 `PT_TLS` 的内容复制过来（初始化 `.tdata`），`.tbss` 部分清零。`fs` 寄存器指向该线程的 TCB（Thread Control Block），紧邻 TLS 块。

---

## 第八章：运行时库——操作世界的基础设施

### 8.1 为什么运行时库必须存在

运行时库是**指称语义与操作语义之间的基础设施层**。某些操作在指称世界里有意义（`new`、`throw`、`thread_local`），但在操作世界里没有直接对应的机器指令，必须通过库函数实现。

编译器会为源代码中没有显式写出的操作生成库调用，这些是**隐式依赖**：

```
操作                     → 运行时库函数
──────────────────────────────────────────
64位整数除法（32位平台）  → __divdi3, __udivdi3 (libgcc)
__int128 运算             → __divti3 等 (libgcc)
软浮点（无 FPU 的平台）   → __addsf3, __mulsf3 等 (libgcc)
原子操作（无原生指令）    → __atomic_load, __atomic_store (libatomic)
栈溢出检测               → __stack_chk_fail (libgcc/libc)
异常抛出                 → __cxa_throw (__cxa_* family, libstdc++/libc++)
异常展开                 → _Unwind_RaiseException (libgcc_s/libunwind)
RTTI                     → __dynamic_cast, __cxa_typeid
全局构造/析构注册        → __cxa_atexit
线程局部变量             → __tls_get_addr (ld.so)
内存分配                 → malloc/free/new/delete (libc/libstdc++)
```

### 8.2 启动序列的完整链路

```
execve
  ↓
内核：加载 ld.so（若有 PT_INTERP）
  ↓
ld.so：自举 → 加载依赖 → 重定位 → .init_array（各库的构造函数）
  ↓
_start（来自 crt1.o，由 gcc/clang 驱动自动链入）
  ├── 设置帧指针为 0（标记调用栈顶端）
  ├── 从内核栈读取 argc, argv, envp
  └── 调用 __libc_start_main
         ├── 初始化 glibc 内部状态（locale, getenv 缓存等）
         ├── 设置 TLS（主线程的 TLS 块）
         ├── 注册 .fini_array 到 atexit
         ├── 调用 .init_array（主程序的全局构造函数）
         │   （ld.so 已调用各库的 .init_array，此时调用主程序的）
         ├── 调用 main(argc, argv, envp)
         ├── main 返回后：调用 exit(main的返回值)
         └── exit：调用 atexit 链（.fini_array、__cxa_atexit 注册的函数）
```

`crt1.o`、`crti.o`、`crtbegin.o`（以及对应的 `crtend.o`、`crtn.o`）由编译器驱动（`gcc`/`clang`）自动添加到链接命令。直接调用 `ld` 而不经过驱动，就会缺少这些文件，导致 `undefined reference to '_start'` 或 `__libc_start_main`。`gcc -v` 可以查看驱动实际传递给 `ld` 的完整参数列表。

### 8.3 `libgcc_s` 与 `compiler-rt`：两套运行时支持库

**libgcc_s**（GCC 运行时）：提供：
- 软件实现的算术运算（多精度整数、软浮点）
- 异常展开（`_Unwind_*` 系列，实现 DWARF CFI 遍历）
- 栈保护

**compiler-rt**（LLVM 运行时）：Clang 的对应物，提供相同的功能集，且可以与 libgcc_s 的符号名兼容（`_Unwind_*` 等）。

两者在同一进程里共存是危险的：`_Unwind_RaiseException` 的实现细节（如何解释 DWARF CFI、如何调用 personality routine）在两者之间有微小差异。若异常展开路径跨越了两套 unwinder 编译的栈帧，展开器可能遇到它无法正确解释的 CFI 信息，导致展开失败或错误的栈帧恢复，最终 `std::terminate`。

### 8.4 libc 的两种链接方式及其影响

**动态链接 libc**（默认）：进程通过 `DT_NEEDED: libc.so.6` 使用 glibc。NSS（Name Service Switch）、`getaddrinfo`、`getpwnam` 等函数在运行时 `dlopen` `libnss_*.so`（`libnss_dns.so.2`、`libnss_files.so.2` 等）——这是 glibc 的插件架构，允许系统管理员配置名字解析来源（`/etc/nsswitch.conf`）。

**静态链接 libc**（`-static`）：把 libc 的代码直接打包进可执行文件。NSS 函数在运行时仍然尝试 `dlopen` `libnss_*.so`（因为 NSS 是运行时插件），但此时可执行文件是静态的——静态可执行文件调用 `dlopen` 是 glibc 明确不支持的场景（`libc.a` 里的 `dlopen` 是一个存根，只能加载与编译时 libc 版本完全匹配的库）。

结论：`gcc -static` 编译的程序，IP 直接连接没有问题，域名解析会失败（除非目标系统上恰好有与编译时 glibc 版本完全相同的 NSS 模块）。

musl libc 的静态链接方案：musl 把 DNS 解析、用户名查询直接静态实现，不使用插件架构。代价是行为不可配置（不支持 LDAP、NIS 等 NSS 扩展）。

### 8.5 内存分配器的二进制接口

`malloc`/`free` 是通过符号插入替换的——替换分配器（jemalloc、tcmalloc、mimalloc）必须在 glibc 的 `malloc` 之前被加载，让自己的 `malloc`/`free` 符号"赢得"全局命名空间里的解析。

```
进程符号解析顺序（简化）：
1. 可执行文件自身的符号
2. LD_PRELOAD 的库
3. DT_NEEDED 的库（按加载顺序）
4. ld.so 自身
```

替换分配器通常通过 `LD_PRELOAD` 或在链接命令行最前面列出（在 libc 之前）实现插入。

关键约束：**分配器是进程级别的单例**。所有 `malloc` 调用必须经过同一个分配器，所有 `free` 调用必须对 `malloc` 是的地址有效。若因某种原因（编译时绑定、IFUNC、`-Bsymbolic`）部分代码绕过了插入，就会出现"跨分配器释放"——将一个分配器分配的内存传给另一个分配器的 `free`，其行为未定义（通常是立即崩溃或悄悄的堆损坏）。

---

## 第九章：综合——同一对象的多种视图

### 9.1 视图对应表

同一个程序在不同层次下呈现为不同的对象。这些对象不是独立的——它们是同一个数学结构在不同函子下的像：

| 层次 | 对象 | 基本单元 | 组合方式 | 等价关系 |
|------|------|---------|---------|---------|
| 源代码 | 翻译单元集合 | 函数、变量声明 | `#include`、extern 引用 | 语义等价（程序行为相同） |
| 目标文件 | 带重定位的节集合 | 节、符号 | 重定位引用 | COMDAT 等价（相同内容的副本） |
| 静态库 | 目标文件的归档 | 目标文件 | 符号索引 | 按需抽取等价 |
| 共享库/可执行文件 | 带动态符号的 ELF | 段、动态符号 | `DT_NEEDED`、`PLT/GOT` | ABI 等价（布局/调用约定相同） |
| 进程 | 虚拟地址空间 + 状态机 | 内存页、寄存器 | 函数调用、内存读写 | 可观察行为等价 |

### 9.2 工具箱：观察各个层次的接口

```
nm -D --with-symbol-versions lib.so    # 观察动态符号层
nm -C                                   # demangle（还原 C++ mangled name）

readelf -l a.out                        # 观察段（执行视图）
readelf -S a.out                        # 观察节（链接视图）
readelf -r a.out                        # 观察重定位记录
readelf -d a.out                        # 观察 .dynamic（动态链接元数据）
readelf --dyn-syms a.out                # 动态符号表

objdump -d a.out                        # 反汇编（代码 → 机器指令）
objdump -R a.out                        # 运行时重定位（PLT/GOT 条目）

LD_DEBUG=libs,bindings ./a.out 2>log    # 观察 ld.so 的完整运行时决策
LD_DEBUG=all ./a.out 2>log             # 更详细（包括重定位处理过程）

/proc/PID/maps                          # 观察运行时虚拟地址空间
/proc/PID/smaps                         # 更详细（含物理内存统计）

gcc -v                                  # 查看驱动传给链接器的完整参数
ld --verbose                            # 查看默认链接脚本

c++filt _ZN3FooC1Ev                    # demangle 单个符号
patchelf --print-rpath lib.so           # 查看 RPATH/RUNPATH
patchelf --set-rpath '$ORIGIN/../lib'   # 修改 RPATH
```

---

## 结语

格罗滕迪克在《收获与播种》里写道，他最重要的能力不是解决难题，而是找到能让难题消失的语言。

本文试图找到的语言是：**指称世界（静态结构）与操作世界（动态执行）的分离，以及连接它们的自由变量逐步绑定机制。**

在这个语言里：

- ELF 是带自由变量的程序指称语义的编码
- 重定位是自由变量的占位符和求值规则
- 链接是自由变量的代数消除运算
- 加载是指称到操作的本体论跃迁
- ABI 是跨越层次边界的类型系统同态条件
- 动态链接是符号绑定的惰性求值策略
- 运行时库是操作世界必须存在而指称世界没有对应物的基础设施

这些不是需要分别记忆的定义。它们是同一个结构在不同维度上的投影。

理解了这个结构，工具链的每个细节——为什么 `.bss` 不占文件空间、为什么 GOT 必须存在、为什么 soname 有三层命名、为什么 TLS 有四种访问模型、为什么启动序列是现在这个顺序——都变成了从地基自然生长出来的推论。

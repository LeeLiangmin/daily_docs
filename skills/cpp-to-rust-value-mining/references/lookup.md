# 查阅表：C/C++ 形态 ↔ Rust 机制 ↔ 归因 ↔ 精彩度

第 2、3 步随时查。一张表回答三个问题：这个 C 形态对应 Rust 的什么机制、归因几级、值不值得单独讲。

**精彩度倾向的判断口径**：这个机制的使用是不是包含了**团队对自己业务的判断**？包含 = A 倾向；换任何 Rust 项目都会这么写 = B 倾向。表里给的是倾向，最终定级仍按 `selection.md` 的五条标准。

## 目录

- [主表](#主表)
- [高价值对照的判断标准](#高价值对照的判断标准)
- [五组典型代码对照](#五组典型代码对照)
- [工程化层面的对照](#工程化层面的对照)
- [低价值对照：不要选](#低价值对照不要选)

## 主表

| C/C++ 里的形态 | 靠什么维持正确性 | Rust 机制 | 常关联的缺陷类别 | 归因 | 精彩度倾向 |
|---|---|---|---|---|---|
| 手动 `malloc`/`free`、`new`/`delete` | 程序员配对 | 所有权 + `Drop` | use-after-free、double free、泄漏 | L1 | B |
| `goto cleanup` 清理路径 | 每个早退分支都记得跳 | `Drop` + `?` | 错误路径漏清理、fd 泄漏 | L1 | B |
| 返回 `-1`/errno，调用方可忽略 | 调用方记得检查 | `Result` + `#[must_use]` + `?` | 未检查返回值 | L1 | B |
| 可能返回 NULL | 调用方记得判空 | `Option<T>` | 空指针解引用 | L1 | B |
| 裸数组 + 长度参数 | 长度算对 | 切片 `&[T]`（边界检查） | 越界读写、off-by-one | L1 | B |
| 容器扩容后旧指针/迭代器 | 程序员避开 | 借用规则 + 生命周期 | 悬垂引用、迭代器失效 | L1 | B |
| 部分字段未初始化 | 程序员记得填 | 变量必须初始化后使用 | 未初始化读取 | L1 | B |
| 隐式数值转换、signed/unsigned 混用 | 程序员当心 | 无隐式转换，须显式 | 类型混淆、负数 | L1 | B |
| **锁与被保护数据分离 + 注释绑定** | 注释 + 人 | **`Mutex<T>`/`RwLock<T>`（数据在锁里）** | 数据竞争、忘记加锁 | L1 | **A** |
| `pthread_mutex_unlock` 散在各分支 | 每条路径都记得解锁 | `MutexGuard` 的 `Drop` | 忘记解锁、挂死 | L1 | B |
| "只能在 X 线程调用"的约定 | 注释 + review | `Send`/`Sync` 约束 | 跨线程误用 | L1 | B |
| 加锁顺序约定 | 人 | **无对应——Rust 不防死锁** | 死锁 | — | 不写 |
| `#define` 状态常量 + `switch` | 记得改全所有 switch | 枚举 + 穷尽 `match` | 漏分支、状态可回退 | L1 | A（若状态机是核心） |
| `void *ctx` + 函数指针表 | 注册方与调用方约定 | trait 对象 / 泛型 | 类型混淆、crash | L1 | A |
| 宏展开生成多份类型代码 | 宏写对 | 泛型 + trait | 宏调试困难、重复实现不一致 | L2 | A |
| 都是 `int`，语义靠命名区分 | 命名约定 | **newtype** | 参数传错、单位混淆 | L2 | **A** |
| "必须先 init 再 use"、"握手后才能发" | 注释 + 人 | **typestate（类型参数表示状态）** | API 误用 | L2 | **A（最精彩）** |
| 构造后再逐个校验，或不校验 | 调用方自觉 | **私有字段 + 智能构造器** | 非法状态对象流入系统 | L2 | **A** |
| 用 0/NULL 当哨兵值 | 约定 | `NonZeroU32`/`NonNull`（还带布局优化） | 哨兵值被当合法值 | L2 | A |
| 头文件里暴露的函数指针表 | 约定不要乱实现 | sealed trait | 外部错误扩展 | L2 | A |
| `buf` + `len` 两个参数 | 保持一致 | const generics / 类型级长度 | 长度不匹配 | L2 | A |
| 结构体字段全 public | 约定不要乱改 | `pub`/`pub(crate)`/私有 | 不变量被外部破坏 | L2 | A |
| 手写 Makefile/CMake + vendored 依赖 | 人工维护 | Cargo + lockfile | 版本不一致 | L3 | B |
| 声明与定义不一致、宏重定义 | 编译器部分检查 | 模块系统，无头文件 | 链接期错误 | L2 | B |
| 异常安全（C++ 构造中途抛出） | 遵守 RAII 惯例 | 无异常，错误是值 | 状态不一致 | L2 | B |

**关于 `Rc`/`Arc` 循环引用**：Rust **不能**防止这类泄漏。若新实现用了引用计数，"不会泄漏"要加限定。

**关于整数溢出**：debug 下 panic，release 默认回绕。`checked_*`/`saturating_*` 显式表达意图属 L2，别说成 L1。

## 高价值对照的判断标准

一组对照值得进材料，当且仅当能用**一句话**填完：

> 旧实现在这里靠 **____** 维持正确性，新实现靠 **____** 维持正确性。

左边填出来是"程序员记得/注释/约定/人工审查/运行时检查"，右边是"编译器/类型系统"——高价值。两边填出来是同一类东西——不是。

## 五组典型代码对照

**下面是模式示意，不是可以直接贴进材料的素材。** 必须去实际代码里找到对应位置，用真实代码做对照。示意的作用是告诉你该找什么形状的东西。

### 1. 手动清理路径 → RAII 全覆盖

找 `goto cleanup`、`goto err`、每个早退分支都要重复的清理代码。

```c
int process(const char *path) {
    FILE *f = NULL; char *buf = NULL; int ret = -1;
    f = fopen(path, "r");
    if (!f) goto cleanup;
    buf = malloc(SIZE);
    if (!buf) goto cleanup;
    if (read_all(f, buf) < 0) goto cleanup;   // 新增早退分支就要记得走 cleanup
    ret = 0;
cleanup:
    if (buf) free(buf);
    if (f) fclose(f);
    return ret;
}
```

```rust
fn process(path: &Path) -> Result<(), Error> {
    let mut f = File::open(path)?;
    let mut buf = Vec::with_capacity(SIZE);
    f.read_to_end(&mut buf)?;   // 任何早退，f 和 buf 都会被释放
    Ok(())
}
```

**佐证**：统计旧代码里 `goto cleanup` 的次数、历史上有多少 fix commit 是在补漏掉的清理。

### 2. 锁与数据分离 → 数据关进锁里（**最推荐，一眼就懂**）

```c
pthread_mutex_t cache_lock;
struct cache *g_cache;   /* 访问 g_cache 前必须持有 cache_lock */
                         /* 但编译器不知道，谁都能直接读 g_cache */
```

```rust
static CACHE: Mutex<Cache> = Mutex::new(Cache::new());
let mut cache = CACHE.lock().unwrap();  // 不拿锁就拿不到 Cache
```

这组几乎不需要解释，读者一眼就懂且很难反驳。**注意它通常属于"不变量消失"而非"编译器帮着查"**——这个区别值得在材料里点明。

### 3. 注释约定的不变量 → typestate

在旧代码里 grep `/* 必须先调用 init() */`、`/* 调用后本对象失效 */` 这类注释。**每一条都是一个靠人记住的不变量。**

```rust
// 未连接的连接对象根本没有 send 方法
let conn: Connection<Disconnected> = Connection::new();
let conn: Connection<Connected> = conn.connect()?;
conn.send(data)?;
```

这是产出最密集的一条，**优先做**。三种结果都要记：变成类型 = 价值点；仍是注释 = 改进不彻底；变成运行时断言 = 部分改进。

### 4. `void*` + 函数指针 → trait

```c
struct handler { void (*cb)(void *ctx, int ev); void *ctx; };
// ctx 的真实类型只存在于程序员脑子里，转错了编译器不会说什么
```

```rust
trait Handler { fn on_event(&mut self, ev: Event); }
```

**归因提醒**：C++ 模板同样能做到类型安全，旧实现若已用模板，这条降为 L3 或不写。

### 5. 返回码 → Result

```c
int rc = do_something();   // 调用方可以完全忽略 rc，编译器毫无意见
```

```rust
let value = do_something()?;   // 忽略 Result 会触发 must_use 警告
```

**佐证**：统计旧代码里未检查返回值的调用点数量，这个数字往往出人意料地大。
**反向检查**：如果新实现 `unwrap()` 满地都是，这条要打折——顺便统计新代码的 `unwrap`/`expect` 密度，既是诚实，也是给自己找到的改进点。

## 工程化层面的对照

不是代码片段对照，但同样有价值，容易被忽略：

- **依赖管理**：vendored 第三方源码 + 手写 Makefile 片段 vs `Cargo.toml` + lockfile。落到具体问题：升级某个依赖要改几个地方？出过版本不一致的事故吗？
- **构建**：CMake/autotools 的平台分支数量 vs `cargo build`；交叉编译的实际步骤对比。
- **测试**：写一个新测试要改几个文件？有没有 doc test、property test？fuzz 接入成本（`cargo-fuzz` vs 手搭 libFuzzer）。
- **静态检查**：旧实现开了哪些 warning、多少被 suppress、有没有跑 sanitizer 及其接入成本 vs clippy 默认能查出什么。
- **API 文档**：doc comment + 文档测试保证示例不过期 vs 手写文档与代码脱节。

说服力来自**具体数字和具体步骤**：不要写"构建更简单了"，要写"跨平台构建从 N 步变成 1 步""CMake 里的平台分支从 N 处降到 0"。

## 低价值对照：不要选

- 纯语法糖对比（`for` 循环 vs 迭代器链），除非能说明它消除了索引越界的可能
- 行数变少，除非能说清少的是哪一类代码
- "Rust 更现代""写起来更爽"这类主观感受
- **用旧实现里最烂的一段对比新实现里最好的一段**——一旦被识破，整份材料就废了

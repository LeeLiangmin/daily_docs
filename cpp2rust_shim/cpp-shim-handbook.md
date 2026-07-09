# C++ Shim 层处理手册：如何应对原有接口的各种 C++ 特性

本文档面向 Rust FFI 对接遗留 C++ 项目的场景，系统梳理 shim 层（`{project_name}_sys/shim/`）需要处理的 C++ 语言特性和标准库特性，给出每类问题的判定标准、处理策略和最小示例。核心红线不变：

> **跨 FFI 边界的函数签名里，不允许出现任何非 C-ABI-稳定的类型。** C++ 特性只能存在于 shim 的 `.cpp` 实现文件内，`.h` 头文件只暴露 C ABI。

在进入具体特性之前，先约定一条贯穿全文的**统一错误约定**，避免各节各自为政导致调用方心智负担过重：

- 所有可失败的导出函数统一返回状态枚举（如 `FooStatus`，成功为 `0`），真正的输出通过 out 参数传递；只有语义上天然是"可空句柄/可空指针"的构造类函数允许用 `nullptr` 表示失败。
- 线程局部的 `foo_last_error()`（见第 3 节）作为补充的详情通道，不作为主判定依据。
- 各节示例中出现的 `bool` 返回值均可理解为这条约定的简化写法，实际工程建议统一到状态枚举。

---

## 1. STL 容器、字符串与非拥有视图

**问题**：`std::string`、`std::vector`、`std::map`、`std::unordered_map` 等没有跨编译器/跨版本稳定的内存布局。

**策略**：
- 输入方向：shim 用 `(指针, 长度)` 现场构造 STL 对象，构造对象是函数局部变量，随栈自动析构。
- 输出方向：定长小数据用调用者提供缓冲区；变长数据由 C++ 侧 `new`/`strdup` 分配，导出配对 `free` 函数。
- `std::map`/`std::set` 这类有序关联容器，输出时按迭代顺序拍平成两个平行数组（keys/values）或 `struct { key; value; }` 数组。

```cpp
// 输入: const std::vector<int>&
bool foo_process(FooHandle h, const int32_t* ids, size_t ids_len);

// 输出（策略B: C++ 分配 + 配对 free）
struct FooStringArray { char** items; size_t len; };
FooStringArray foo_list_names(FooHandle h);
void foo_free_string_array(FooStringArray arr);
```

**非拥有视图：`std::string_view` / `std::span`**

C++17 的 `std::string_view` 和 C++20 的 `std::span<T>` 本质上就是 `(指针, 长度)`，与 shim 的输入约定天然对应，转换是零成本的。但必须在头文件注释里写死**生命周期约定**：

- 视图不拥有数据。如果原接口接受视图后会**保存**它（而不是当场用完），shim 必须在内部拷贝一份，或在注释里明确"调用方必须保证数据在 XX 之前一直有效"——后者容易在 Rust 侧造成悬垂引用误用，生产环境优先选拷贝。
- 输出方向返回视图（如 `std::string_view getName() const`）时，注释必须写明视图指向的底层数据由哪个对象持有、随哪个 handle 销毁而失效。

```cpp
// C++: void setLabel(std::string_view s);  // 内部会保存
// shim 内部拷贝，调用方无需保证 s 的后续生命周期
bool foo_set_label(FooHandle h, const char* s, size_t len);

// C++: std::string_view name() const;
// 返回的指针指向 h 内部存储，h 销毁后失效，调用方不得 free
bool foo_get_name(FooHandle h, const char** out, size_t* out_len);
```

## 2. `std::optional` / `std::variant` / `std::any` / `std::expected`

**问题**：这类"和类型"容器同样没有稳定 ABI，且语义（有值/无值、当前活跃分支）必须显式表达。

**策略**：
- `std::optional<T>` → `(bool has_value, T value)` 的 out 参数，或指针为 `nullptr` 表示无值（仅当 T 本身是指针/句柄时适用）。
- `std::variant<A, B, C>` → tagged union：`enum` 表示当前类型 + `union`/独立字段。
- `std::any` 一般不建议跨边界暴露；如果必须，退化为 `void*` + 类型 ID + 自定义销毁函数指针，由调用方负责按类型 ID 解释，shim 承担全部类型擦除逻辑。
- C++23 的 `std::expected<T, E>` 本质就是二分支的和类型，直接套用统一错误约定：`E` 映射成状态枚举/错误码返回，`T` 走 out 参数；如果 `E` 携带复杂信息，走第 3 节的 TLS 详情通道。

```cpp
typedef enum { FOO_KIND_INT, FOO_KIND_STRING } FooKind;
typedef struct {
    FooKind kind;
    int32_t as_int;      // kind == FOO_KIND_INT 时有效
    char* as_string;     // kind == FOO_KIND_STRING 时有效，需要配对 free
} FooVariant;
```

## 3. 异常与错误传递（双向）

**问题**：C++ 异常穿越 `extern "C"` 边界是未定义行为；Rust 完全没有异常处理机制去接住它。反过来，Rust 闭包的 panic 穿出 `extern "C"` 函数同样不允许（见本节末尾）。

**策略（C++ → Rust 方向）**：
- shim 每个导出函数体必须 `try { ... } catch (...) {}` 包裹，不允许任何异常逃逸。
- 转换方式二选一：
  1. 返回值本身就是状态（`bool`/指针可空）时，异常 → `false`/`nullptr`。
  2. 需要区分失败原因时，用线程局部错误状态：异常发生时把 `what()` 存入 TLS 缓冲区，导出 `foo_last_error()` 供 Rust 查询。
- 绝不能用"业务上不会抛异常"作为理由省略 try/catch——第三方库升级、边界输入变化都可能引入新的异常路径。

```cpp
static thread_local std::string g_last_error;

bool foo_load(FooHandle h, const char* path, size_t len) {
    try {
        static_cast<Foo*>(h)->load(std::string(path, len));
        return true;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return false;
    } catch (...) {
        g_last_error = "unknown C++ exception";
        return false;
    }
}

const char* foo_last_error() { return g_last_error.c_str(); }
```

Rust 侧对应把返回值映射为 `Result<T, Error>`，`Error` 内部按需调用 `foo_last_error` 取详情。

**非异常错误通道：`std::error_code`**

不是所有 C++ 接口都用异常报错。原接口如果用 `std::error_code`/`std::errc`，映射相对直接：`error_code::value()` 是 `int`，可以直接过边界，但必须**连同 category 一起表达**——同一个数值在不同 category 下含义不同。建议 shim 层把项目内实际出现的 `(category, value)` 组合收敛映射到自己的状态枚举，而不是把裸 `int` 甩给 Rust。

**Rust panic 反向逃逸（Rust → C++ 方向）**

自 Rust 1.81 起，panic 沿栈展开穿出普通 `extern "C"` 函数会直接 abort 整个进程（此前版本是 UB）；Rust 另提供 `extern "C-unwind"` 支持展开互通，但按本手册红线，**不依赖 unwind 互通**，统一在边界处兜底：

- 所有会被 C++ 调用的 Rust 函数（主要是第 8 节的 trampoline），函数体必须用 `std::panic::catch_unwind` 包裹，panic 转换成错误码/默认值返回。
- `catch_unwind` 要求闭包 `UnwindSafe`；捕获了可变状态时用 `AssertUnwindSafe` 显式确认，并保证 panic 后该状态不会以损坏形式被继续使用。

```rust
extern "C" fn trampoline(value: i32, user_data: *mut c_void) {
    let result = std::panic::catch_unwind(|| {
        let closure = unsafe { &*(user_data as *const Box<dyn Fn(i32)>) };
        closure(value);
    });
    if result.is_err() {
        // 记录日志/置错误标志，绝不让 panic 继续展开
    }
}
```

## 4. 对象生命周期：构造/析构、RAII、智能指针、所有权转移

**问题**：C++ 对象的构造/析构、`std::unique_ptr`/`std::shared_ptr` 管理的资源，需要在 Rust 里映射成明确的所有权模型。

**策略**：
- 普通对象：opaque handle + 成对的 `create`/`destroy` 导出函数，Rust safe binding 用 `Drop` 调用 `destroy`。
- `std::unique_ptr<T>` 成员：不直接暴露，shim 内部持有，Rust 侧只感知外层 handle 的生命周期。
- `std::shared_ptr<T>` 语义（需要共享所有权、引用计数）：如果原接口确实依赖共享语义，shim 层可以维护一个 `shared_ptr` 注册表，导出 `foo_retain`/`foo_release` 一对函数模拟引用计数；Rust 侧包一层 `Clone` 递增引用、`Drop` 递减引用。
- 严禁把 C++ `new` 出来的内存交给 Rust 的 `Box`/全局分配器接管，反之亦然——两侧分配器不保证一致，`free`/`delete` 必须发生在分配的同一侧（展开见第 21 节）。

```cpp
typedef struct FooOpaque FooOpaque;
typedef FooOpaque* FooHandle;

FooHandle foo_create(const char* cfg, size_t cfg_len);
void foo_destroy(FooHandle h);          // 对应 unique_ptr<Foo> 的析构

// 模拟 shared_ptr 引用计数
FooHandle foo_retain(FooHandle h);      // 内部 shared_ptr 拷贝, use_count++
void foo_release(FooHandle h);          // shared_ptr 析构, use_count--
```

**移动语义与所有权转移**

原接口如果通过 `std::move` 转移所有权（如 `std::unique_ptr<Item> takeItem()`、`void submit(Job&& job)`），C ABI 里没有"移动"概念，shim 用**显式的所有权转移函数**表达：

- 从 C++ 移出给 Rust：导出 `foo_take_xxx(...) -> XxxHandle`，shim 内部 `std::move`/`release()` 出裸指针，注释明确"调用后原容器/对象不再持有该资源，返回的 handle 由调用方负责 `xxx_destroy`"。
- 从 Rust 移入给 C++：导出 `foo_submit_xxx(FooHandle h, XxxHandle item)`，注释明确"调用成功后 item 的所有权归 h，调用方不得再使用或 destroy 该 handle"。失败路径要写清所有权归属（建议：失败时所有权不转移，仍归调用方）。

```cpp
// C++: std::unique_ptr<Item> Container::takeFirst();
ItemHandle foo_take_first(FooHandle h);   // 返回 nullptr 表示空；非空则调用方负责 item_destroy

// C++: void Queue::submit(std::unique_ptr<Job> job);
// 成功: job 所有权归队列; 失败(返回 false): 所有权仍归调用方
bool foo_submit(FooHandle h, JobHandle job);
```

## 5. 继承与多态（虚函数、抽象类）

**问题**：虚函数表布局同样是编译器相关的 ABI 细节，Rust 无法直接调用虚函数。

**策略**：
- 不跨边界暴露带虚函数的类本身；shim 内部持有具体类型或基类指针，导出的是**按行为拍平的自由函数**，内部完成虚派发。
- 如果 Rust 侧需要"多态调用"的效果（即调用方不知道具体子类），让 shim 提供一个统一的 handle 类型 + 一组操作函数，shim 内部 `dynamic_cast`/虚调用来分发，Rust 只看到统一接口，感知不到继承关系。
- 如果需要 Rust 侧反向实现"C++ 虚函数"（即 C++ 回调 Rust 实现的接口），用第 8 节的 vtable-as-struct 方式模拟。

```cpp
// C++ 侧: class Shape { virtual double area() = 0; }; class Circle : Shape {...};
typedef struct ShapeOpaque* ShapeHandle;

double shape_area(ShapeHandle h) {
    try { return static_cast<Shape*>(h)->area(); } catch (...) { return -1.0; }
}
```

## 6. 模板与泛型

**问题**：C++ 模板在编译期实例化，没有运行时统一符号；`template<typename T> class Container<T>` 本身不能直接导出。

**策略**：
- **不导出模板本身**，只导出项目里实际用到的具体实例化类型（如 `Container<int>`、`Container<std::string>`），每个实例化各自生成一套 shim 函数，函数名带类型后缀区分（如 `container_int_get`、`container_str_get`）。
- 如果模板参数种类很多且都要暴露，评估是否可以在 C++ 侧收窄成一个非模板的"能力接口"（如统一转成 `void*` + 类型标签），避免 shim 爆炸式增长。
- 纯 header-only 模板工具函数（如编译期常量、type traits）一般不需要跨边界暴露，这类东西应在 Manifest 中判定为"无法形成稳定 C ABI contract"而跳过。

```cpp
// C++: template<typename T> class Stack { void push(T); T pop(); };
// 只暴露实际用到的 Stack<int> 和 Stack<std::string>
typedef struct StackIntOpaque* StackIntHandle;
void stack_int_push(StackIntHandle h, int32_t v);
bool stack_int_pop(StackIntHandle h, int32_t* out);

typedef struct StackStrOpaque* StackStrHandle;
void stack_str_push(StackStrHandle h, const char* s, size_t len);
bool stack_str_pop(StackStrHandle h, char** out, size_t* out_len); // 需配对 free
```

## 7. 运算符重载

**问题**：`operator==`、`operator<<`、`operator[]` 等语法糖在 C ABI 里不存在对应概念。

**策略**：直接翻译成具名函数，语义不变：

| C++ | shim 导出 |
|---|---|
| `a == b` | `foo_equals(a, b) -> bool` |
| `a < b` | `foo_less_than(a, b) -> bool` |
| `a[i]` | `foo_get_at(h, i, out) -> bool` |
| `os << obj` | `foo_to_string(h) -> char*`（配 free） |
| `a + b` | `foo_add(a, b) -> FooHandle`（新对象，调用方负责 destroy） |

## 8. 回调函数、`std::function`、Lambda

**问题**：`std::function<R(Args...)>` 是类型擦除的可调用对象，没有 C ABI；Lambda 捕获的上下文更是编译器私有实现。

**策略**：
- C++ 侧接受回调的接口，shim 改成"函数指针 + `void* user_data`"这一 C 语言经典模式。
- Rust 侧把闭包 `Box` 到堆上，转成裸指针传给 `user_data`，同时提供一个 `extern "C" fn` 作为 trampoline，在 trampoline 内部把 `user_data` 转回 Rust 闭包类型并调用。
- 必须明确 trampoline 和 `user_data` 的生命周期：谁负责在最后释放 `Box`，通常是显式的 `foo_unregister_callback` 或对象销毁时一并释放。
- trampoline 内部必须 `catch_unwind` 兜住 panic（见第 3 节），不允许 panic 穿回 C++。
- **回调触发线程**必须在头文件注释里写明：回调可能在 C++ 侧的任意工作线程被调用时，Rust 闭包捕获的所有内容必须是 `Send`（若可能并发触发则还需 `Sync`），safe binding 层用 trait bound 强制，而不是靠文档口头约定。

```cpp
// C++: void setCallback(std::function<void(int)> cb);
// 注意: 回调可能在内部工作线程触发, user_data 指向的内容必须线程安全
typedef void (*FooCallback)(int32_t value, void* user_data);
void foo_set_callback(FooHandle h, FooCallback cb, void* user_data);
```

```rust
extern "C" fn trampoline(value: i32, user_data: *mut c_void) {
    let _ = std::panic::catch_unwind(|| {
        let closure = unsafe { &*(user_data as *const Box<dyn Fn(i32) + Send>) };
        closure(value);
    });
}
// 注册时 Box::into_raw 转出去，注销/析构时 Box::from_raw 收回来释放
```

## 9. 异步：`std::future` / `std::promise` / 协程

**问题**：`std::future<T>` 没有 C ABI，且"等待完成"这一语义需要和 Rust 侧的同步/异步模型对接；C++20 协程（`co_await`/`co_return`）返回的 awaitable 类型更是完全编译器/库私有。

**策略**：二选一，按 Rust 侧调用模式决定：

1. **轮询模式**：shim 内部持有 `std::future`（包在一个异步操作 handle 里），导出 `foo_op_is_ready(OpHandle)` 和 `foo_op_take_result(OpHandle, ...)`。适合 Rust 侧是同步代码或自己有事件循环、愿意主动轮询的场景。注意 `take_result` 语义是一次性的（对应 `future::get()` 只能调一次），重复调用必须返回明确错误而不是 UB。
2. **回调模式**：shim 内部在 future 完成时（如通过 `std::thread` + `future::wait()`，或原接口本身提供 completion callback）触发第 8 节的"函数指针 + user_data"回调。适合对接 Rust 的 async 生态——safe binding 里把回调桥接成 oneshot channel，包装成 `impl Future`。

- C++20 协程接口一般折叠进这套模型：shim 内部 `co_await` 到底（或用库提供的同步等待入口），对外只暴露轮询或回调，不暴露任何协程类型。
- 无论哪种模式，**取消语义**必须显式处理：异步操作 handle 被 destroy 时，未完成的操作是被取消、被 detach 还是阻塞等待完成，必须在注释里写死并在 shim 里实现一致，否则 Rust 侧 `Drop` 的时机会造成难查的挂起或 use-after-free。

```cpp
// C++: std::future<Result> Engine::computeAsync(Input in);
typedef struct FooOpOpaque* FooOpHandle;

FooOpHandle foo_compute_async(FooHandle h, const uint8_t* in, size_t in_len);
bool foo_op_is_ready(FooOpHandle op);
// 只能成功调用一次; 未 ready 时返回 false 且不消耗结果
bool foo_op_take_result(FooOpHandle op, FooResult* out);
// 未完成时销毁 = 请求取消并等待内部线程退出后返回
void foo_op_destroy(FooOpHandle op);
```

## 10. 静态成员、全局状态、单例

**问题**：`static` 成员变量、Meyer's Singleton 等全局状态在多个 Rust 调用点之间共享，容易引入隐式耦合和线程安全问题。

**策略**：
- 尽量避免直接暴露全局状态本身；把"访问全局单例"包装成显式的 `foo_singleton_instance() -> FooHandle` 之类的函数，让 Rust 侧显式感知这是一个共享句柄，而不是误以为每次调用都创建新对象。
- 全局状态如果不是线程安全的，必须在 Manifest/文档里明确标注，shim 层可以加互斥锁做保护，或者在 Rust safe binding 里用 `Mutex`/单线程限定类型包装，阻止误用。
- 如果全局状态只是用来初始化一次（如某些库要求的 `init()`/`shutdown()`），导出对应函数并在文档里说明调用顺序要求（如"必须在其他调用前调用一次，且只能调用一次"）。

```cpp
FooHandle foo_singleton_instance();  // 内部返回 Singleton::instance() 的指针，不创建新对象，不需要 destroy
bool foo_global_init();              // 进程级初始化，幂等或显式要求只调用一次
void foo_global_shutdown();
```

## 11. 引用参数 vs 指针，`const` 语义

**问题**：C++ 的 `T&`、`const T&` 没有直接的 C 对应，且引用不能为空这一保证在 C ABI 里也不存在。

**策略**：
- `const T&` 输入参数 → `const T*`，shim 内部解引用前判空；`T&` 输出参数（用作返回值的替代）→ `T* out`，同样判空。
- 保留原接口的 `const` 语义到注释里，提醒 Rust 侧对应用 `&` 而不是 `&mut`。
- 空指针语义必须在头文件注释里写清楚：是"未定义行为需要调用方保证非空"，还是"shim 会做判空返回错误码"。生产环境的 shim 建议一律做判空防御，即使原 C++ 接口用引用隐含了非空假设。

```cpp
// C++: void update(const Config& cfg, Result& out);
bool foo_update(FooHandle h, const FooConfig* cfg, FooResult* out); // cfg/out 均判空
```

## 12. 枚举：`enum class` 与 unscoped `enum`

**问题**：`enum class` 不能隐式转 `int`，且不同枚举类型即使值相同也不能互转，这本身不是 ABI 问题，但需要在 shim/bindgen 里显式对齐数值。另外，**不带固定底层类型的 unscoped `enum`，其底层类型（进而 `sizeof`）是实现定义的**——同一个枚举在不同编译器下大小可能不同，这才是真正的 ABI 隐患。

**策略**：
- shim 头文件里用普通 C `enum` 或 `int32_t` 常量重新声明一份，数值和顺序必须和 C++ 侧 `enum class` 保持一致，建议用 `static_assert` 在 `.cpp` 里做编译期校验，防止两边定义漂移。
- 原 C++ 侧枚举如果没有显式底层类型（`enum Color { ... }` 而非 `enum Color : int32_t { ... }`），跨边界前先在 C++ 侧补上 `: int32_t`，或在 shim 边界一律以 `int32_t` 传递，绝不在签名里直接使用大小不确定的枚举类型。
- bindgen 可以直接生成对应的 Rust `enum` 或常量，safe binding 层再包一层 `TryFrom<i32>` 做校验，拒绝非法数值。

```cpp
// C++: enum class Status : int32_t { Ok = 0, NotFound = 1, Invalid = 2 };
typedef enum { FOO_STATUS_OK = 0, FOO_STATUS_NOT_FOUND = 1, FOO_STATUS_INVALID = 2 } FooStatus;

static_assert(static_cast<int32_t>(Status::Ok) == FOO_STATUS_OK, "enum drift");
static_assert(static_cast<int32_t>(Status::NotFound) == FOO_STATUS_NOT_FOUND, "enum drift");
static_assert(sizeof(FooStatus) == sizeof(int32_t), "enum size drift");
```

## 13. 函数重载、命名空间、符号可见性与调用约定

**问题**：C ABI 不支持重载（所有导出符号名必须唯一），命名空间也不存在于 C 符号表里（未加 `extern "C"` 时会被 name mangling，但 mangled 名字不稳定）。此外，符号能不能被链接器看见、以什么调用约定被调用，也都属于边界契约的一部分。

**策略**：
- 每个重载版本改成独立的具名函数，按参数区别加后缀，如 `foo_parse_from_string` / `foo_parse_from_bytes`。
- 命名空间路径拍平进符号前缀，如 `myproj::parser::Json` → `myproj_parser_json_*`，避免跨模块符号冲突，这也是本 skill 里"导出符号统一使用 `{target_stem}_` 前缀"的原因。
- 所有导出函数必须包在 `extern "C" { ... }` 里，关闭 C++ name mangling，否则 bindgen/链接器拿到的符号名不可预测。

**符号可见性（共享库场景）**：
- GCC/Clang 建议全局开 `-fvisibility=hidden`，需要导出的函数显式标 `__attribute__((visibility("default")))`；Windows 上对应 `__declspec(dllexport)`（使用方为 `dllimport`）。惯例是定义一个统一的导出宏：

```cpp
#if defined(_WIN32)
  #define FOO_API __declspec(dllexport)
#else
  #define FOO_API __attribute__((visibility("default")))
#endif

extern "C" {
FOO_API FooHandle foo_create(const char* cfg, size_t cfg_len);
}
```

- 静态库场景可见性问题不突出，但导出宏留空定义即可，保持头文件统一。

**调用约定**：
- x64（Windows 与 SysV）各自只有一种 C 调用约定，一般无需操心；**32 位 x86 Windows** 上 `__cdecl`/`__stdcall`/`__fastcall` 并存，`extern "C"` 只管符号名不管调用约定。如果目标平台包含 win32，导出函数和函数指针类型必须显式统一（通常统一 `__cdecl`，与 Rust 的 `extern "C"` 对应），并写进导出宏。

## 14. 字符串编码：`wchar_t`、`char16_t`、本地编码、`std::filesystem::path`

**问题**：`std::wstring`/`wchar_t` 在不同平台宽度不同（Windows 上 16 位，Linux/macOS 上通常 32 位），不能假设它和 Rust 的 `String`（UTF-8）直接兼容。

**策略**：
- 统一在 shim 层做编码转换，对外只暴露 UTF-8 的 `(const char*, size_t)`。
- Windows 下如果原接口本身要求 `wchar_t`（如调用 Win32 API），shim 内部用 `MultiByteToWideChar`/`WideCharToMultiByte`（或等价的 ICU/`std::codecvt` 替代方案，注意 `codecvt` 在新标准里已弃用）完成 UTF-8 ↔ UTF-16 转换，边界之外统一是 UTF-8。
- 非 UTF-8 的本地编码（如 GBK）遗留数据，同样在 shim 内转换成 UTF-8 再传给 Rust，不要把编码问题甩给调用方。

**`std::filesystem::path`**：本质是字符串，但其 native 表示是平台相关的（Windows 上 `wchar_t` 序列，POSIX 上 `char` 序列），且 Windows 路径并不保证是合法 UTF-16、POSIX 路径不保证是合法 UTF-8。策略：
- 常规场景：边界统一 UTF-8，shim 内部用 `std::filesystem::u8path`/`path::u8string`（或 C++20 的 `char8_t` 系列接口）转换。
- 如果项目确实需要处理"非合法编码的路径"（如遍历任意文件系统），退化为原始字节序列 `(const uint8_t*, size_t)` 传递，并在 Rust 侧用 `OsString`/`PathBuf` 的平台特定构造接住，注释写明"内容是平台 native 字节，不保证 UTF-8"。

## 15. 数组/矩阵/固定大小缓冲区

**问题**：`std::array<T, N>`、C 风格定长数组、多维数组，布局本身是稳定的（和 `T[N]` 一致），但语义（行主序/列主序、是否可变长）需要显式约定。

**策略**：`std::array<T, N>` 可以直接以 `T*` + 编译期已知的 `N` 传递，不需要额外转换，只需在头文件注释里写明长度约定；真正需要处理的是外层包裹它的容器（如 `std::vector<std::array<float, 3>>`），这时按第 1 节的思路拍平成 `(const float* data, size_t count)`，并注明每个逻辑元素占 3 个 float。

## 16. POD 结构体按值传递与内存布局

**问题**：并非所有 `struct` 都能按值跨 `extern "C"` 边界。带非平凡拷贝/移动构造函数或析构函数的类型按值传递时，C++ ABI 会引入隐藏的构造/析构调用甚至改为隐式传指针，C 侧完全无法对应——这是 UB。此外，即使是纯数据结构体，padding、对齐、位域布局也可能两侧不一致。

**判定标准**：只有同时满足 **trivially-copyable** 且 **standard-layout** 的类型（即传统意义上的 POD）才允许按值出现在边界签名或边界结构体字段里。C++ 侧用 `static_assert` 强制：

```cpp
static_assert(std::is_trivially_copyable_v<FooConfig>, "must be trivially copyable");
static_assert(std::is_standard_layout_v<FooConfig>, "must be standard layout");
```

**策略**：
- 不满足条件的类型一律退回 opaque handle（第 4 节）。
- 满足条件的 POD，在 shim 头文件里用纯 C 语法**重新声明一份**（字段类型全部用定宽类型，见第 17 节），`.cpp` 内 `static_assert(sizeof(...))` + 逐字段 `static_assert(offsetof(...))` 与原类型比对，防止漂移；Rust 侧对应 `#[repr(C)]`。
- **禁止在边界结构体里使用位域**（bit-field）：位的分配顺序、跨存储单元行为都是实现定义的，GCC/MSVC 布局不同。需要紧凑标志位时改用显式的 `uint32_t flags` + 位掩码常量。
- 谨慎对待 `#pragma pack`/`alignas`：原类型若使用了非默认对齐，shim 声明必须原样复制同等 pack/align 指示，且 Rust 侧要用 `#[repr(C, packed(N))]`/`#[repr(align(N))]` 对齐，并接受 packed 字段取引用受限等代价。默认建议：边界结构体不使用非默认对齐，宁可多几个字节 padding。

```cpp
// shim 头文件（纯 C 声明）
typedef struct {
    int32_t width;
    int32_t height;
    float   scale;
    uint32_t flags;      // 位域改掩码: FOO_FLAG_VISIBLE = 1u << 0, ...
} FooConfig;

// shim .cpp 内校验与 C++ 原类型一致
static_assert(sizeof(FooConfig) == sizeof(cpp::Config), "size drift");
static_assert(offsetof(FooConfig, scale) == offsetof(cpp::Config, scale), "layout drift");
```

## 17. 基础类型宽度与平台差异

**问题**：C/C++ 的裸整型和部分浮点型宽度是平台相关的，签名里直接沿用会造成同一份 shim 在不同平台上 ABI 不一致。

**必须知道的差异**：

| 类型 | 风险 |
|---|---|
| `long` / `unsigned long` | Windows 是 LLP64（32 位），Linux/macOS 是 LP64（64 位）。**边界签名禁止裸 `long`**，shim 内转换成 `int32_t`/`int64_t` |
| `char` | 符号性平台/编译器相关（ARM Linux 上默认 unsigned）。字节数据一律用 `uint8_t`，文本用 `char` 但只承载 UTF-8 |
| `long double` | x86 Linux 是 80 位扩展精度，MSVC 上等同 64 位 `double`，AArch64 Linux 是 128 位。**禁止过边界**，shim 内收窄成 `double` 并评估精度损失 |
| `__int128` / `unsigned __int128` | MSVC 不支持，跨语言 ABI 无保证。禁止过边界，拆成两个 `uint64_t` 或退化为字节数组 |
| `size_t` / `ptrdiff_t` / `intptr_t` | 宽度随平台指针宽度变化，但两侧定义一致（Rust 对应 `usize`/`isize`），**允许使用**，且长度/索引参数推荐用 `size_t` |
| `int` / `int32_t` 等定宽类型 | 在所有主流平台上 `int` 是 32 位，但纪律上仍推荐签名里显式写 `int32_t`，消除歧义 |

**`std::chrono` 时间类型**：`duration`/`time_point` 是模板类型，不能过边界。拍平成整数并**在参数名或注释里写死单位与纪元**，推荐统一 `int64_t` 纳秒（duration）和"自 Unix epoch 起的纳秒数 `int64_t`"（time_point）；shim 内部用 `duration_cast` 转换。不要用 `double` 秒数表示时间——精度问题会在长时间戳上爆发。

```cpp
// C++: void setTimeout(std::chrono::milliseconds ms);
void foo_set_timeout_ns(FooHandle h, int64_t timeout_ns);  // 单位: 纳秒
```

## 18. 多线程、线程局部状态与同步原语

**问题**：C++ 侧可能假设某些调用发生在特定线程（如 UI 线程），或使用 `thread_local` 存储上下文，Rust 侧的异步/多线程调用模式如果不匹配会导致数据错乱或崩溃。

**策略**：
- 明确每个导出函数的线程安全等级：无状态纯函数、需要串行调用的实例方法、要求固定线程调用的方法，分别在头文件注释和 Manifest Reason 里标注。
- 如果原实现依赖 `thread_local`，shim 不应该悄悄掩盖这一点，而是要么在文档里明确"必须在同一 OS 线程调用"，要么在 Rust safe binding 里用非 `Send`/非 `Sync` 的类型标记阻止跨线程误用。
- 需要跨线程调用但原实现不是线程安全的场景，shim 层可以加锁，但要评估锁粒度是否会引入死锁或严重降低并发度，必要时把"加锁"这个决策留给 Rust 侧的 safe binding（比如用 `Mutex<Handle>` 包装）而不是悄悄在 C++ 侧全局加锁。

**同步原语红线**：
- `std::atomic<T>` **不得按值过边界**：其布局、是否 lock-free 都没有跨实现保证（非 lock-free 的 atomic 内部可能藏一把锁）。如果原接口暴露原子变量，shim 改成读/写函数（内部带合适的 memory order），或整体收进 handle 里。
- `std::mutex`/`std::condition_variable` 等同步原语不可拷贝不可移动、内部结构平台私有，**绝不出现在边界签名或边界结构体里**。跨边界的同步需求一律通过导出函数（`foo_lock`/`foo_unlock`，或更好的：把临界区整个封装在一个导出函数内部）表达。

## 19. 宏定义与编译期常量

**问题**：`#define MAX_SIZE 128` 这类宏在预处理阶段就展开了，bindgen 默认不一定能正确识别所有宏（尤其是复杂表达式宏），也无法自动生成 Rust 常量。

**策略**：
- 简单的字面量宏，bindgen 通常能直接转成 Rust 常量，确认生成结果符合预期即可。
- 复杂的函数式宏或依赖其他宏展开的常量，建议在 shim 头文件里用 `static const` 或 `constexpr`（C ABI 友好的具名常量）重新声明一份，保证 bindgen 稳定识别，同时避免宏展开语义在 Rust 里丢失。

```cpp
// 原始: #define FOO_MAX_RETRY (3 * 2)
static const int32_t FOO_MAX_RETRY = 6;  // shim 头文件里显式声明，便于 bindgen 识别
```

## 20. Pimpl 惯用法与不完整类型

**问题**：很多 C++ 类本身已经用 pimpl（pointer to implementation）隐藏了实现细节，这和 opaque handle 的思路是一致的，反而是 shim 层最容易对接的情况。

**策略**：如果原类已经是 pimpl 设计，shim 可以直接把 pimpl 指针本身当成 opaque handle 复用，不需要额外包一层；如果原类没有 pimpl（成员直接摊在类定义里，包含 STL 成员），则由 shim 承担"人工 pimpl"的角色——对外只给不完整类型的指针，内部 `.cpp` 里转型成完整类型访问。

## 21. C++ 运行时、CRT 与分配器一致性

**问题**：即使每个签名都是完美的 C ABI，如果 shim（及其背后的 C++ 库）和最终链接产物在**运行时库层面**不一致，仍会出现最难排查的一类崩溃：堆损坏、静默的 ODR 冲突、跨模块 STL 对象布局错位。

**必须遵守的约束**：
- **谁分配谁释放**是铁律（第 4 节已提）：跨模块/跨语言的 `malloc`/`free`、`new`/`delete` 配对必须发生在同一侧，导出配对 free 函数就是这条铁律的落地形式。
- **Windows CRT 一致性**：所有参与链接的 C++ 目标必须使用同一 CRT 变体（`/MD` vs `/MT`，debug vs release）。debug CRT（`/MDd`）与 release CRT 混链、或不同版本 MSVC 运行时混链，堆句柄不同，跨界 free 直接堆损坏。Rust 侧默认链 release CRT，因此 C++ 侧 debug 构建对接 Rust 时要特别小心。
- **标准库实现一致性**：Linux/macOS 上 libstdc++ 与 libc++ ABI 互不兼容，整条链路（原 C++ 库、shim、其他 C++ 依赖）必须统一用同一个标准库实现，用 `ldd`/`otool -L` 校验没有混入两个。
- **STL debug 模式**：MSVC 的 `_ITERATOR_DEBUG_LEVEL`、libstdc++ 的 `_GLIBCXX_DEBUG` 会**改变 STL 容器的内存布局**。同一进程内不同编译单元该配置不一致，就是静默的 ODR 违规——这也是"STL 类型绝不过边界、shim 内部也要和原库同配置编译"的又一重理由。构建系统里应把这类宏定义收敛到单一出处。
- **静态 vs 动态链接 C++ 运行时**：多个模块各自静态链接 C++ 运行时再互相传递 C++ 对象是危险的（各自一份运行时状态）；本手册的架构下由于边界只有 C ABI、C++ 对象不跨模块，风险已大幅降低，但仍建议整个 C++ 侧（原库 + shim）编成**一个**链接单元，避免 C++ 对象在两个 C++ 模块之间流动。

## 22. ABI 稳定性的持续校验

无论用了以上哪种策略，shim 交付后都建议保留以下几类校验，防止未来 C++ 侧代码演进悄悄破坏约定：

| 校验点 | 方式 |
|---|---|
| enum 数值/大小漂移 | `.cpp` 内 `static_assert` 比对 C++ 原始枚举值和 shim 导出枚举值，以及 `sizeof` |
| 结构体字段对齐 | 对必须暴露字段布局的 POD 类型，`static_assert(sizeof/offsetof(...))` 校验和原始类型一致，外加 `is_trivially_copyable`/`is_standard_layout` 断言 |
| 符号可见性 | 导出函数全部 `extern "C"` + 统一导出宏，链接后用 `nm`/`dumpbin` 校验符号未被 mangling、且预期之外的符号未泄漏 |
| 异常泄漏 | 每个导出函数体走查确认有 `try/catch` 包裹，建议 CI 里静态检查规则强制 |
| panic 泄漏 | 每个被 C++ 调用的 Rust `extern "C" fn`（trampoline）走查确认有 `catch_unwind` 包裹 |
| 运行时一致性 | CI 里校验链接产物的 CRT/标准库依赖（`ldd`/`otool -L`/`dumpbin /dependents`），发现混链即失败 |
| ABI 版本常量 | 头文件导出 `FOO_ABI_VERSION` 整数常量 + `foo_abi_version()` 运行时函数，任何破坏性契约变更时递增；Rust 侧初始化时比对编译期常量与运行时返回值，不一致直接 fail-fast，防止新旧库静默错位 |
| smoke test | 每个 shim 函数至少有一条 Rust 侧 smoke test 覆盖成功路径和一条错误路径 |

```cpp
#define FOO_ABI_VERSION 3
FOO_API int32_t foo_abi_version(void);   // .cpp 里 return FOO_ABI_VERSION;
```

---

## 总结：一张判断表

| C++ 特性 | 能否直接过边界 | shim 处理方式 |
|---|---|---|
| STL 容器/字符串 | 否 | 指针+长度转换，或分配+配对 free |
| string_view/span | 否（但语义对应） | 转 (指针, 长度)，注释写死生命周期约定 |
| optional/variant/expected | 否 | out 参数 + bool，或 tagged union；expected 走统一错误约定 |
| 异常 | 否 | try/catch 转错误码 + TLS 错误信息 |
| Rust panic（反向） | 否 | trampoline 内 catch_unwind 兜底 |
| 对象生命周期/智能指针 | 否 | opaque handle + create/destroy(/retain/release) |
| 移动语义/所有权转移 | 否 | 显式 take/submit 函数，注释写死所有权归属 |
| 虚函数/继承 | 否 | 拍平成自由函数，内部虚派发 |
| 模板 | 否 | 只导出具体实例化，不导出模板本身 |
| 运算符重载 | 否 | 翻译成具名函数 |
| 回调/std::function/lambda | 否 | 函数指针 + user_data + trampoline（含 panic 兜底、线程标注） |
| future/promise/协程 | 否 | 异步操作 handle + 轮询或回调，取消语义显式化 |
| 全局状态/单例 | 部分 | 显式访问函数，标注线程安全性 |
| 引用参数 | 否 | 转指针，显式判空语义 |
| enum class / unscoped enum | 部分 | 重新声明 + static_assert 校验数值与大小，底层类型固定为定宽 |
| 重载/命名空间 | 否 | 具名后缀函数 + 符号前缀拍平 + 统一导出宏 |
| wchar_t/本地编码/fs::path | 否 | shim 内转换，边界外统一 UTF-8（特殊场景退化为原始字节） |
| std::array/定长数组 | 是（布局稳定） | 直接传指针+编译期长度，仅需注释语义 |
| POD 结构体按值 | 部分 | 仅 trivially-copyable + standard-layout 允许；重新声明 + sizeof/offsetof 校验；禁位域 |
| 裸 long / long double / __int128 | 否 | 换定宽类型；long double 收窄 double；__int128 拆两个 u64 |
| chrono 时间类型 | 否 | 拍平 int64_t + 写死单位与纪元 |
| atomic/mutex | 否 | 读写函数封装/收进 handle，绝不按值暴露 |
| 宏 | 部分 | 简单字面量可直接 bindgen，复杂宏改具名常量 |
| Pimpl | 是（已隐藏实现） | 直接复用为 opaque handle |

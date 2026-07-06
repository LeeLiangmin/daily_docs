# C++ Shim 层处理手册:如何应对原有接口的各种 C++ 特性

本文档面向 Rust FFI 对接遗留 C++ 项目的场景,系统梳理 shim 层(`{project_name}_sys/shim/`)需要处理的 C++ 语言特性和标准库特性,给出每类问题的判定标准、处理策略和最小示例。核心红线不变:

> **跨 FFI 边界的函数签名里,不允许出现任何非 C-ABI-稳定的类型。** C++ 特性只能存在于 shim 的 `.cpp` 实现文件内,`.h` 头文件只暴露 C ABI。

---

## 1. STL 容器与字符串

**问题**:`std::string`、`std::vector`、`std::map`、`std::unordered_map` 等没有跨编译器/跨版本稳定的内存布局。

**策略**:
- 输入方向:shim 用 `(指针, 长度)` 现场构造 STL 对象,构造对象是函数局部变量,随栈自动析构。
- 输出方向:定长小数据用调用者提供缓冲区;变长数据由 C++ 侧 `new`/`strdup` 分配,导出配对 `free` 函数。
- `std::map`/`std::set` 这类有序关联容器,输出时按迭代顺序拍平成两个平行数组(keys/values)或 `struct { key; value; }` 数组。

```cpp
// 输入: const std::vector<int>&
bool foo_process(FooHandle h, const int32_t* ids, size_t ids_len);

// 输出(策略B: C++ 分配 + 配对 free)
struct FooStringArray { char** items; size_t len; };
FooStringArray foo_list_names(FooHandle h);
void foo_free_string_array(FooStringArray arr);
```

## 2. `std::optional` / `std::variant` / `std::any`

**问题**:这类"和类型"容器同样没有稳定 ABI,且语义(有值/无值、当前活跃分支)必须显式表达。

**策略**:
- `std::optional<T>` → `(bool has_value, T value)` 的 out 参数,或指针为 `nullptr` 表示无值(仅当 T 本身是指针/句柄时适用)。
- `std::variant<A, B, C>` → tagged union:`enum` 表示当前类型 + `union`/独立字段。
- `std::any` 一般不建议跨边界暴露;如果必须,退化为 `void*` + 类型 ID + 自定义销毁函数指针,由调用方负责按类型 ID 解释,shim 承担全部类型擦除逻辑。

```cpp
typedef enum { FOO_KIND_INT, FOO_KIND_STRING } FooKind;
typedef struct {
    FooKind kind;
    int32_t as_int;      // kind == FOO_KIND_INT 时有效
    char* as_string;     // kind == FOO_KIND_STRING 时有效,需要配对 free
} FooVariant;
```

## 3. 异常

**问题**:C++ 异常穿越 `extern "C"` 边界是未定义行为;Rust 完全没有异常处理机制去接住它。

**策略**:
- shim 每个导出函数体必须 `try { ... } catch (...) {}` 包裹,不允许任何异常逃逸。
- 转换方式二选一:
  1. 返回值本身就是状态(`bool`/指针可空)时,异常 → `false`/`nullptr`。
  2. 需要区分失败原因时,用线程局部错误状态:异常发生时把 `what()` 存入 TLS 缓冲区,导出 `foo_last_error()` 供 Rust 查询。
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

Rust 侧对应把返回值映射为 `Result<T, Error>`,`Error` 内部按需调用 `foo_last_error` 取详情。

## 4. 对象生命周期:构造/析构、RAII、智能指针

**问题**:C++ 对象的构造/析构、`std::unique_ptr`/`std::shared_ptr` 管理的资源,需要在 Rust 里映射成明确的所有权模型。

**策略**:
- 普通对象:opaque handle + 成对的 `create`/`destroy` 导出函数,Rust safe binding 用 `Drop` 调用 `destroy`。
- `std::unique_ptr<T>` 成员:不直接暴露,shim 内部持有,Rust 侧只感知外层 handle 的生命周期。
- `std::shared_ptr<T>` 语义(需要共享所有权、引用计数)：如果原接口确实依赖共享语义,shim 层可以维护一个 `shared_ptr` 注册表,导出 `foo_retain`/`foo_release` 一对函数模拟引用计数;Rust 侧包一层 `Clone` 递增引用、`Drop` 递减引用。
- 严禁把 C++ `new` 出来的内存交给 Rust 的 `Box`/全局分配器接管,反之亦然——两侧分配器不保证一致,`free`/`delete` 必须发生在分配的同一侧。

```cpp
typedef struct FooOpaque FooOpaque;
typedef FooOpaque* FooHandle;

FooHandle foo_create(const char* cfg, size_t cfg_len);
void foo_destroy(FooHandle h);          // 对应 unique_ptr<Foo> 的析构

// 模拟 shared_ptr 引用计数
FooHandle foo_retain(FooHandle h);      // 内部 shared_ptr 拷贝, use_count++
void foo_release(FooHandle h);          // shared_ptr 析构, use_count--
```

## 5. 继承与多态(虚函数、抽象类)

**问题**:虚函数表布局同样是编译器相关的 ABI 细节,Rust 无法直接调用虚函数。

**策略**:
- 不跨边界暴露带虚函数的类本身;shim 内部持有具体类型或基类指针,导出的是**按行为拍平的自由函数**,内部完成虚派发。
- 如果 Rust 侧需要"多态调用"的效果(即调用方不知道具体子类),让 shim 提供一个统一的 handle 类型 + 一组操作函数,shim 内部 `dynamic_cast`/虚调用来分发,Rust 只看到统一接口,感知不到继承关系。
- 如果需要 Rust 侧反向实现"C++ 虚函数"(即 C++ 回调 Rust 实现的接口),用第 8 节的 vtable-as-struct 方式模拟。

```cpp
// C++ 侧: class Shape { virtual double area() = 0; }; class Circle : Shape {...};
typedef struct ShapeOpaque* ShapeHandle;

double shape_area(ShapeHandle h) {
    try { return static_cast<Shape*>(h)->area(); } catch (...) { return -1.0; }
}
```

## 6. 模板与泛型

**问题**:C++ 模板在编译期实例化,没有运行时统一符号;`template<typename T> class Container<T>` 本身不能直接导出。

**策略**:
- **不导出模板本身**,只导出项目里实际用到的具体实例化类型(如 `Container<int>`、`Container<std::string>`),每个实例化各自生成一套 shim 函数,函数名带类型后缀区分(如 `container_int_get`、`container_str_get`)。
- 如果模板参数种类很多且都要暴露,评估是否可以在 C++ 侧收窄成一个非模板的"能力接口"(如统一转成 `void*` + 类型标签),避免 shim 爆炸式增长。
- 纯 header-only 模板工具函数(如编译期常量、type traits)一般不需要跨边界暴露,这类东西应在 Manifest 中判定为"无法形成稳定 C ABI contract"而跳过。

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

**问题**:`operator==`、`operator<<`、`operator[]` 等语法糖在 C ABI 里不存在对应概念。

**策略**:直接翻译成具名函数,语义不变:

| C++ | shim 导出 |
|---|---|
| `a == b` | `foo_equals(a, b) -> bool` |
| `a < b` | `foo_less_than(a, b) -> bool` |
| `a[i]` | `foo_get_at(h, i, out) -> bool` |
| `os << obj` | `foo_to_string(h) -> char*`(配 free) |
| `a + b` | `foo_add(a, b) -> FooHandle`(新对象,调用方负责 destroy) |

## 8. 回调函数、`std::function`、Lambda

**问题**:`std::function<R(Args...)>` 是类型擦除的可调用对象,没有 C ABI;Lambda 捕获的上下文更是编译器私有实现。

**策略**:
- C++ 侧接受回调的接口,shim 改成"函数指针 + `void* user_data`"这一 C 语言经典模式。
- Rust 侧把闭包 `Box` 到堆上,转成裸指针传给 `user_data`,同时提供一个 `extern "C" fn` 作为 trampoline,在 trampoline 内部把 `user_data` 转回 Rust 闭包类型并调用。
- 必须明确 trampoline 和 `user_data` 的生命周期:谁负责在最后释放 `Box`,通常是显式的 `foo_unregister_callback` 或对象销毁时一并释放。

```cpp
// C++: void setCallback(std::function<void(int)> cb);
typedef void (*FooCallback)(int32_t value, void* user_data);
void foo_set_callback(FooHandle h, FooCallback cb, void* user_data);
```

```rust
extern "C" fn trampoline(value: i32, user_data: *mut c_void) {
    let closure = unsafe { &*(user_data as *const Box<dyn Fn(i32)>) };
    closure(value);
}
// 注册时 Box::into_raw 转出去,注销/析构时 Box::from_raw 收回来释放
```

## 9. 静态成员、全局状态、单例

**问题**:`static` 成员变量、Meyer's Singleton 等全局状态在多个 Rust 调用点之间共享,容易引入隐式耦合和线程安全问题。

**策略**:
- 尽量避免直接暴露全局状态本身;把"访问全局单例"包装成显式的 `foo_singleton_instance() -> FooHandle` 之类的函数,让 Rust 侧显式感知这是一个共享句柄,而不是误以为每次调用都创建新对象。
- 全局状态如果不是线程安全的,必须在 Manifest/文档里明确标注,shim 层可以加互斥锁做保护,或者在 Rust safe binding 里用 `Mutex`/单线程限定类型包装,阻止误用。
- 如果全局状态只是用来初始化一次(如某些库要求的 `init()`/`shutdown()`),导出对应函数并在文档里说明调用顺序要求(如"必须在其他调用前调用一次,且只能调用一次")。

```cpp
FooHandle foo_singleton_instance();  // 内部返回 Singleton::instance() 的指针,不创建新对象,不需要 destroy
bool foo_global_init();              // 进程级初始化,幂等或显式要求只调用一次
void foo_global_shutdown();
```

## 10. 引用参数 vs 指针,`const` 语义

**问题**:C++ 的 `T&`、`const T&` 没有直接的 C 对应,且引用不能为空这一保证在 C ABI 里也不存在。

**策略**:
- `const T&` 输入参数 → `const T*`,shim 内部解引用前判空;`T&` 输出参数(用作返回值的替代)→ `T* out`,同样判空。
- 保留原接口的 `const` 语义到注释里,提醒 Rust 侧对应用 `&` 而不是 `&mut`。
- 空指针语义必须在头文件注释里写清楚:是"未定义行为需要调用方保证非空",还是"shim 会做判空返回错误码"。生产环境的 shim 建议一律做判空防御,即使原 C++ 接口用引用隐含了非空假设。

```cpp
// C++: void update(const Config& cfg, Result& out);
bool foo_update(FooHandle h, const FooConfig* cfg, FooResult* out); // cfg/out 均判空
```

## 11. `enum class`(强类型枚举)

**问题**:`enum class` 不能隐式转 `int`,且不同枚举类型即使值相同也不能互转,这本身不是 ABI 问题,但需要在 shim/bindgen 里显式对齐数值。

**策略**:
- shim 头文件里用普通 C `enum` 或 `int32_t` 常量重新声明一份,数值和顺序必须和 C++ 侧 `enum class` 保持一致,建议用 `static_assert` 在 `.cpp` 里做编译期校验,防止两边定义漂移。
- bindgen 可以直接生成对应的 Rust `enum` 或常量,safe binding 层再包一层 `TryFrom<i32>` 做校验,拒绝非法数值。

```cpp
// C++: enum class Status : int32_t { Ok = 0, NotFound = 1, Invalid = 2 };
typedef enum { FOO_STATUS_OK = 0, FOO_STATUS_NOT_FOUND = 1, FOO_STATUS_INVALID = 2 } FooStatus;

static_assert(static_cast<int32_t>(Status::Ok) == FOO_STATUS_OK, "enum drift");
static_assert(static_cast<int32_t>(Status::NotFound) == FOO_STATUS_NOT_FOUND, "enum drift");
```

## 12. 函数重载与命名空间

**问题**:C ABI 不支持重载(所有导出符号名必须唯一),命名空间也不存在于 C 符号表里(未加 `extern "C"` 时会被 name mangling,但 mangled 名字不稳定)。

**策略**:
- 每个重载版本改成独立的具名函数,按参数区别加后缀,如 `foo_parse_from_string` / `foo_parse_from_bytes`。
- 命名空间路径拍平进符号前缀,如 `myproj::parser::Json` → `myproj_parser_json_*`,避免跨模块符号冲突,这也是本 skill 里"导出符号统一使用 `{target_stem}_` 前缀"的原因。
- 所有导出函数必须包在 `extern "C" { ... }` 里,关闭 C++ name mangling,否则 bindgen/链接器拿到的符号名不可预测。

## 13. 字符串编码:`wchar_t`、`char16_t`、本地编码

**问题**:`std::wstring`/`wchar_t` 在不同平台宽度不同(Windows 上 16 位,Linux/macOS 上通常 32 位),不能假设它和 Rust 的 `String`(UTF-8)直接兼容。

**策略**:
- 统一在 shim 层做编码转换,对外只暴露 UTF-8 的 `(const char*, size_t)`。
- Windows 下如果原接口本身要求 `wchar_t`(如调用 Win32 API),shim 内部用 `MultiByteToWideChar`/`WideCharToMultiByte`(或等价的 ICU/`std::codecvt` 替代方案,注意 `codecvt` 在新标准里已弃用)完成 UTF-8 ↔ UTF-16 转换,边界之外统一是 UTF-8。
- 非 UTF-8 的本地编码(如 GBK)遗留数据,同样在 shim 内转换成 UTF-8 再传给 Rust,不要把编码问题甩给调用方。

## 14. 数组/矩阵/固定大小缓冲区

**问题**:`std::array<T, N>`、C 风格定长数组、多维数组,布局本身是稳定的(和 `T[N]` 一致),但语义(行主序/列主序、是否可变长)需要显式约定。

**策略**:`std::array<T, N>` 可以直接以 `T*` + 编译期已知的 `N` 传递,不需要额外转换,只需在头文件注释里写明长度约定;真正需要处理的是外层包裹它的容器(如 `std::vector<std::array<float, 3>>`),这时按第 1 节的思路拍平成 `(const float* data, size_t count)`,并注明每个逻辑元素占 3 个 float。

## 15. 多线程与线程局部状态

**问题**:C++ 侧可能假设某些调用发生在特定线程(如 UI 线程),或使用 `thread_local` 存储上下文,Rust 侧的异步/多线程调用模式如果不匹配会导致数据错乱或崩溃。

**策略**:
- 明确每个导出函数的线程安全等级:无状态纯函数、需要串行调用的实例方法、要求固定线程调用的方法,分别在头文件注释和 Manifest Reason 里标注。
- 如果原实现依赖 `thread_local`,shim 不应该悄悄掩盖这一点,而是要么在文档里明确"必须在同一 OS 线程调用",要么在 Rust safe binding 里用非 `Send`/非 `Sync` 的类型标记阻止跨线程误用。
- 需要跨线程调用但原实现不是线程安全的场景,shim 层可以加锁,但要评估锁粒度是否会引入死锁或严重降低并发度,必要时把"加锁"这个决策留给 Rust 侧的 safe binding(比如用 `Mutex<Handle>` 包装)而不是悄悄在 C++ 侧全局加锁。

## 16. 宏定义与编译期常量

**问题**:`#define MAX_SIZE 128` 这类宏在预处理阶段就展开了,bindgen 默认不一定能正确识别所有宏(尤其是复杂表达式宏),也无法自动生成 Rust 常量。

**策略**:
- 简单的字面量宏,bindgen 通常能直接转成 Rust 常量,确认生成结果符合预期即可。
- 复杂的函数式宏或依赖其他宏展开的常量,建议在 shim 头文件里用 `static const` 或 `constexpr`(C ABI 友好的具名常量)重新声明一份,保证 bindgen 稳定识别,同时避免宏展开语义在 Rust 里丢失。

```cpp
// 原始: #define FOO_MAX_RETRY (3 * 2)
static const int32_t FOO_MAX_RETRY = 6;  // shim 头文件里显式声明,便于 bindgen 识别
```

## 17. Pimpl 惯用法与不完整类型

**问题**:很多 C++ 类本身已经用 pimpl(pointer to implementation)隐藏了实现细节,这和 opaque handle 的思路是一致的,反而是 shim 层最容易对接的情况。

**策略**:如果原类已经是 pimpl 设计,shim 可以直接把 pimpl 指针本身当成 opaque handle 复用,不需要额外包一层;如果原类没有 pimpl(成员直接摊在类定义里,包含 STL 成员),则由 shim 承担"人工 pimpl"的角色——对外只给不完整类型的指针,内部 `.cpp` 里转型成完整类型访问。

## 18. ABI 稳定性的持续校验

无论用了以上哪种策略,shim 交付后都建议保留以下几类校验,防止未来 C++ 侧代码演进悄悄破坏约定:

| 校验点 | 方式 |
|---|---|
| enum 数值漂移 | `.cpp` 内 `static_assert` 比对 C++ 原始枚举值和 shim 导出枚举值 |
| 结构体字段对齐 | 对必须暴露字段布局的 POD 类型,`static_assert(sizeof/offsetof(...))` 校验和原始类型一致 |
| 符号可见性 | 导出函数全部 `extern "C"`,链接时用 `nm`/`dumpbin` 校验符号未被 mangling |
| 异常泄漏 | 每个导出函数体走查确认有 `try/catch` 包裹,建议 CI 里静态检查规则强制 |
| smoke test | 每个 shim 函数至少有一条 Rust 侧 smoke test 覆盖成功路径和一条错误路径 |

---

## 总结:一张判断表

| C++ 特性 | 能否直接过边界 | shim 处理方式 |
|---|---|---|
| STL 容器/字符串 | 否 | 指针+长度转换,或分配+配对 free |
| optional/variant | 否 | out 参数 + bool,或 tagged union |
| 异常 | 否 | try/catch 转错误码 + TLS 错误信息 |
| 对象生命周期/智能指针 | 否 | opaque handle + create/destroy(/retain/release) |
| 虚函数/继承 | 否 | 拍平成自由函数,内部虚派发 |
| 模板 | 否 | 只导出具体实例化,不导出模板本身 |
| 运算符重载 | 否 | 翻译成具名函数 |
| 回调/std::function/lambda | 否 | 函数指针 + user_data + trampoline |
| 全局状态/单例 | 部分 | 显式访问函数,标注线程安全性 |
| 引用参数 | 否 | 转指针,显式判空语义 |
| enum class | 部分 | 重新声明 + static_assert 校验数值 |
| 重载/命名空间 | 否 | 具名后缀函数 + 符号前缀拍平 |
| wchar_t/本地编码 | 否 | shim 内转换,边界外统一 UTF-8 |
| std::array/定长数组 | 是(布局稳定) | 直接传指针+编译期长度,仅需注释语义 |
| 宏 | 部分 | 简单字面量可直接 bindgen,复杂宏改具名常量 |
| Pimpl | 是(已隐藏实现) | 直接复用为 opaque handle |

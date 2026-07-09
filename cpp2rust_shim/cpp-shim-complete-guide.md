# C++ Shim 层完整指南：心智模型、实践模式与特性手册

本文档面向为遗留 C++ 项目搭建 Rust FFI 链路的工程实践，回答一个问题：**拿到一个真实的、依赖第三方库的、大量使用 C++ 特性的项目，shim 层（`{project_name}_sys/shim/`）到底该怎么写。**

它由两部分融合而成：前六部分是**按工作流展开的实践手册**（心智模型 → 四种模式 → 横切问题 → 第三方依赖 → 深水区特性 → 落地校验），教你如何上手一个真实接口；两个附录是**特性参考与专题**（模板实例化发现、最小完整示例）。使用建议：第一次接入通读第一到第四部分建立套路，遇到具体的 gnarly 特性时查第五部分和判断表。

核心红线贯穿全文，且只约束一个文件（下文的 L2）：

> **跨 FFI 边界的函数签名里，不允许出现任何非 C-ABI-稳定的类型。** C++ 特性只能存在于 shim 的 `.cpp` 实现文件内，`.h` 头文件只暴露 C ABI。

---

# 第一部分：先建立正确的心智模型

## 1.1 四层结构：谁能看见什么

一切实践决策都源自这张分层图。做任何一个接口前，先在脑子里过一遍每层的可见性规则：

```
┌─────────────────────────────────────────────────────────┐
│ L4  Rust 业务代码                                         │
│     只使用 safe binding 的 Rust 类型(String/Vec/Result)   │
├─────────────────────────────────────────────────────────┤
│ L3  safe binding ({project}_sys/src/**.rs)               │
│     持有 raw binding，负责 Drop/Result/生命周期，          │
│     对外只暴露 safe Rust API                              │
├─────────────────────────────────────────────────────────┤
│ L2  shim 头文件 (shim/**_ffi.h)      ★ 唯一的净化点 ★     │
│     只有 C 标准类型：int32_t/size_t/bool/裸指针/           │
│     opaque handle/POD struct。                            │
│     不 include 任何 C++ 头文件、STL、第三方库头文件         │
├─────────────────────────────────────────────────────────┤
│ L1  shim 实现 (shim/**_ffi.cpp) + 原有 C++ 项目           │
│     C++ 的自由世界：STL、Boost、OpenCV、protobuf、         │
│     模板、异常、智能指针……全部照常使用，一行不改            │
└─────────────────────────────────────────────────────────┘
```

三条铁律，全部只约束 L2 这一个文件：

1. **L2 的 include 列表只允许 C 标准头**（`stdint.h`/`stddef.h`/`stdbool.h`）。出现任何 C++ 或第三方头文件即为封装失败。
2. **bindgen 只解析 L2**。因此 bindgen 的 include path 不需要、也不应该配置任何第三方库路径——如果发现 bindgen 跑不通需要加 OpenCV/Boost 的 include path，这本身就是 L2 被污染的报警信号。
3. **L1 不受任何限制**。第三方库照常 include、照常链接、照常调用；原有业务代码一行不改。FFI 封装改变的只是"类型名字能不能穿过语言边界"，不是"能不能使用某个库"。

一个常见误解需要在团队内明确澄清："shim 头文件不能出现第三方类型" ≠ "不能使用第三方库"。库的能力全部保留，只是 `cv::Mat`、`boost::optional` 这些**类型名字**在穿越 Rust/C++ 边界的一瞬间，被 L1 翻译成两边都认识的 C 类型（裸指针 + 基本类型 + 长度），过了边界再由 L3 重新包装成好用的 Rust 类型。

## 1.2 每个接口动手前的五分钟决策流

对着原有接口的每一个函数签名，按顺序问四个问题，答案直接决定写法：

```
Q1: 签名里的每个类型，是不是 C ABI 稳定的?
    (int/float/裸指针/纯 C struct → 是; 其他一切 C++ 类型 → 否)
    │
    ├─ 全部是 → 走【直通模式】: 可能连 shim 都不用写，直接 bindgen 原头文件
    │
    └─ 存在否 → Q2: 这个 C++ 类型，Rust 侧需要"看内容"还是只需要"转手"?
                │
                ├─ 只转手(拿到后原样传给下一个 C++ 接口)
                │    → 走【opaque handle 模式】: 不翻译内容，包成指针透传
                │
                └─ 要看内容 → Q3: 数据是"值语义小数据"还是"资源/大对象"?
                             │
                             ├─ 值语义(字符串/数组/简单结构)
                             │    → 走【拍平模式】: 指针+长度 / POD struct
                             │
                             └─ 资源/大对象 → Q4: 有没有现成的字节流表示?
                                            │
                                            ├─ 有(protobuf/json/自带序列化)
                                            │    → 走【字节流模式】
                                            │
                                            └─ 没有 → opaque handle +
                                                      按需提供数据提取函数
```

四种模式覆盖实践中 95% 以上的接口。下面每种模式给出完整可抄的写法。真正 gnarly 的边角类型（POD 布局、`long`/`long double` 陷阱、future、CRT 一致性）在第五部分作为深水区参考展开。

---

# 第二部分：四种核心模式的标准写法

## 2.1 直通模式：签名本来就是 C ABI 稳定的

原接口如果长这样，不需要写任何 shim 实现：

```cpp
// legacy 项目里本来就有的稳定 C API
extern "C" int foo_version(void);
extern "C" int foo_checksum(const uint8_t* data, size_t len);
```

只需要确认三件事：头文件能被 bindgen 消费（纯 C 语法）、include path 完整、bindgen allowlist 覆盖到目标符号。这对应 Manifest 里 `C ABI Shims=none` + Reason 注明 direct bindgen 的情况——注意 direct bindgen 只免除手写 shim，**不免除 L3 safe binding**：raw binding 仍然要私有化，对外仍然要包一层 safe API。

**实践判断技巧**：很多 C++ 项目会有一部分"C 风格核心 + C++ 便利封装"的分层。优先找到 C 风格核心层直通，比逐个翻译 C++ 便利层划算得多。用代码图谱工具（如 GitNexus 的 `context`）查一下 C++ 便利函数的实现，经常会发现它只是薄薄一层转发。

## 2.2 拍平模式：值语义数据的双向翻译

适用于：字符串、数值数组、简单结构体、`optional`、小型 map——所有"Rust 侧真正需要读写其内容"的值类型数据。

**方向一（Rust → C++，输入参数）：指针+长度进，shim 内现场构造**

这是最简单、最零风险的方向，固定模板：

```cpp
// shim.h
extern "C" bool myapi_load(MyHandle h,
                            const char* path, size_t path_len,      // ← std::string
                            const int32_t* ids, size_t ids_len);    // ← std::vector<int>
```

```cpp
// shim.cpp
#include "myapi.h"       // 原有 C++ 接口，含 STL 签名，照常 include
#include "myapi_ffi.h"

extern "C" bool myapi_load(MyHandle h, const char* path, size_t path_len,
                            const int32_t* ids, size_t ids_len) {
    if (!h || (!path && path_len) || (!ids && ids_len)) return false;  // 判空防御
    try {
        std::string s(path, path_len);                 // 局部构造，函数返回自动析构
        std::vector<int> v(ids, ids + ids_len);
        return static_cast<MyApi*>(h)->load(s, v);     // 调原接口，一行不改
    } catch (...) { return false; }
}
```

实践要点：

- 字符串**永远传 `(ptr, len)` 对**而不是 NUL 结尾——Rust 的 `&str` 天然是胖指针，`s.as_ptr(), s.len()` 零成本；而 `CString` 转换要多一次分配还要处理内部 NUL 错误。
- STL 对象作为 shim 函数的**局部变量**，生命周期在函数体内闭合，不需要任何跨边界的内存管理——这是拍平模式输入方向零心智负担的原因。
- `std::string_view`/`std::span` 输入等价于 `(ptr, len)`，处理方式相同；但若原接口会**保存**这个视图（而不是当场用完），shim 内部必须拷贝一份，否则会造成悬垂。

**方向二（C++ → Rust，输出），按数据大小二选一：**

小而定长 → 调用者提供缓冲区（无堆分配，适合高频调用）：

```cpp
// shim.h — 两段式：先问大小，再填数据
extern "C" size_t myapi_get_name_len(MyHandle h);
extern "C" bool   myapi_get_name(MyHandle h, char* buf, size_t buf_len);
```

变长/复杂 → C++ 分配 + 导出配对 free（灵活，适合低频大数据）：

```cpp
// shim.h
extern "C" bool myapi_export_json(MyHandle h, char** out, size_t* out_len);
extern "C" void myapi_free_buffer(char* p);
```

```cpp
// shim.cpp
extern "C" bool myapi_export_json(MyHandle h, char** out, size_t* out_len) {
    if (!h || !out || !out_len) return false;
    try {
        std::string json = static_cast<MyApi*>(h)->exportJson();
        *out = (char*)malloc(json.size());
        if (!*out) return false;
        memcpy(*out, json.data(), json.size());
        *out_len = json.size();
        return true;
    } catch (...) { return false; }
}
extern "C" void myapi_free_buffer(char* p) { free(p); }
```

**内存配对铁律**：分配和释放必须发生在同一侧。C++ `malloc`/`new` 的内存只能由 C++ 侧导出的 free 函数释放，Rust 绝不能用 `Box::from_raw`/`Vec::from_raw_parts` 接管；反之 Rust 分配的缓冲区 C++ 侧只能写入、不能释放。（两侧分配器/运行时不保证一致，深层原因见第 5.4 节。）L3 safe binding 用 RAII 兜底：

```rust
// L3: 保证 free 一定被调用
pub struct JsonExport { ptr: *mut c_char, len: usize }
impl Drop for JsonExport {
    fn drop(&mut self) { unsafe { myapi_free_buffer(self.ptr) } }
}
impl JsonExport {
    pub fn as_str(&self) -> &str {
        unsafe { std::str::from_utf8_unchecked(
            std::slice::from_raw_parts(self.ptr as *const u8, self.len)) }
    }
}
```

**特殊值类型的拍平对照表：**

| 原类型 | 拍平后的 C ABI 形式 |
|---|---|
| `std::optional<T>` | `bool` 返回值 + `T* out` 参数；或 `has_value` 字段的 POD struct |
| `std::variant<A,B>` | `enum tag` + union/平行字段的 POD struct |
| `std::any` | 不建议暴露；必须时退化为 `void*` + 类型 ID + 销毁函数指针，shim 承担全部类型擦除 |
| `std::expected<T,E>`(C++23) | 二分支和类型：`E` 走状态枚举/错误码，`T` 走 out 参数 |
| `std::map<K,V>` | 平行数组 `(K* keys, V* vals, size_t len)` 或 `struct{K;V;}` 数组 |
| `std::pair<A,B>` | 两个 out 参数，或 POD struct |
| `enum class E` | shim.h 重新声明 C enum，.cpp 里 `static_assert` 数值一致（见 5.5） |
| `bool`(签名里的) | 保留 bool(C99 起稳定)，或保守用 `int32_t`，统一即可 |
| `std::string_view` 输入 | `(const char*, size_t)`，和 string 一样 |

## 2.3 opaque handle 模式：资源、大对象、第三方类型的透传

适用于：带析构逻辑的对象、内含 STL/第三方成员的类、只在 C++ 接口之间流转不需要 Rust 读内容的类型。这是实践中用得最多的模式。

**基础形态：create/destroy 配对**

```cpp
// shim.h
typedef struct MyApiOpaque MyApiOpaque;      // 不完整类型，布局不可见
typedef MyApiOpaque* MyHandle;

extern "C" MyHandle myapi_create(const char* cfg, size_t cfg_len);
extern "C" void     myapi_destroy(MyHandle h);   // 允许 h == NULL，幂等
```

```cpp
// shim.cpp
extern "C" MyHandle myapi_create(const char* cfg, size_t cfg_len) {
    try {
        auto* obj = new MyApi(std::string(cfg, cfg_len));
        return reinterpret_cast<MyHandle>(obj);
    } catch (...) { return nullptr; }
}
extern "C" void myapi_destroy(MyHandle h) {
    delete reinterpret_cast<MyApi*>(h);          // delete nullptr 是安全的
}
```

```rust
// L3: Drop 保证 destroy 恰好调用一次
pub struct MyApi { handle: MyHandle }
impl MyApi {
    pub fn new(cfg: &str) -> Result<Self, Error> {
        let h = unsafe { myapi_create(cfg.as_ptr() as _, cfg.len()) };
        if h.is_null() { Err(Error::last()) } else { Ok(Self { handle: h }) }
    }
}
impl Drop for MyApi {
    fn drop(&mut self) { unsafe { myapi_destroy(self.handle) } }
}
// 默认不实现 Send/Sync，除非确认了线程安全性(见 3.5)
```

**变体一：原接口返回 `std::shared_ptr<T>`（共享所有权）**

handle 指向的不是 T 本身，而是堆上多包一层的 shared_ptr 壳，用壳的生命周期控制引用计数：

```cpp
extern "C" MyHandle myapi_create_engine() {
    try {
        auto sp = myapi::createEngine();     // shared_ptr<Engine>
        return reinterpret_cast<MyHandle>(new std::shared_ptr<Engine>(sp));  // 壳
    } catch (...) { return nullptr; }
}
extern "C" MyHandle myapi_engine_clone(MyHandle h) {   // Rust 侧 Clone → 引用计数+1
    if (!h) return nullptr;
    auto* sp = reinterpret_cast<std::shared_ptr<Engine>*>(h);
    return reinterpret_cast<MyHandle>(new std::shared_ptr<Engine>(*sp));
}
extern "C" void myapi_engine_release(MyHandle h) {     // Drop → 引用计数-1
    delete reinterpret_cast<std::shared_ptr<Engine>*>(h);
}
```

**变体二：第三方类型在接口间流转（如 `cv::Mat` 贯穿多个函数）**

不要每次跨边界都拍平——把第三方对象本身包成 handle 透传，只在真正需要读数据的终点提供提取函数：

```cpp
// shim.h — cv::Mat 三个字从头到尾没出现
typedef struct ImgOpaque* ImgHandle;

extern "C" ImgHandle myapi_load_image(const char* path, size_t len);
extern "C" ImgHandle myapi_denoise(MyHandle api, ImgHandle img);   // Mat→Mat, 全程不出 C++
extern "C" ImgHandle myapi_sharpen(MyHandle api, ImgHandle img);
extern "C" bool myapi_img_read(ImgHandle img, uint8_t* buf, size_t buf_len,
                                int* rows, int* cols, int* channels);  // 终点才提取
extern "C" void myapi_img_destroy(ImgHandle img);
```

Rust 侧串联 `load → denoise → sharpen → read` 时，中间结果只是 handle 在转手，没有任何像素数据的拷贝和翻译，性能与纯 C++ 调用链几乎一致。**这是处理"接口签名依赖第三方类型"的首选答案**：第三方类型不需要翻译，只需要藏起来。

**变体三：类成员里有第三方/STL 类型**

```cpp
class MyProcessor {
    cv::Mat cache_;                    // 成员含第三方类型
    std::vector<Result> history_;
public: ...
};
```

不需要任何特殊处理——opaque handle 隐藏的是**整个对象的布局**，成员里有什么与 Rust 无关。只有当 Rust 需要读取某个成员时，才为那个成员单独加一个提取函数（按 2.2 拍平）。如果原类已经是 pimpl 设计，连壳都不用包，pimpl 指针直接当 handle 用（见 5.5）。

**所有权转移（move-out / move-in）**

原接口通过 `std::move` 转移所有权时（如 `std::unique_ptr<Item> takeItem()`、`void submit(Job&&)`），C ABI 没有"移动"概念，用**显式的转移函数**表达，并在注释里写死转移后归属：

```cpp
// C++: std::unique_ptr<Item> Container::takeFirst();
ItemHandle foo_take_first(FooHandle h);   // 返回 nullptr 表示空；非空则调用方负责 item_destroy

// C++: void Queue::submit(std::unique_ptr<Job> job);
// 成功: job 所有权归队列; 失败(返回 false): 所有权仍归调用方，需自行 destroy
bool foo_submit(FooHandle h, JobHandle job);
```

## 2.4 字节流模式：有 schema 的复杂结构

适用于：protobuf 消息、JSON 可表达的配置/结果对象、任何"两侧都能按同一 schema 解析"的复杂嵌套数据。

```cpp
// shim.h — 复杂结构退化为 bytes
extern "C" bool myapi_handle_request(MyHandle h,
                                      const uint8_t* req, size_t req_len,
                                      uint8_t** resp, size_t* resp_len);
extern "C" void myapi_free_bytes(uint8_t* p);
```

```cpp
// shim.cpp — protobuf 类型只活在这里
#include "myrequest.pb.h"

extern "C" bool myapi_handle_request(MyHandle h, const uint8_t* req, size_t req_len,
                                      uint8_t** resp, size_t* resp_len) {
    try {
        MyRequest request;
        if (!request.ParseFromArray(req, (int)req_len)) return false;
        MyResponse response = static_cast<MyApi*>(h)->handle(request);
        std::string bytes = response.SerializeAsString();
        *resp = (uint8_t*)malloc(bytes.size());
        memcpy(*resp, bytes.data(), bytes.size());
        *resp_len = bytes.size();
        return true;
    } catch (...) { return false; }
}
```

Rust 侧用 `prost` 从同一份 `.proto` 生成结构体，两边不共享任何 C++ 类型，只共享 schema 和字节流。**选择判据**：结构嵌套超过两层、字段超过十个、或者未来还会加字段——手写 POD struct 拍平的维护成本会迅速超过一次序列化的运行时开销，直接上字节流。反之，三五个字段的扁平结构，POD struct 拍平更直接（POD 拍平的布局纪律见 5.1）。

---

# 第三部分：横切问题的统一处理

以下问题不属于某种模式，而是**所有 shim 函数都要过一遍**的检查项。

## 3.1 异常与错误传递（双向）

**C++ → Rust 方向**：C++ 异常穿越 `extern "C"` 边界是 UB。团队约定：**shim.cpp 里每一个导出函数体，第一层就是 try/catch**，没有"这个函数肯定不抛"的豁免——第三方库升级、意外输入都可能引入新异常路径。

需要错误详情时，统一用线程局部错误槽，全项目一份：

```cpp
// shim 公共部分
static thread_local std::string g_last_error;

#define SHIM_GUARD_BEGIN try {
#define SHIM_GUARD_END(fail_ret) \
    } catch (const std::exception& e) { g_last_error = e.what(); return fail_ret; } \
      catch (...) { g_last_error = "unknown C++ exception"; return fail_ret; }

extern "C" const char* myapi_last_error(void) { return g_last_error.c_str(); }
```

```cpp
extern "C" bool myapi_load(MyHandle h, const char* p, size_t n) {
    if (!h) { g_last_error = "null handle"; return false; }
    SHIM_GUARD_BEGIN
        return static_cast<MyApi*>(h)->load(std::string(p, n));
    SHIM_GUARD_END(false)
}
```

L3 把 `false`/`nullptr` + `last_error` 统一映射为 `Result<T, Error>`。

**非异常错误通道**：原接口若用 `std::error_code`/`std::errc` 报错，`value()` 是整型可直接过边界，但必须**连同 category 一起表达**——同一数值在不同 category 下含义不同。建议在 shim 层把项目内实际出现的 `(category, value)` 组合收敛映射到自己的状态枚举，而不是把裸 `int` 甩给 Rust。

**Rust panic 反向逃逸（Rust → C++ 方向）**：对称的一面同样不允许。自 Rust 1.81 起，panic 穿出普通 `extern "C"` 函数会 abort 进程；按本手册红线不依赖 `-unwind` 互通，统一在边界兜底——所有会被 C++ 调用的 Rust 函数（主要是回调 trampoline）必须用 `std::panic::catch_unwind` 包住，panic 转成错误码/默认值返回（示例见 3.2）。

## 3.2 回调：函数指针 + user_data + trampoline

原接口的 `std::function`/lambda 参数，shim 一律降级为 C 经典模式：

```cpp
// shim.h
typedef void (*MyCallback)(int32_t event, void* user_data);
extern "C" bool myapi_set_callback(MyHandle h, MyCallback cb, void* user_data);
extern "C" void myapi_clear_callback(MyHandle h);   // 必须提供，否则 Rust 侧闭包无法安全回收
```

```cpp
// shim.cpp — 桥接到 std::function
extern "C" bool myapi_set_callback(MyHandle h, MyCallback cb, void* ud) {
    if (!h || !cb) return false;
    SHIM_GUARD_BEGIN
        static_cast<MyApi*>(h)->setCallback([cb, ud](int e) { cb(e, ud); });
        return true;
    SHIM_GUARD_END(false)
}
```

```rust
// L3: Box 闭包 + trampoline，生命周期与 wrapper 绑定
pub struct MyApi { handle: MyHandle, cb: Option<Box<Box<dyn Fn(i32) + Send>>> }

extern "C" fn trampoline(event: i32, ud: *mut c_void) {
    // panic 绝不允许穿回 C++
    let _ = std::panic::catch_unwind(|| {
        let f = unsafe { &*(ud as *const Box<dyn Fn(i32) + Send>) };
        f(event);
    });
}
impl MyApi {
    pub fn set_callback(&mut self, f: impl Fn(i32) + Send + 'static) {
        let boxed: Box<Box<dyn Fn(i32) + Send>> = Box::new(Box::new(f));
        unsafe { myapi_set_callback(self.handle, trampoline,
                                     &*boxed as *const _ as *mut c_void); }
        self.cb = Some(boxed);   // wrapper 持有，Drop 时先 clear_callback 再释放
    }
}
```

三个必答题写进代码注释：回调可能在哪个线程触发？对象销毁后回调是否还可能到达（必须保证不会）？回调内部再调 API 会不会死锁？——这三个问题的答案要从 L1 源码确认，代码图谱工具查回调触发点是有效手段。注意 `user_data` 指向的 Rust 闭包若可能在 C++ 工作线程被触发，捕获的内容必须 `Send`（可能并发触发还需 `Sync`），用 trait bound 强制而不是靠口头约定。

## 3.3 对象生命周期、符号名与命名空间

**符号名拍平**：C ABI 符号必须全局唯一且无 mangling，统一命名公式：

```
{target_stem}_{动作}[_{类型区分后缀}]
```

| 原接口 | shim 导出 |
|---|---|
| `parse(const std::string&)` / `parse(const uint8_t*, size_t)` 重载 | `json_parse_str` / `json_parse_bytes` |
| `Stack<int>` / `Stack<std::string>` 模板实例 | `stack_int_*` / `stack_str_*`（只导出实际用到的实例化，永不导出模板本身；如何"发现用到哪些实例"见附录 A） |
| `myproj::parser::Json::dump()` | `parser_json_dump`（命名空间拍进前缀） |
| `operator==` / `operator[]` / `operator<<` | `foo_equals` / `foo_get_at` / `foo_to_string` |

**所有导出函数必须包在 `extern "C" { ... }` 里**关闭 name mangling，否则 bindgen/链接器拿到的符号名不可预测。

**符号可见性与调用约定**（共享库场景）：GCC/Clang 建议 `-fvisibility=hidden` + 显式 `__attribute__((visibility("default")))`，Windows 对应 `__declspec(dllexport)`，惯例是定义统一导出宏：

```cpp
#if defined(_WIN32)
  #define FOO_API __declspec(dllexport)
#else
  #define FOO_API __attribute__((visibility("default")))
#endif
```

32 位 x86 Windows 上 `__cdecl`/`__stdcall` 并存，`extern "C"` 只管符号名不管调用约定；若目标平台含 win32，导出函数和函数指针类型必须显式统一（通常 `__cdecl`，与 Rust `extern "C"` 对应）。

## 3.4 线程与全局状态：标注重于加锁

- 每个导出函数在 shim.h 注释里标注线程安全等级：`// thread-safe` / `// requires external sync` / `// main-thread only`。这个信息必须从 L1 源码确认（查全局变量、`thread_local`、单例的使用），不能猜。
- L3 用类型系统落实标注：非线程安全的 handle wrapper **不实现 `Send`/`Sync`**（默认行为，保持即可）；确认线程安全后才手动 `unsafe impl Send`。让编译器阻止误用，比文档提醒可靠。
- 单例/全局 init 类接口，显式导出 `xxx_global_init()`/`xxx_global_shutdown()`，调用顺序约束写注释；不要在 shim 里悄悄隐藏"第一次调用才初始化"的副作用。
- 慎用"shim 层全局加锁"来制造线程安全——锁粒度决策留给 L3（`Mutex<MyApi>`），Rust 侧可见可控，C++ 侧的隐藏锁排查死锁时是灾难。
- **同步原语红线**：`std::atomic<T>`（布局与 lock-free 性不保证跨实现一致）、`std::mutex`/`std::condition_variable`（不可拷贝不可移动、内部平台私有）**绝不按值出现在边界签名或边界结构体里**。跨边界的同步需求一律通过导出函数表达，或把整个临界区封装进一个导出函数内部。

## 3.5 字符串编码：边界外统一 UTF-8

shim 边界上的所有字符串一律 UTF-8 + `(ptr, len)`。原接口用 `std::wstring`/`wchar_t`（注意平台宽度差异：Windows 16 位，Linux/macOS 通常 32 位）或本地编码（GBK 等）的，转换收敛在 shim.cpp 内完成（Windows 用 `MultiByteToWideChar`/`WideCharToMultiByte` 或 ICU），不把编码问题泄漏给 Rust 侧。L3 收到字节后用 `String::from_utf8_lossy` 或严格校验，取决于数据源可信度。

`std::filesystem::path` 本质是字符串但 native 表示平台相关（Windows 是 `wchar_t` 序列且不保证合法 UTF-16）：常规场景边界统一 UTF-8，shim 内用 `u8string`/`u8path` 转换；需处理任意文件系统的非法编码路径时，退化为原始字节序列 `(const uint8_t*, size_t)`，Rust 侧用 `OsString`/`PathBuf` 接住并注明"平台 native 字节，不保证 UTF-8"。

---

# 第四部分：第三方库依赖的工程处理

## 4.1 接口签名依赖第三方类型：按位置套模式

原有 API 头文件里出现 `cv::Mat`、`boost::optional`、`Eigen::MatrixXd` 时，不需要新理论，按类型出现的位置套用第二部分的模式：

| 第三方类型出现位置 | 套用模式 | 说明 |
|---|---|---|
| 输入参数 | 拍平(2.2 方向一) | shim.cpp 内用裸数据现场构造第三方对象；优先零拷贝构造(`cv::Mat(rows,cols,type,ptr)`、`Eigen::Map`) |
| 按值返回 | 拍平(2.2 方向二) | 对象生命周期在 shim 函数内闭合，数据搬出即可 |
| 智能指针返回 | opaque handle 变体一 | 包 shared_ptr 壳，不暴露第三方类型布局 |
| 在多个接口间流转 | opaque handle 变体二 | 透传 handle，终点才提取，避免反复翻译 |
| 你的类的成员 | opaque handle 变体三 | 整对象作 handle，成员与 Rust 无关 |
| protobuf 消息 | 字节流(2.4) | 两侧共享 .proto，不共享 C++ 类型 |

零拷贝构造的坑要写进注释：例如 Eigen 默认列主序、C 数组直觉是行主序，约定不一致时**数值错位但不报错**，必须在 shim.h 里注明 `// row-major` 并在 smoke test 里用非对称矩阵验证。

## 4.2 例外：第三方库本身是稳定 C ABI

zlib、SQLite、libcurl 这类纯 C 库的类型（如 `z_stream`）是稳定 C 结构，可以直接 bindgen 它们的头文件，不需要在 shim 里转手。判断标准：库的头文件本身能用纯 C 编译器编译通过，且供应商有跨版本 ABI 承诺。拿不准就当不稳定处理——多包一层 handle 的成本远低于一次布局漂移的排查成本。

## 4.3 build.rs：两条 include path 必须分开

这是本场景下最高频的实操坑。`cc::Build`（编译 shim.cpp）和 `bindgen`（解析 shim.h）的 include path 职责完全不同：

```rust
fn main() {
    // ① cc::Build 编译 L1，需要第三方库的一切
    cc::Build::new()
        .cpp(true).std("c++17")
        .include("shim")
        .include(legacy_root.join("include"))
        .include("/usr/include/opencv4")            // 第三方 include 只在这里
        .files(shim_sources)
        .files(legacy_sources_needed)                // 依赖分析确定的 legacy 源文件
        .compile("myapi_shim");

    // ② 链接第三方库
    println!("cargo:rustc-link-lib=opencv_core");
    println!("cargo:rustc-link-lib=stdc++");         // 或 macOS: c++

    // ③ bindgen 只看 L2，不需要任何第三方路径
    bindgen::Builder::default()
        .header("shim/myapi_ffi.h")
        .allowlist_function("myapi_.*")
        .allowlist_type("MyApi.*")
        .generate().unwrap()
        .write_to_file(out.join("bindings.rs")).unwrap();

    // ④ 变更追踪
    println!("cargo:rerun-if-changed=shim");
}
```

**自检信号**：③ 如果报"找不到 opencv2/core.hpp"，不是去给 bindgen 加 include path，而是回头检查 shim.h——它被污染了。

## 4.4 版本锁定

第三方库版本漂移会让"同一份代码在不同机器行为不同"：

- 能 vendoring 就 vendoring（源码进仓库或 git submodule 锁定 commit）。
- 只能链接系统库时，在 shim.cpp 里用版本宏做编译期拦截：

  ```cpp
  #include <opencv2/core/version.hpp>
  static_assert(CV_VERSION_MAJOR == 4, "requires OpenCV 4.x");
  ```

- 版本要求写进 Manifest 对应条目的 Reason 和 README，CI 环境固定版本。
- 整个 C++ 侧（原库 + shim）建议编成**一个链接单元**，避免 C++ 对象在两个 C++ 模块之间流动（运行时一致性详见 5.4）。

---

# 第五部分：类型系统深水区（特性参考）

前四部分覆盖了 95% 的接口。这一部分是**遇到具体 gnarly 特性时的查阅参考**，把最容易在真实项目里咬人、但前面模式没展开的 ABI 细节集中起来。

## 5.1 POD 结构体按值传递与内存布局

**并非所有 `struct` 都能按值跨边界。** 带非平凡拷贝/移动构造或析构函数的类型按值传递时，C++ ABI 会引入隐藏的构造/析构调用甚至改为隐式传指针，C 侧无法对应——这是 UB。

**判定标准**：只有同时满足 **trivially-copyable** 且 **standard-layout**（传统 POD）的类型，才允许按值出现在边界签名或边界结构体字段里，用 `static_assert` 强制：

```cpp
static_assert(std::is_trivially_copyable_v<FooConfig>, "must be trivially copyable");
static_assert(std::is_standard_layout_v<FooConfig>, "must be standard layout");
```

- 不满足的类型一律退回 opaque handle（2.3）。
- 满足的 POD 在 shim.h 里用纯 C 语法**重新声明**（字段全用定宽类型，见 5.2），`.cpp` 内 `static_assert(sizeof(...))` + 逐字段 `static_assert(offsetof(...))` 与原类型比对防漂移；Rust 侧 `#[repr(C)]`。
- **禁止位域**（bit-field）：位分配顺序、跨存储单元行为都是实现定义的。需要紧凑标志位改用 `uint32_t flags` + 位掩码常量。
- 谨慎对待 `#pragma pack`/`alignas`：默认建议边界结构体不使用非默认对齐，宁可多几个字节 padding；确需时两侧对齐指示必须完全一致（Rust 用 `#[repr(C, packed(N))]`/`#[repr(align(N))]`）。

## 5.2 基础类型宽度与平台差异

C/C++ 的裸整型和部分浮点型宽度是平台相关的，签名里直接沿用会造成同一份 shim 在不同平台上 ABI 不一致：

| 类型 | 风险与处理 |
|---|---|
| `long` / `unsigned long` | Windows LLP64（32 位）vs Linux/macOS LP64（64 位）。**边界签名禁止裸 `long`**，shim 内转 `int32_t`/`int64_t` |
| `char` | 符号性平台/编译器相关。字节数据一律 `uint8_t`，文本用 `char` 但只承载 UTF-8 |
| `long double` | x86 Linux 80 位、MSVC 等同 64 位、AArch64 128 位。**禁止过边界**，shim 内收窄 `double` 并评估精度 |
| `__int128` | MSVC 不支持，跨语言 ABI 无保证。禁止过边界，拆两个 `uint64_t` 或退化字节数组 |
| `size_t`/`ptrdiff_t`/`intptr_t` | 两侧定义一致（Rust `usize`/`isize`），**允许使用**，长度/索引推荐 `size_t` |
| `int` 等 | 主流平台 `int` 是 32 位，但纪律上签名显式写 `int32_t` 消除歧义 |

**`std::chrono` 时间类型**不能过边界，拍平成整数并**写死单位与纪元**：推荐 duration 用 `int64_t` 纳秒、time_point 用"自 Unix epoch 起 `int64_t` 纳秒"；shim 内 `duration_cast` 转换。不要用 `double` 秒数表示时间（长时间戳精度爆炸）。

```cpp
void foo_set_timeout_ns(FooHandle h, int64_t timeout_ns);  // 单位: 纳秒
```

## 5.3 异步：future / promise / 协程

`std::future<T>` 没有 C ABI，C++20 协程返回的 awaitable 更是库私有。二选一，按 Rust 侧调用模式决定：

1. **轮询模式**：shim 内部持有 future（包在异步操作 handle 里），导出 `foo_op_is_ready` + `foo_op_take_result`。`take_result` 一次性（对应 `future::get()` 只能调一次），重复调用返回明确错误而非 UB。
2. **回调模式**：future 完成时触发第 3.2 节的"函数指针 + user_data"回调，safe binding 桥接成 oneshot channel 包装成 `impl Future`，对接 Rust async 生态。

- C++20 协程一般折叠进这套模型：shim 内部 `co_await` 到底，对外只暴露轮询或回调。
- **取消语义必须显式**：异步操作 handle 被 destroy 时，未完成操作是取消、detach 还是阻塞等待完成，必须在注释里写死并实现一致，否则 Rust `Drop` 时机会造成难查的挂起或 use-after-free。

```cpp
typedef struct FooOpOpaque* FooOpHandle;
FooOpHandle foo_compute_async(FooHandle h, const uint8_t* in, size_t in_len);
bool foo_op_is_ready(FooOpHandle op);
bool foo_op_take_result(FooOpHandle op, FooResult* out);  // 只能成功一次
void foo_op_destroy(FooOpHandle op);                      // 未完成时销毁 = 请求取消并等待退出
```

## 5.4 C++ 运行时、CRT 与分配器一致性

即使每个签名都是完美 C ABI，运行时库层面不一致仍会造成最难排查的崩溃：堆损坏、静默 ODR 冲突、跨模块 STL 布局错位。

- **谁分配谁释放**是铁律（2.2 已强调）：导出配对 free 函数就是它的落地形式。
- **Windows CRT 一致性**：所有 C++ 目标必须同一 CRT 变体（`/MD` vs `/MT`、debug vs release）。debug CRT 与 release CRT 混链堆句柄不同，跨界 free 直接堆损坏。Rust 默认链 release CRT，C++ 侧 debug 构建对接时要特别小心。
- **标准库实现一致性**：Linux/macOS 上 libstdc++ 与 libc++ ABI 互不兼容，整条链路必须统一，用 `ldd`/`otool -L` 校验没混入两个。
- **STL debug 模式**：MSVC `_ITERATOR_DEBUG_LEVEL`、libstdc++ `_GLIBCXX_DEBUG` 会改变 STL 容器布局，同进程内不一致就是静默 ODR 违规——这也是"STL 绝不过边界、shim 与原库同配置编译"的又一重理由。
- **链接单元**：整个 C++ 侧编成一个链接单元，避免 C++ 对象在两个 C++ 模块间流动。

## 5.5 其他特性速查

**引用 / `const` 语义**：`const T&` → `const T*`，`T&` 输出 → `T* out`，shim 内解引用前一律判空（引用非空保证在 C ABI 里不存在）；原 `const` 语义写进注释提醒 L3 用 `&` 而非 `&mut`。

**`enum class` / unscoped enum**：shim.h 用 C enum 或 `int32_t` 常量重声明，`.cpp` 里 `static_assert` 数值一致 + `sizeof` 一致。特别注意**无固定底层类型的 unscoped enum 大小是实现定义的**，跨边界前先补 `: int32_t` 或一律以 `int32_t` 传递。L3 用 `TryFrom<i32>` 校验拒绝非法值。

```cpp
// C++: enum class Status : int32_t { Ok = 0, NotFound = 1 };
typedef enum { FOO_STATUS_OK = 0, FOO_STATUS_NOT_FOUND = 1 } FooStatus;
static_assert(static_cast<int32_t>(Status::Ok) == FOO_STATUS_OK, "enum drift");
static_assert(sizeof(FooStatus) == sizeof(int32_t), "enum size drift");
```

**宏 / 编译期常量**：简单字面量宏 bindgen 通常能转；复杂函数式宏或依赖展开的常量，在 shim.h 里用 `static const`/`constexpr` 重声明保证 bindgen 稳定识别。

```cpp
// 原始: #define FOO_MAX_RETRY (3 * 2)
static const int32_t FOO_MAX_RETRY = 6;
```

**Pimpl / 不完整类型**：原类已是 pimpl 设计的，pimpl 指针直接当 opaque handle 复用，不用额外包壳；没有 pimpl（成员含 STL）的，shim 承担"人工 pimpl"——对外只给不完整类型指针，`.cpp` 内转型成完整类型访问。

**`std::array` / 定长数组**：布局稳定（同 `T[N]`），可直接 `T*` + 编译期已知 `N` 传递，只需注释写明长度与行/列主序约定；外层容器（如 `vector<array<float,3>>`）按 2.2 拍平成 `(const float* data, size_t count)` 并注明每逻辑元素占 3 个 float。

## 5.6 一张判断表

| C++ 特性 | 能否直接过边界 | shim 处理方式 | 主要参见 |
|---|---|---|---|
| STL 容器/字符串 | 否 | 指针+长度，或分配+配对 free | 2.2 |
| string_view/span | 否（语义对应） | 转 (ptr, len)，注释写死生命周期 | 2.2 |
| optional/variant/expected | 否 | out+bool 或 tagged union；expected 走错误约定 | 2.2 |
| 异常 | 否 | try/catch 转错误码 + TLS 详情 | 3.1 |
| Rust panic（反向） | 否 | trampoline 内 catch_unwind 兜底 | 3.1/3.2 |
| 对象生命周期/智能指针 | 否 | opaque handle + create/destroy(/retain/release) | 2.3 |
| 移动语义/所有权转移 | 否 | 显式 take/submit 函数，注释写死归属 | 2.3 |
| 虚函数/继承 | 否 | 拍平成自由函数，内部虚派发 | 2.3 |
| 模板 | 否 | 只导出具体实例化，不导出模板本身 | 3.3/附录A |
| 运算符重载 | 否 | 翻译成具名函数 | 3.3 |
| 回调/std::function/lambda | 否 | 函数指针 + user_data + trampoline | 3.2 |
| future/promise/协程 | 否 | 异步 handle + 轮询或回调，取消语义显式化 | 5.3 |
| 全局状态/单例 | 部分 | 显式访问函数，标注线程安全性 | 3.4 |
| 引用参数 | 否 | 转指针，显式判空 | 5.5 |
| enum class / unscoped enum | 部分 | 重声明 + static_assert 数值与大小 | 5.5 |
| 重载/命名空间 | 否 | 具名后缀函数 + 符号前缀拍平 + 导出宏 | 3.3 |
| wchar_t/本地编码/fs::path | 否 | shim 内转换，边界外统一 UTF-8 | 3.5 |
| std::array/定长数组 | 是（布局稳定） | 直接传指针+编译期长度 | 5.5 |
| POD 结构体按值 | 部分 | 仅 trivially-copyable+standard-layout；重声明+校验；禁位域 | 5.1 |
| 裸 long / long double / __int128 | 否 | 换定宽类型；long double 收窄；__int128 拆两个 u64 | 5.2 |
| chrono 时间类型 | 否 | 拍平 int64_t + 写死单位与纪元 | 5.2 |
| atomic/mutex | 否 | 读写函数封装/收进 handle，绝不按值暴露 | 3.4 |
| 宏 | 部分 | 简单字面量可 bindgen，复杂宏改具名常量 | 5.5 |
| Pimpl | 是（已隐藏实现） | 直接复用为 opaque handle | 5.5 |
| 复杂嵌套结构 | 否 | 字节流 + schema（protobuf/json） | 2.4 |

---

# 第六部分：落地、校验与反模式

## 6.1 单个接口的实施步骤

1. **读签名，跑决策流**（1.2）：确定模式，把结论写进 Manifest Reason。
2. **确认五个语义**再写代码：参数/返回值的所有权、错误表达方式、空指针语义、线程约束、expected 来源。任何一项从源码确认不了 → 回读证据或问人，不猜。
3. **写 shim.h**：只用 C 标准类型，每个函数注释写清所有权和空指针语义。
4. **写 shim.cpp**：include 原头文件和第三方头文件，套 SHIM_GUARD 宏，判空，类型翻译，调原接口。
5. **写 L3 safe binding**：raw binding 私有化，Drop/Result/类型标注，unsafe 集中在 crate 内部。
6. **写 smoke test**：一条成功路径 + 一条错误路径，expected 来自源码/spec/测试等可信来源。
7. **build + test 通过后**才更新 Manifest 状态。

## 6.2 shim 代码评审 checklist

| # | 检查项 | 不合格的典型症状 |
|---|---|---|
| 1 | shim.h 的 include 只有 C 标准头 | 出现 `<string>`/`<opencv2/...>`/项目内部 C++ 头 |
| 2 | 每个导出函数有 try/catch 全包裹 | "这个函数不会抛"的口头豁免 |
| 3 | 每个 create 有配对 destroy，每个 alloc 有配对 free | 返回 `char*` 但找不到对应释放函数 |
| 4 | 分配与释放在同一侧 | Rust 里出现 `Box::from_raw` 接管 C++ 内存 |
| 5 | 所有指针入参有判空 | 直接解引用参数 |
| 6 | 字符串是 (ptr,len)，编码 UTF-8 | 依赖 NUL 结尾；wchar_t 泄漏到 shim.h |
| 7 | enum 有 static_assert 数值+大小校验 | shim.h 手抄枚举值，无编译期比对 |
| 8 | 线程安全等级有注释，L3 的 Send/Sync 与之一致 | wrapper 默认被 `unsafe impl Send` |
| 9 | 回调有注销函数，闭包生命周期由 wrapper 持有；trampoline 有 catch_unwind | set 了回调但对象销毁后回调仍可能触发；panic 穿回 C++ |
| 10 | bindgen 不需要第三方 include path 即可通过 | build.rs 里 bindgen 配了 opencv 路径 |
| 11 | 按值结构体是 trivially-copyable + standard-layout | 边界结构体含 STL 成员或非平凡析构；出现位域 |
| 12 | 签名无裸 long / long double / __int128 | 直接沿用原接口的平台相关基础类型 |

## 6.3 ABI 稳定性的持续校验

shim 交付后保留以下校验，防止未来 C++ 侧演进悄悄破坏约定：

| 校验点 | 方式 |
|---|---|
| enum 数值/大小漂移 | `.cpp` 内 `static_assert` 比对 C++ 原始枚举值和 sizeof |
| 结构体布局 | `static_assert(sizeof/offsetof(...))` + `is_trivially_copyable`/`is_standard_layout` 断言 |
| 符号可见性 | 全部 `extern "C"` + 导出宏，`nm`/`dumpbin` 校验未 mangling、无意外符号泄漏 |
| 异常泄漏 | 每个导出函数体确认 try/catch，CI 静态检查强制 |
| panic 泄漏 | 每个被 C++ 调用的 Rust `extern "C" fn` 确认 catch_unwind |
| 运行时一致性 | CI 校验链接产物 CRT/标准库依赖（`ldd`/`otool -L`/`dumpbin /dependents`），混链即失败 |
| ABI 版本常量 | 导出 `FOO_ABI_VERSION` 常量 + `foo_abi_version()` 函数，破坏性变更时递增；Rust 初始化时比对编译期常量与运行时返回，不一致 fail-fast |
| smoke test | 每个 shim 函数至少一条成功路径 + 一条错误路径 |

```cpp
#define FOO_ABI_VERSION 3
FOO_API int32_t foo_abi_version(void);   // .cpp 里 return FOO_ABI_VERSION;
```

## 6.4 反模式速查

| 反模式 | 为什么错 | 正确做法 |
|---|---|---|
| 因为接口依赖第三方类型而认为"没法做 FFI" | 混淆了"使用库"和"暴露类型" | 类型藏进 L1，套 4.1 的位置对照表 |
| bindgen 直接解析含 STL/第三方类型的原头文件 | 赌 ABI，换编译器即炸 | bindgen 只解析净化过的 shim.h |
| 每次跨边界都把大对象拍平成数组 | 无谓拷贝，接口爆炸 | 流转用 opaque handle，终点才提取 |
| 为通过 smoke test 放宽断言/吞掉错误 | 掩盖 FFI/生命周期真实问题 | 修问题本身；expected 不可信就停下确认 |
| shim 里悄悄全局加锁"保证"线程安全 | 隐藏锁，死锁难排查 | 标注等级，锁的决策上移到 L3 |
| 手写 POD struct 拍平十几个字段的嵌套结构 | 维护成本失控，加字段两边改 | 上字节流模式，schema 驱动 |
| 导出模板/公开全部 raw bindgen 符号 | 无稳定符号/unsafe 面失控 | 只导出具体实例化；raw binding 私有化 |
| 边界结构体按值传含非平凡析构的类型 | 隐藏构造/析构调用，UB | 退回 opaque handle；仅 POD 允许按值 |
| 签名直接用原接口的 `long`/`long double` | 平台间 ABI 不一致，静默错位 | 换定宽类型，shim 内转换 |

---

# 附录 A：如何发现模板用到了哪些实例化

3.3 节的策略是"只导出实际用到的具体实例化"，但**"实际用到了哪些"这个集合怎么算出来**本身就是一个难点，值得单独展开。

## A.1 为什么"发现"本身就是难点

模板实例化是**编译期、隐式、且散布在整个调用方代码里**的行为，不是一个能在库定义处一眼看全的清单。`grep 'Container<'` 会**同时漏报和误报**，因为 C++ 类型书写花样太多：

- **别名遮蔽**：`using IntBox = Container<int>;` 之后代码写 `IntBox`，grep 抓不到。`typedef`、template alias 同理。
- **CTAD / auto 推导**：`Container c{1, 2, 3};` 源码里根本没写模板参数。
- **默认模板参数**：源码写 `Container<int>`，真正实例化的规范类型可能是 `Container<int, std::allocator<int>>`。去重必须基于**补全默认参数后的规范类型**，而正则看不到被省略的部分。
- **传递实例化**：库自己的模板内部实例化出的类型，调用方源码里完全不出现。
- **宏 / 条件编译**：`#ifdef` 分支下才出现的实例化，取决于在哪个平台看。

所以"发现"必须靠**理解类型系统的工具**，有两个权威来源：源码级（编译器前端 AST）和产物级（编译产物的符号/调试信息）。

## A.2 路径一：Clang AST —— 源码级的权威答案

关键节点是 `ClassTemplateSpecializationDecl`（每个具体实例化），函数模板用 `functionDecl(isTemplateInstantiation())`。它已解决别名、CTAD、默认参数，因为你拿到的是**补全后的规范类型**。

快速探查：

```
clang-query> match classTemplateSpecializationDecl(hasName("::myproj::Container"))
```

工程化则写 LibTooling/RecursiveASTVisitor，在 `VisitClassTemplateSpecializationDecl` 里取 `getTemplateArgs()`、`getCanonicalType()` 规范化、`getSpecializationKind()` 区分隐式/显式，拍平成去重清单。

两个硬约束：**必须喂真实编译参数**（`CMAKE_EXPORT_COMPILE_COMMANDS=ON` 生成 `compile_commands.json`，用一致的 `-I`/`-D`/`-std`/平台宏）；**必须覆盖全部触发实例化的 TU**（隐式实例化只在触发它的 TU 的 AST 里出现，只解析库本身看到的是零）。

## A.3 路径二：编译产物的 DWARF / 符号表 —— 地面真相

拿最终 `.a`/`.so`，`nm -C` 看去混淆符号：`_ZN9ContainerIiE3getEv` 解出来就是 `Container<int>::get()`；或带 `-g` 编译后 `llvm-dwarfdump` 读 `DW_TAG_class_type`，`DW_AT_name` 直接是 `Container<int>`。注意 `-O2` 可能内联掉某些实例化不发射符号，发现用的这一遍应 `-O0 -g`（必要时 `-fno-inline`）。这是"编译器实实在在处理过的实例化"的完整快照，兜住路径一因分析范围不全的漏看，也做交叉验证。

## A.4 推荐做法：把"发现"反转成"约束 + 差异检查"

纯发现是**开集**问题，对代码演进脆弱：今天扫出 5 个，明天有人新写一个 `Container<Foo>`，shim 静默不覆盖直到运行期才炸——这和本手册"static_assert 防漂移、ABI 版本常量 fail-fast"的哲学相悖。更稳的做法是**把开集变闭集**：

1. **Manifest 里维护显式的"受支持实例化清单"**，作为唯一事实来源。
2. **在一个 shim TU 里对清单每项做显式实例化**：`template class myproj::Container<int>;`。一石二鸟——强制发射稳定符号（bindgen/链接拿得到），且把 ABI 钉死在你控制的地方。
3. **用路径一的 Clang AST pass 做 CI 差异门禁**：扫全库，凡是目标模板的实例化出现了但不在清单里的就**报错**。"用到了没导出的新实例化"从静默漏洞变成响亮的构建失败。

初次接入用路径一/二**生成清单初稿**（把人从手写枚举解放）；之后清单进版本控制，发现工具退居**守门员**。CI 告警频繁、清单膨胀到难维护时，就是该收窄成 `void*` + 类型标签的信号。

```cpp
// shim 专用 TU：显式实例化 + 钉死 ABI，符号稳定可链接
template class myproj::Container<int>;
template class myproj::Container<std::string>;

typedef struct ContainerIntOpaque* ContainerIntHandle;
bool container_int_get(ContainerIntHandle h, size_t idx, int32_t* out);
```
---

# 附录 B：最小完整示例（串起四层）

以"原接口 `cv::Mat MyApi::denoise(const cv::Mat&)`"为例，四层各自的样子：

```cpp
/* L2: shim/img_ffi.h ——只有 C */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
typedef struct MyApiOpaque* MyHandle;
typedef struct ImgOpaque*   ImgHandle;

MyHandle  myapi_create(void);
void      myapi_destroy(MyHandle h);
ImgHandle myapi_img_from_buffer(const uint8_t* data, int rows, int cols, int ch); /* 拷入 */
ImgHandle myapi_denoise(MyHandle h, ImgHandle img);      /* NULL = 失败，查 last_error */
bool      myapi_img_read(ImgHandle img, uint8_t* buf, size_t buf_len,
                          int* rows, int* cols, int* ch);
void      myapi_img_destroy(ImgHandle img);
const char* myapi_last_error(void);
```

```cpp
/* L1: shim/img_ffi.cpp ——C++ 与第三方库的自由世界 */
#include <opencv2/core.hpp>
#include "myapi.h"
#include "img_ffi.h"
static thread_local std::string g_err;

extern "C" ImgHandle myapi_denoise(MyHandle h, ImgHandle img) {
    if (!h || !img) { g_err = "null arg"; return nullptr; }
    try {
        auto& in = *reinterpret_cast<cv::Mat*>(img);
        cv::Mat out = reinterpret_cast<MyApi*>(h)->denoise(in);  // 原接口，零改动
        return reinterpret_cast<ImgHandle>(new cv::Mat(std::move(out)));
    } catch (const std::exception& e) { g_err = e.what(); return nullptr; }
      catch (...) { g_err = "unknown"; return nullptr; }
}
```

```rust
/* L3: src/img.rs ——safe binding */
pub struct Image { h: ImgHandle }
impl Drop for Image { fn drop(&mut self) { unsafe { myapi_img_destroy(self.h) } } }

impl MyApi {
    pub fn denoise(&self, img: &Image) -> Result<Image, Error> {
        let out = unsafe { myapi_denoise(self.h, img.h) };
        if out.is_null() { Err(Error::last()) } else { Ok(Image { h: out }) }
    }
}
```

```rust
/* L4: 业务代码 ——看不见任何 FFI 痕迹 */
let api = MyApi::new()?;
let img = Image::from_buffer(&pixels, 480, 640, 3)?;
let clean = api.denoise(&img)?;
```

`cv::Mat` 在 L1 里正常工作，L2 里不存在，L3 把裸指针包成带 Drop 的 `Image`，L4 写起来和纯 Rust 库没有区别——这就是整套方案要达到的终态。

# C++ Shim 层实践方案:从真实项目出发的 FFI 封装指南

本文档面向为遗留 C++ 项目搭建 Rust FFI 链路的工程实践,回答一个问题:**拿到一个真实的、依赖第三方库的、大量使用 C++ 特性的项目,shim 层到底该怎么写。**

---

## 第一部分:先建立正确的心智模型

### 1.1 四层结构:谁能看见什么

一切实践决策都源自这张分层图。做任何一个接口前,先在脑子里过一遍每层的可见性规则:

```
┌─────────────────────────────────────────────────────────┐
│ L4  Rust 业务代码                                         │
│     只使用 safe binding 的 Rust 类型(String/Vec/Result)   │
├─────────────────────────────────────────────────────────┤
│ L3  safe binding ({project}_sys/src/**.rs)               │
│     持有 raw binding,负责 Drop/Result/生命周期,           │
│     对外只暴露 safe Rust API                              │
├─────────────────────────────────────────────────────────┤
│ L2  shim 头文件 (shim/**_ffi.h)      ★ 唯一的净化点 ★     │
│     只有 C 标准类型:int32_t/size_t/bool/裸指针/            │
│     opaque handle/POD struct。                            │
│     不 include 任何 C++ 头文件、STL、第三方库头文件          │
├─────────────────────────────────────────────────────────┤
│ L1  shim 实现 (shim/**_ffi.cpp) + 原有 C++ 项目            │
│     C++ 的自由世界:STL、Boost、OpenCV、protobuf、          │
│     模板、异常、智能指针……全部照常使用,一行不改             │
└─────────────────────────────────────────────────────────┘
```

三条铁律,全部只约束 L2 这一个文件:

1. **L2 的 include 列表只允许 C 标准头**(`stdint.h`/`stddef.h`/`stdbool.h`)。出现任何 C++ 或第三方头文件即为封装失败。
2. **bindgen 只解析 L2**。因此 bindgen 的 include path 不需要、也不应该配置任何第三方库路径——如果发现 bindgen 跑不通需要加 OpenCV/Boost 的 include path,这本身就是 L2 被污染的报警信号。
3. **L1 不受任何限制**。第三方库照常 include、照常链接、照常调用;原有业务代码一行不改。FFI 封装改变的只是"类型名字能不能穿过语言边界",不是"能不能使用某个库"。

一个常见误解需要在团队内明确澄清:"shim 头文件不能出现第三方类型" ≠ "不能使用第三方库"。库的能力全部保留,只是 `cv::Mat`、`boost::optional` 这些**类型名字**在穿越 Rust/C++ 边界的一瞬间,被 L1 翻译成两边都认识的 C 类型(裸指针 + 基本类型 + 长度),过了边界再由 L3 重新包装成好用的 Rust 类型。

### 1.2 每个接口动手前的五分钟决策流

对着原有接口的每一个函数签名,按顺序问四个问题,答案直接决定写法:

```
Q1: 签名里的每个类型,是不是 C ABI 稳定的?
    (int/float/裸指针/纯 C struct → 是; 其他一切 C++ 类型 → 否)
    │
    ├─ 全部是 → 走【直通模式】: 可能连 shim 都不用写,直接 bindgen 原头文件
    │
    └─ 存在否 → Q2: 这个 C++ 类型,Rust 侧需要"看内容"还是只需要"转手"?
                │
                ├─ 只转手(拿到后原样传给下一个 C++ 接口)
                │    → 走【opaque handle 模式】: 不翻译内容,包成指针透传
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

四种模式覆盖实践中 95% 以上的接口。下面每种模式给出完整可抄的写法。

---

## 第二部分:四种核心模式的标准写法

### 2.1 直通模式:签名本来就是 C ABI 稳定的

原接口如果长这样,不需要写任何 shim 实现:

```cpp
// legacy 项目里本来就有的稳定 C API
extern "C" int foo_version(void);
extern "C" int foo_checksum(const uint8_t* data, size_t len);
```

只需要确认三件事:头文件能被 bindgen 消费(纯 C 语法)、include path 完整、bindgen allowlist 覆盖到目标符号。这对应 Manifest 里 `C ABI Shims=none` + Reason 注明 direct bindgen 的情况——注意 direct bindgen 只免除手写 shim,**不免除 L3 safe binding**:raw binding 仍然要私有化,对外仍然要包一层 safe API。

**实践判断技巧**:很多 C++ 项目会有一部分"C 风格核心 + C++ 便利封装"的分层。优先找到 C 风格核心层直通,比逐个翻译 C++ 便利层划算得多。用 GitNexus `context` 查一下 C++ 便利函数的实现,经常会发现它只是薄薄一层转发。

### 2.2 拍平模式:值语义数据的双向翻译

适用于:字符串、数值数组、简单结构体、`optional`、小型 map——所有"Rust 侧真正需要读写其内容"的值类型数据。

**方向一(Rust → C++,输入参数):指针+长度进,shim 内现场构造**

这是最简单、最零风险的方向,固定模板:

```cpp
// shim.h
extern "C" bool myapi_load(MyHandle h,
                            const char* path, size_t path_len,      // ← std::string
                            const int32_t* ids, size_t ids_len);    // ← std::vector<int>
```

```cpp
// shim.cpp
#include "myapi.h"       // 原有 C++ 接口,含 STL 签名,照常 include
#include "myapi_ffi.h"

extern "C" bool myapi_load(MyHandle h, const char* path, size_t path_len,
                            const int32_t* ids, size_t ids_len) {
    if (!h || (!path && path_len) || (!ids && ids_len)) return false;  // 判空防御
    try {
        std::string s(path, path_len);                 // 局部构造,函数返回自动析构
        std::vector<int> v(ids, ids + ids_len);
        return static_cast<MyApi*>(h)->load(s, v);     // 调原接口,一行不改
    } catch (...) { return false; }
}
```

实践要点:

- 字符串**永远传 `(ptr, len)` 对**而不是 NUL 结尾——Rust 的 `&str` 天然是胖指针,`s.as_ptr(), s.len()` 零成本;而 `CString` 转换要多一次分配还要处理内部 NUL 错误。
- STL 对象作为 shim 函数的**局部变量**,生命周期在函数体内闭合,不需要任何跨边界的内存管理——这是拍平模式输入方向零心智负担的原因。

**方向二(C++ → Rust,输出),按数据大小二选一:**

小而定长 → 调用者提供缓冲区(无堆分配,适合高频调用):

```cpp
// shim.h — 两段式:先问大小,再填数据
extern "C" size_t myapi_get_name_len(MyHandle h);
extern "C" bool   myapi_get_name(MyHandle h, char* buf, size_t buf_len);
```

变长/复杂 → C++ 分配 + 导出配对 free(灵活,适合低频大数据):

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

**内存配对铁律**:分配和释放必须发生在同一侧。C++ `malloc`/`new` 的内存只能由 C++ 侧导出的 free 函数释放,Rust 绝不能用 `Box::from_raw`/`Vec::from_raw_parts` 接管;反之 Rust 分配的缓冲区 C++ 侧只能写入、不能释放。L3 safe binding 用 RAII 兜底:

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

**特殊值类型的拍平对照表:**

| 原类型 | 拍平后的 C ABI 形式 |
|---|---|
| `std::optional<T>` | `bool` 返回值 + `T* out` 参数;或 `has_value` 字段的 POD struct |
| `std::variant<A,B>` | `enum tag` + union/平行字段的 POD struct |
| `std::map<K,V>` | 平行数组 `(K* keys, V* vals, size_t len)` 或 `struct{K;V;}` 数组 |
| `std::pair<A,B>` | 两个 out 参数,或 POD struct |
| `enum class E` | shim.h 重新声明 C enum,.cpp 里 `static_assert` 数值一致 |
| `bool`(签名里的) | 保留 bool(C99 起稳定),或保守用 `int32_t`,统一即可 |
| `std::string_view` 输入 | `(const char*, size_t)`,和 string 一样 |

### 2.3 opaque handle 模式:资源、大对象、第三方类型的透传

适用于:带析构逻辑的对象、内含 STL/第三方成员的类、只在 C++ 接口之间流转不需要 Rust 读内容的类型。这是实践中用得最多的模式。

**基础形态:create/destroy 配对**

```cpp
// shim.h
typedef struct MyApiOpaque MyApiOpaque;      // 不完整类型,布局不可见
typedef MyApiOpaque* MyHandle;

extern "C" MyHandle myapi_create(const char* cfg, size_t cfg_len);
extern "C" void     myapi_destroy(MyHandle h);   // 允许 h == NULL,幂等
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
// 默认不实现 Send/Sync,除非确认了线程安全性(见 3.4)
```

**变体一:原接口返回 `std::shared_ptr<T>`(共享所有权)**

handle 指向的不是 T 本身,而是堆上多包一层的 shared_ptr 壳,用壳的生命周期控制引用计数:

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

**变体二:第三方类型在接口间流转(如 `cv::Mat` 贯穿多个函数)**

不要每次跨边界都拍平——把第三方对象本身包成 handle 透传,只在真正需要读数据的终点提供提取函数:

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

Rust 侧串联 `load → denoise → sharpen → read` 时,中间结果只是 handle 在转手,没有任何像素数据的拷贝和翻译,性能与纯 C++ 调用链几乎一致。**这是处理"接口签名依赖第三方类型"的首选答案**:第三方类型不需要翻译,只需要藏起来。

**变体三:类成员里有第三方/STL 类型**

```cpp
class MyProcessor {
    cv::Mat cache_;                    // 成员含第三方类型
    std::vector<Result> history_;
public: ...
};
```

不需要任何特殊处理——opaque handle 隐藏的是**整个对象的布局**,成员里有什么与 Rust 无关。只有当 Rust 需要读取某个成员时,才为那个成员单独加一个提取函数(按 2.2 拍平)。如果原类已经是 pimpl 设计,连壳都不用包,pimpl 指针直接当 handle 用。

### 2.4 字节流模式:有 schema 的复杂结构

适用于:protobuf 消息、JSON 可表达的配置/结果对象、任何"两侧都能按同一 schema 解析"的复杂嵌套数据。

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

Rust 侧用 `prost` 从同一份 `.proto` 生成结构体,两边不共享任何 C++ 类型,只共享 schema 和字节流。**选择判据**:结构嵌套超过两层、字段超过十个、或者未来还会加字段——手写 POD struct 拍平的维护成本会迅速超过一次序列化的运行时开销,直接上字节流。反之,三五个字段的扁平结构,POD struct 拍平更直接。

---

## 第三部分:横切问题的统一处理

以下问题不属于某种模式,而是**所有 shim 函数都要过一遍**的检查项。

### 3.1 异常:每个导出函数无一例外

C++ 异常穿越 `extern "C"` 边界是 UB。团队约定:**shim.cpp 里每一个导出函数体,第一层就是 try/catch**,没有"这个函数肯定不抛"的豁免——第三方库升级、意外输入都可能引入新异常路径。

需要错误详情时,统一用线程局部错误槽,全项目一份:

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

### 3.2 回调:函数指针 + user_data + trampoline

原接口的 `std::function`/lambda 参数,shim 一律降级为 C 经典模式:

```cpp
// shim.h
typedef void (*MyCallback)(int32_t event, void* user_data);
extern "C" bool myapi_set_callback(MyHandle h, MyCallback cb, void* user_data);
extern "C" void myapi_clear_callback(MyHandle h);   // 必须提供,否则 Rust 侧闭包无法安全回收
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
// L3: Box 闭包 + trampoline,生命周期与 wrapper 绑定
pub struct MyApi { handle: MyHandle, cb: Option<Box<Box<dyn Fn(i32)>>> }

extern "C" fn trampoline(event: i32, ud: *mut c_void) {
    let f = unsafe { &*(ud as *const Box<dyn Fn(i32)>) };
    f(event);
}
impl MyApi {
    pub fn set_callback(&mut self, f: impl Fn(i32) + 'static) {
        let boxed: Box<Box<dyn Fn(i32)>> = Box::new(Box::new(f));
        unsafe { myapi_set_callback(self.handle, trampoline,
                                     &*boxed as *const _ as *mut c_void); }
        self.cb = Some(boxed);   // wrapper 持有,Drop 时先 clear_callback 再释放
    }
}
```

三个必答题写进代码注释:回调可能在哪个线程触发?对象销毁后回调是否还可能到达(必须保证不会)?回调内部再调 API 会不会死锁?——这三个问题的答案要从 L1 源码确认,GitNexus `context` 查回调的触发点是有效手段。

### 3.3 重载、模板、命名空间:符号名的拍平规则

C ABI 符号必须全局唯一且无 mangling,统一命名公式:

```
{target_stem}_{动作}[_{类型区分后缀}]
```

| 原接口 | shim 导出 |
|---|---|
| `parse(const std::string&)` / `parse(const uint8_t*, size_t)` 重载 | `json_parse_str` / `json_parse_bytes` |
| `Stack<int>` / `Stack<std::string>` 模板实例 | `stack_int_*` / `stack_str_*`(只导出实际用到的实例化,永不导出模板本身) |
| `myproj::parser::Json::dump()` | `parser_json_dump`(命名空间拍进前缀) |
| `operator==` / `operator[]` / `operator<<` | `foo_equals` / `foo_get_at` / `foo_to_string` |

### 3.4 线程与全局状态:标注重于加锁

- 每个导出函数在 shim.h 注释里标注线程安全等级:`// thread-safe` / `// requires external sync` / `// main-thread only`。这个信息必须从 L1 源码确认(查全局变量、`thread_local`、单例的使用),不能猜。
- L3 用类型系统落实标注:非线程安全的 handle wrapper **不实现 `Send`/`Sync`**(默认行为,保持即可);确认线程安全后才手动 `unsafe impl Send`。让编译器阻止误用,比文档提醒可靠。
- 单例/全局 init 类接口,显式导出 `xxx_global_init()`/`xxx_global_shutdown()`,调用顺序约束写注释;不要在 shim 里悄悄隐藏"第一次调用才初始化"的副作用。
- 慎用"shim 层全局加锁"来制造线程安全——锁粒度决策留给 L3(`Mutex<MyApi>`),Rust 侧可见可控,C++ 侧的隐藏锁排查死锁时是灾难。

### 3.5 字符串编码:边界外统一 UTF-8

shim 边界上的所有字符串一律 UTF-8 + `(ptr, len)`。原接口用 `std::wstring`/`wchar_t`(注意平台宽度差异:Windows 16 位,Linux 32 位)或本地编码(GBK 等)的,转换收敛在 shim.cpp 内完成,不把编码问题泄漏给 Rust 侧。L3 收到字节后用 `String::from_utf8_lossy` 或严格校验,取决于数据源可信度。

---

## 第四部分:第三方库依赖的工程处理

### 4.1 接口签名依赖第三方类型:按位置套模式

原有 API 头文件里出现 `cv::Mat`、`boost::optional`、`Eigen::MatrixXd` 时,不需要新理论,按类型出现的位置套用第二部分的模式:

| 第三方类型出现位置 | 套用模式 | 说明 |
|---|---|---|
| 输入参数 | 拍平(2.2 方向一) | shim.cpp 内用裸数据现场构造第三方对象;优先用零拷贝构造(`cv::Mat(rows,cols,type,ptr)`、`Eigen::Map`) |
| 按值返回 | 拍平(2.2 方向二) | 对象生命周期在 shim 函数内闭合,数据搬出即可 |
| 智能指针返回 | opaque handle 变体一 | 包 shared_ptr 壳,不暴露第三方类型布局 |
| 在多个接口间流转 | opaque handle 变体二 | 透传 handle,终点才提取,避免反复翻译 |
| 你的类的成员 | opaque handle 变体三 | 整对象作 handle,成员与 Rust 无关 |
| protobuf 消息 | 字节流(2.4) | 两侧共享 .proto,不共享 C++ 类型 |

零拷贝构造的坑要写进注释:例如 Eigen 默认列主序、C 数组直觉是行主序,约定不一致时**数值错位但不报错**,必须在 shim.h 里注明 `// row-major` 并在 smoke test 里用非对称矩阵验证。

### 4.2 例外:第三方库本身是稳定 C ABI

zlib、SQLite、libcurl 这类纯 C 库的类型(如 `z_stream`)是稳定 C 结构,可以直接 bindgen 它们的头文件,不需要在 shim 里转手。判断标准:库的头文件本身能用纯 C 编译器编译通过,且供应商有跨版本 ABI 承诺。拿不准就当不稳定处理——多包一层 handle 的成本远低于一次布局漂移的排查成本。

### 4.3 build.rs:两条 include path 必须分开

这是本场景下最高频的实操坑。`cc::Build`(编译 shim.cpp)和 `bindgen`(解析 shim.h)的 include path 职责完全不同:

```rust
fn main() {
    // ① cc::Build 编译 L1,需要第三方库的一切
    cc::Build::new()
        .cpp(true).std("c++17")
        .include("shim")
        .include(legacy_root.join("include"))
        .include("/usr/include/opencv4")            // 第三方 include 只在这里
        .files(shim_sources)
        .files(legacy_sources_needed)                // Step 2 依赖分析确定的 legacy 源文件
        .compile("myapi_shim");

    // ② 链接第三方库
    println!("cargo:rustc-link-lib=opencv_core");
    println!("cargo:rustc-link-lib=stdc++");         // 或 macOS: c++

    // ③ bindgen 只看 L2,不需要任何第三方路径
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

**自检信号**:③ 如果报"找不到 opencv2/core.hpp",不是去给 bindgen 加 include path,而是回头检查 shim.h——它被污染了。

### 4.4 版本锁定

第三方库版本漂移会让"同一份代码在不同机器行为不同":

- 能 vendoring 就 vendoring(源码进仓库或 git submodule 锁定 commit)。
- 只能链接系统库时,在 shim.cpp 里用版本宏做编译期拦截:
  ```cpp
  #include <opencv2/core/version.hpp>
  static_assert(CV_VERSION_MAJOR == 4, "requires OpenCV 4.x");
  ```
- 版本要求写进 Manifest 对应条目的 Reason 和 README,CI 环境固定版本。

---

## 第五部分:落地清单

### 5.1 单个接口的实施步骤

1. **读签名,跑决策流**(1.2):确定模式,把结论写进 Manifest Reason。
2. **确认五个语义**再写代码:参数/返回值的所有权、错误表达方式、空指针语义、线程约束、expected 来源。任何一项从源码确认不了 → 回读证据或问人,不猜。
3. **写 shim.h**:只用 C 标准类型,每个函数注释写清所有权和空指针语义。
4. **写 shim.cpp**:include 原头文件和第三方头文件,套 SHIM_GUARD 宏,判空,类型翻译,调原接口。
5. **写 L3 safe binding**:raw binding 私有化,Drop/Result/类型标注,unsafe 集中在 crate 内部。
6. **写 smoke test**:一条成功路径 + 一条错误路径,expected 来自源码/spec/测试等可信来源。
7. **build + test 通过后**才更新 Manifest 状态。

### 5.2 shim 代码评审 checklist

| # | 检查项 | 不合格的典型症状 |
|---|---|---|
| 1 | shim.h 的 include 只有 C 标准头 | 出现 `<string>`/`<opencv2/...>`/项目内部 C++ 头 |
| 2 | 每个导出函数有 try/catch 全包裹 | "这个函数不会抛"的口头豁免 |
| 3 | 每个 create 有配对 destroy,每个 alloc 有配对 free | 返回 `char*` 但找不到对应释放函数 |
| 4 | 分配与释放在同一侧 | Rust 里出现 `Box::from_raw` 接管 C++ 内存 |
| 5 | 所有指针入参有判空 | 直接解引用参数 |
| 6 | 字符串是 (ptr,len),编码 UTF-8 | 依赖 NUL 结尾;wchar_t 泄漏到 shim.h |
| 7 | enum 有 static_assert 数值校验 | shim.h 手抄枚举值,无编译期比对 |
| 8 | 线程安全等级有注释,L3 的 Send/Sync 与之一致 | wrapper 默认被 `unsafe impl Send` |
| 9 | 回调有注销函数,闭包生命周期由 wrapper 持有 | set 了回调但对象销毁后回调仍可能触发 |
| 10 | bindgen 不需要第三方 include path 即可通过 | build.rs 里 bindgen 配了 opencv 路径 |

### 5.3 反模式速查

| 反模式 | 为什么错 | 正确做法 |
|---|---|---|
| 因为接口依赖第三方类型而认为"没法做 FFI" | 混淆了"使用库"和"暴露类型" | 类型藏进 L1,套 4.1 的位置对照表 |
| bindgen 直接解析含 STL/第三方类型的原头文件 | 赌 ABI,换编译器即炸 | bindgen 只解析净化过的 shim.h |
| 每次跨边界都把大对象拍平成数组 | 无谓拷贝,接口爆炸 | 流转用 opaque handle,终点才提取 |
| 为通过 smoke test 放宽断言/吞掉错误 | 掩盖 FFI/生命周期真实问题 | 修问题本身;expected 不可信就停下确认 |
| shim 里悄悄全局加锁"保证"线程安全 | 隐藏锁,死锁难排查 | 标注等级,锁的决策上移到 L3 |
| 手写 POD struct 拍平十几个字段的嵌套结构 | 维护成本失控,加字段两边改 | 上字节流模式,schema 驱动 |
| 导出模板/公开全部 raw bindgen 符号 | 无稳定符号/unsafe 面失控 | 只导出具体实例化;raw binding 私有化 |

---

## 附:最小完整示例(串起四层)

以"原接口 `cv::Mat MyApi::denoise(const cv::Mat&)`"为例,四层各自的样子:

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
ImgHandle myapi_denoise(MyHandle h, ImgHandle img);      /* NULL = 失败,查 last_error */
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
        cv::Mat out = reinterpret_cast<MyApi*>(h)->denoise(in);  // 原接口,零改动
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

`cv::Mat` 在 L1 里正常工作,L2 里不存在,L3 把裸指针包成带 Drop 的 `Image`,L4 写起来和纯 Rust 库没有区别——这就是整套方案要达到的终态。

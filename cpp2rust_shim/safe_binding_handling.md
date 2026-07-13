# Safe Binding 原始指针处理赋能文档

> 适用范围：`{project_name}_sys` sys crate 中，基于 bindgen 产物编写 Rust safe binding 时，如何处理来自 C/C++ shim 的原始指针参数与返回值。

---

## 0. 核心原则

safe binding 层存在的唯一目的：**把裸指针的语义"翻译"成 Rust 类型系统能表达的安全约束**，让 unsafe 只留在 sys crate 内部的桥接代码里，调用方（测试、上层业务代码）不需要、也不应该直接接触裸指针。

处理任何一个原始指针参数或返回值之前，必须先回答 5 个问题：

| 问题 | 目的 |
|------|------|
| 这个指针代表什么？（句柄 / 数组首地址 / 字符串 / 可选值 / 回调上下文） | 决定映射到哪种 Rust 类型 |
| 谁分配、谁释放？ | 决定是否需要 `Drop`，以及释放函数是谁 |
| 指针指向的内存生命周期覆盖多久？ | 决定用借用（`&T`）还是拥有（owned wrapper） |
| 是否允许为空？ | 决定是否用 `Option<T>` |
| 是否有并发/重入约束？ | 决定是否需要 guard、`!Send`/`!Sync` 标记 |

这 5 个问题的答案必须来自 C/C++ API 契约、头文件注释、源码实现或用户确认，**不能猜测**——这与 skill 中"expected 必须有可信来源"的原则一致，指针语义同样属于必须回读证据的范畴。

---

## 1. 决策树：这个指针该映射成什么 Rust 类型

```mermaid
flowchart TD
    A[C 侧原始指针参数/返回值] --> B{代表单个不透明对象?}
    B -->|是| B1{谁负责释放?}
    B1 -->|Rust侧持有并需释放| B2[owned wrapper + Drop]
    B1 -->|仅借用，生命周期不归Rust管| B3[&T / &mut T 借用包装]
    B -->|否| C{代表连续内存 buffer?}
    C -->|是，带长度| C1{Rust侧拥有内存?}
    C1 -->|是| C2[owned buffer wrapper + Drop]
    C1 -->|否，只是查看| C3[&[u8] / &mut [u8]]
    C -->|否| D{代表 NUL 结尾字符串?}
    D -->|是| D1{所有权归C，需专门free?}
    D1 -->|是| D2[owned CStr wrapper + Drop]
    D1 -->|否，借用即可| D3[即时转 &str/String，不长期持有]
    D -->|否| E{可能为 NULL 表示可选?}
    E -->|是| E1[Option<T> 包装对应类型]
    E -->|否| F{代表回调上下文 void*?}
    F -->|是| F1[闭包 + trampoline，userdata 内部管理]
    F -->|否| G[人工评估：可能需要暴露受限 unsafe API]
```

---

## 2. 五类典型指针的处理模式

### 2.1 不透明对象句柄（Opaque Handle）

**场景**：`Parser* parser_create(...)` / `void parser_destroy(Parser*)`，C++ 对象通过 handle 跨 FFI 暴露。

**处理原则**：
- 用 tuple struct 包裹 `NonNull<CType>`，字段私有，禁止外部构造
- 构造函数返回 `Result<Self, Error>`，内部做空指针检查
- 实现 `Drop`，调用对应释放函数；如果 C 侧允许重复释放或有"已释放"状态，需要在 wrapper 内维护标记避免 UB
- 所有后续操作都是 `&self` / `&mut self` 方法，内部临时取出裸指针传给 raw binding，方法本身不是 `unsafe`

```rust
use std::ptr::NonNull;

pub struct Parser(NonNull<sys::CParser>);

impl Parser {
    pub fn new() -> Result<Self, Error> {
        // SAFETY: parser_create 是纯 C ABI 调用，无前置条件
        let ptr = unsafe { sys::parser_create() };
        NonNull::new(ptr)
            .map(Parser)
            .ok_or(Error::CreateFailed)
    }

    pub fn parse(&mut self, input: &str) -> Result<(), Error> {
        let c_input = CString::new(input).map_err(|_| Error::InvalidInput)?;
        // SAFETY: self.0 在整个对象生命周期内保证非空且有效；
        // c_input 在本次调用期间存活，parser_parse 不保留其指针
        let rc = unsafe { sys::parser_parse(self.0.as_ptr(), c_input.as_ptr()) };
        Error::from_code(rc)
    }
}

impl Drop for Parser {
    fn drop(&mut self) {
        // SAFETY: self.0 由 new() 保证非空、由本对象独占所有权，
        // Drop 只会被调用一次（Rust 所有权系统保证）
        unsafe { sys::parser_destroy(self.0.as_ptr()) };
    }
}
```

**易错点**：
- 忘记 `NonNull` 校验，直接把可能为 null 的裸指针包进 wrapper
- `Drop` 中裸指针悬垂（构造失败路径没有正确处理，导致析构未初始化对象）
- 多个 wrapper 共享同一裸指针（违反 Rust 唯一所有权假设）→ 若 C 侧确实是引用计数对象，应改用内部 `Arc`-like 计数或 C 侧自身的 refcount API，不能简单 `Clone` 裸指针

---

### 2.2 连续内存 Buffer（`const uint8_t* data, size_t len`）

**场景**：读写字节数组、序列化输出等。

**处理原则**：
- **输入方向**（Rust → C）：直接用 `&[u8]` / `&str`，内部转 `.as_ptr()` + `.len()`；不新增分配
- **输出方向，C 借出内存给 Rust 查看**：用 `&[u8]`，且必须明确这个 slice 的生命周期不能超过对应 C 对象的生命周期（用 Rust 生命周期参数绑定到宿主对象的 `&self`）
- **输出方向，C 分配内存交给 Rust 拥有**：包成 owned buffer wrapper，`Drop` 里调用对应 `_free`

```rust
// 输入：只读借用，无需 unsafe 对外暴露
pub fn read_bytes(&self, data: &[u8]) -> Result<i32, Error> {
    // SAFETY: data 的指针和长度在本次调用期间一致有效，
    // read_bytes 不持有该指针超出调用范围
    let rc = unsafe { sys::read_bytes(self.0.as_ptr(), data.as_ptr(), data.len()) };
    Error::from_code(rc)
}

// 输出：C 侧分配、需要专门释放函数
pub struct OwnedBuffer {
    ptr: NonNull<u8>,
    len: usize,
}

impl OwnedBuffer {
    pub fn as_slice(&self) -> &[u8] {
        // SAFETY: ptr 和 len 由构造函数从 C 侧一次性获取，
        // 期间未发生写入，且生命周期不超过 self
        unsafe { std::slice::from_raw_parts(self.ptr.as_ptr(), self.len) }
    }
}

impl Drop for OwnedBuffer {
    fn drop(&mut self) {
        unsafe { sys::buffer_free(self.ptr.as_ptr(), self.len) };
    }
}
```

**易错点**：
- 借用型 buffer 没有绑定生命周期参数，导致 Rust 侧可以在宿主对象释放后继续持有 slice（悬垂引用）
- owned buffer 释放时用错释放函数（例如用 `free` 释放 C++ `new[]` 分配的内存）
- 长度单位不一致（字节数 vs 元素个数），必须在函数注释和 shim 头文件注释中明确

---

### 2.3 NUL 结尾字符串（`const char*`）

**处理原则**：

| 场景 | 处理方式 |
|------|----------|
| Rust → C，传入字符串 | `CString::new(s)?`，**必须绑定到变量**再 `.as_ptr()`，禁止 `CString::new(s)?.as_ptr()` 链式写法（临时值提前 drop 导致悬垂指针） |
| C → Rust，借用只读字符串（C 侧继续持有，Rust 不释放） | 立即 `unsafe { CStr::from_ptr(ptr) }.to_str()?.to_owned()`，转成 `String` 后不再持有裸指针；不要把 `&CStr` 长期存到结构体里 |
| C → Rust，C 侧分配、需要专门 free 的字符串 | 包成 owned wrapper（类似 2.1），`Drop` 时调用对应 `_free_string`，`as_str()` 方法内部按需转换 |

```rust
pub fn set_name(&mut self, name: &str) -> Result<(), Error> {
    let c_name = CString::new(name).map_err(|_| Error::InvalidInput)?; // 绑定变量
    // SAFETY: c_name 在本次调用期间存活；set_name 内部会拷贝字符串内容，
    // 不保留传入指针（已通过头文件注释确认）
    let rc = unsafe { sys::parser_set_name(self.0.as_ptr(), c_name.as_ptr()) };
    Error::from_code(rc)
}

pub fn last_error(&self) -> Option<String> {
    // SAFETY: parser_last_error 返回的指针要么为 NULL，要么指向一个
    // 生命周期覆盖到下一次 API 调用之前的只读 C 字符串（已在头文件确认）
    let ptr = unsafe { sys::parser_last_error(self.0.as_ptr()) };
    if ptr.is_null() {
        return None;
    }
    let s = unsafe { CStr::from_ptr(ptr) }.to_string_lossy().into_owned();
    Some(s)
}
```

**易错点**：
- 传入字符串含内部 NUL 字节，`CString::new` 会返回 `Err`，必须处理而不是 `unwrap`
- 借用字符串在下一次 API 调用后失效（很多 C 库用同一块静态 buffer 返回错误信息），必须立即拷贝成 owned `String`，不能延迟读取

---

### 2.4 可选指针（Nullable，表达 Optional 语义）

**处理原则**：
- 参数层面：`Option<&T>` → 内部转换成 `ptr::null()` 或有效指针
- 返回层面：先判空，再包装成 `Option<T>` 或 `Option<Wrapper>`

```rust
pub fn find(&self, key: &str) -> Result<Option<Value>, Error> {
    let c_key = CString::new(key).map_err(|_| Error::InvalidInput)?;
    // SAFETY: 见 2.1/2.3 说明；find 返回 NULL 表示未找到，非 NULL 时
    // 返回一个新分配对象，所有权转移给调用者
    let ptr = unsafe { sys::map_find(self.0.as_ptr(), c_key.as_ptr()) };
    Ok(NonNull::new(ptr).map(Value))
}

pub fn set_parent(&mut self, parent: Option<&Node>) {
    let raw = parent.map_or(std::ptr::null(), |p| p.as_raw());
    unsafe { sys::node_set_parent(self.0.as_ptr(), raw) };
}
```

**易错点**：
- 只在返回值判空，忘记参数方向也可能需要传 null（很多 C API 用 `NULL` 表示"使用默认值"）

---

### 2.5 回调上下文 / `void* userdata`

**场景**：C API 接受函数指针 + `void*` userdata 做回调注册，典型于事件监听、进度回调。

**处理原则**：
- 提供接受 Rust 闭包的 safe 接口，内部把闭包装箱（`Box<dyn FnMut(...)>`）后把裸指针存入 `void* userdata`
- 提供一个 `extern "C"` trampoline 函数，签名匹配 C 侧要求，内部把 `userdata` 转回 `Box`，调用闭包
- 必须保证闭包的生命周期覆盖回调可能被触发的整个期间；如果注册和触发是异步的，闭包需要 `'static` 约束
- 注销/销毁时必须回收 `Box`，避免内存泄漏；如果 C 侧没有显式注销接口，需要在文档中说明这是已知限制

```rust
type BoxedCallback = Box<dyn FnMut(i32) + 'static>;

extern "C" fn trampoline(value: i32, userdata: *mut c_void) {
    // SAFETY: userdata 由 register_callback 设置，
    // 生命周期由返回的 CallbackHandle 管理，触发前不会被提前释放
    let cb = unsafe { &mut *(userdata as *mut BoxedCallback) };
    cb(value);
}

pub struct CallbackHandle {
    raw: *mut BoxedCallback,
}

impl Parser {
    pub fn on_event(&mut self, f: impl FnMut(i32) + 'static) -> CallbackHandle {
        let boxed: Box<BoxedCallback> = Box::new(Box::new(f));
        let raw = Box::into_raw(boxed);
        unsafe {
            sys::parser_register_callback(self.0.as_ptr(), Some(trampoline), raw as *mut c_void)
        };
        CallbackHandle { raw }
    }
}

impl Drop for CallbackHandle {
    fn drop(&mut self) {
        // SAFETY: raw 由 on_event 通过 Box::into_raw 产生，且只会被
        // CallbackHandle 释放一次
        unsafe { drop(Box::from_raw(self.raw)) };
    }
}
```

**易错点**：
- 忘记 `'static` 约束，闭包捕获了会先于回调触发而失效的局部变量
- `Box::into_raw` 之后没有对应的 `Box::from_raw` 回收路径
- 多线程回调时闭包内部访问了非 `Send` 数据

---

## 3. 什么情况下才允许对外暴露 `unsafe fn`

原则：**能用 safe wrapper 表达的 API 不应该暴露为 `unsafe`**。只有以下情况才考虑暴露 `unsafe`：

- 需要和其他 FFI 系统/宿主环境对接，调用方必须拿到裸指针本身（例如嵌入到另一个绑定层）
- 性能极端敏感路径，safe 包装引入的检查/拷贝不可接受，且已有充分证据（不是猜测）
- C API 本身的前置条件无法在类型系统中表达（例如"必须在特定线程调用"），safe wrapper 无法兜底

暴露时必须满足的强制要求（对应 skill 中的自检项）：

```rust
/// 返回底层 C 对象的裸指针，供与 XxxSDK 的外部 FFI 层对接使用。
///
/// # Safety
/// - 返回的指针在 `self` 存活期间保证非空且有效；
///   调用者不得在 `self` 被 drop 后继续使用该指针
/// - 调用者不得对返回的指针调用任何释放函数（所有权仍归 `self`）
/// - 调用者不得在持有该指针期间从其他线程调用 `self` 的 `&mut` 方法
///   （对象内部无同步保护）
pub unsafe fn raw_handle(&self) -> *mut sys::CParser {
    self.0.as_ptr()
}
```

`# Safety` 注释必须覆盖：指针有效性范围、生命周期约束、所有权是否转移及由谁释放、是否允许重复释放/空指针、并发访问限制。缺失任意一项，必须先补充再继续，不能只在报告里声明"已检查"。

---

## 4. 自检清单（生成/修改 safe binding 后逐项核对）

| 检查项 | 合格标准 |
|--------|----------|
| 类型映射 | 每个裸指针参数/返回值都已按第 1 节决策树映射为对应安全类型，没有裸指针原样穿透到公开签名（除非属于第 3 节允许场景） |
| 所有权 | owned 资源都有对应 `Drop` 或显式 `close`/`free`，释放函数与分配函数一一对应，不存在双重释放风险 |
| 借用生命周期 | 借用型返回值（slice、`&str`）的生命周期已正确绑定到宿主对象，不能在宿主释放后继续访问 |
| 字符串绑定 | 所有 `CString` 构造都绑定到具名变量后再取指针，没有链式临时值写法 |
| 空指针 | 每个可能为 NULL 的参数/返回值都已用 `Option<T>` 表达，构造路径有显式判空 |
| 回调生命周期 | 回调闭包生命周期覆盖已确认，`Box::into_raw` 均有对应回收路径 |
| unsafe 边界 | 公开 API 中不存在可以用 safe wrapper 替代却仍标 `unsafe` 的函数 |
| unsafe 注释 | 每个确需暴露的 `unsafe fn` 都有完整 `# Safety` 说明（有效性/生命周期/所有权/并发） |
| 错误路径 | 分配失败、错误码返回都已转换为 `Result`，没有在错误路径遗漏资源释放 |

---

## 5. 速查表

| 裸指针语义 | Rust safe 类型 | 关键动作 |
|-----------|----------------|----------|
| 不透明对象句柄，Rust 拥有 | `struct Wrapper(NonNull<T>)` | 实现 `Drop`，方法内部临时取指针 |
| 不透明对象句柄，仅借用 | `&T` / `&mut T`（生命周期绑定宿主） | 不实现 `Drop`，禁止跨宿主生命周期持有 |
| 输入 buffer | `&[u8]` / `&str` | 直接 `.as_ptr()` + `.len()`，无需分配 |
| 输出 buffer，C 分配需释放 | owned wrapper + `Drop` | 记录长度，`as_slice()` 内部 `from_raw_parts` |
| 输出字符串，C 借用 | 立即转 `String`/`&str` | 不持有裸指针，防止下次调用后失效 |
| 输出字符串，C 分配需释放 | owned wrapper + `Drop` | 调用专门 `_free_string` |
| 可能为空的指针 | `Option<T>` | 构造/返回路径显式判空 |
| 回调 `void* userdata` | 闭包 + `extern "C"` trampoline | `Box::into_raw`/`Box::from_raw` 配对 |
| 必须暴露裸指针（罕见） | `unsafe fn` | 完整 `# Safety` 注释，覆盖有效性/生命周期/所有权/并发 |

# 代码测试覆盖率赋能文档

GCC 与 Clang/LLVM 体系完整指南 | 版本 3.0 | 适用 GCC ≥ 9.x，Clang/LLVM ≥ 12.x

---

## 目录

1. [基本概念](#1-基本概念)
2. [GCC 覆盖率体系](#2-gcc-覆盖率体系)
   - 2.1 工具链数据流
   - 2.2 编译设置
   - 2.3 运行与收集
   - 2.4 分支覆盖率专项
   - 2.5 过滤不需要的部分
   - 2.6 常见问题排查
3. [Clang/LLVM 覆盖率体系](#3-clangllvm-覆盖率体系)
   - 3.1 插桩原理与运行时依赖
   - 3.2 编译设置
   - 3.3 运行与收集
   - 3.4 过滤不需要的部分
   - 3.5 常见问题排查
4. [两大体系对比](#4-两大体系对比)
5. [构建系统集成](#5-构建系统集成)
   - 5.1 CMake
   - 5.2 Makefile
6. [CI/CD 集成](#6-cicd-集成)
7. [快速命令速查](#7-快速命令速查)

---

## 1 基本概念

**测试覆盖率（Code Coverage）** 衡量测试用例覆盖源代码的程度，帮助团队找出未被测试触达的代码路径。

| 覆盖率类型 | 说明 | GCC | Clang |
|-----------|------|:---:|:-----:|
| **行覆盖（Line）** | 哪些源码行被执行过 | ✓ | ✓ |
| **函数覆盖（Function）** | 哪些函数被调用过 | ✓ | ✓ |
| **分支覆盖（Branch）** | if/switch/&&/\|\| 每条路径是否都被触发 | ✓ | ✓ |
| **区域覆盖（Region）** | 比行更细的代码区块，能区分宏展开与模板实例 | — | ✓ |
| **MC/DC** | 每个条件独立影响决策结果的覆盖（航空/嵌入式标准） | — | ✓（GCC ≥ 14.2 也支持） |

---

## 2 GCC 覆盖率体系

### 2.1 工具链数据流

```
源代码
  │
  ├─[编译: --coverage]──► .gcno  （控制流图注记，编译时生成）
  │
  └─[运行]──────────────► .gcda  （执行计数，程序退出时写入，多次运行自动累积）
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
               gcov -b              lcov --capture
             .gcov 文本              coverage.info
                                         │
                                    genhtml
                                    HTML 报告
```

### 2.2 编译设置

`--coverage` 是核心标志（等价于 `-fprofile-arcs -ftest-coverage`），**编译和链接阶段都必须加**。

```bash
# C 单文件
gcc --coverage -O0 -g -o my_program my_program.c

# C++ 多文件
g++ --coverage -O0 -g -std=c++17 -o my_app main.cpp utils.cpp

# 分步编译（链接时同样需要 --coverage）
g++ --coverage -O0 -g -c file1.cpp -o file1.o
g++ --coverage -O0 -g -c file2.cpp -o file2.o
g++ --coverage -O0 -g file1.o file2.o -o my_app
```

| 选项 | 作用 |
|------|------|
| `--coverage` | 等价于 `-fprofile-arcs -ftest-coverage`，插入计数器并生成控制流注记 |
| `-O0` | 禁用优化，防止编译器消除分支导致覆盖率数据失真 |
| `-g` | 保留调试信息，报告能精确映射到源码行号 |
| `-fprofile-update=atomic` | 多线程场景下原子写 `.gcda`，防止数据竞争损坏 |

### 2.3 运行与收集

程序正常退出时自动写 `.gcda`；多次运行数据自动累积叠加：

```bash
./my_app
./my_tests --gtest_filter='*'

# 多场景运行，覆盖率数据累积
./my_app --input case1.txt
./my_app --input case2.txt
```

**程序崩溃时 `.gcda` 不落盘**，需在信号处理中手动刷写：

```c
#include <signal.h>

// GCC < 11
extern void __gcov_flush(void);
// GCC >= 11（推荐）
extern void __gcov_dump(void);

static void flush_on_crash(int sig) {
    __gcov_dump();
    _exit(128 + sig);
}

int main(void) {
    signal(SIGSEGV, flush_on_crash);
    signal(SIGABRT, flush_on_crash);
    signal(SIGTERM, flush_on_crash);
    /* ... */
}
```

**安装 lcov：**
```bash
sudo apt-get install lcov      # Ubuntu/Debian
sudo yum install lcov          # RHEL/CentOS
brew install lcov              # macOS
```

**生成 HTML 报告：**
```bash
# 收集（--branch-coverage 启用分支统计）
lcov --capture --directory . \
     --output-file coverage.info \
     --branch-coverage

# 过滤（见 2.5 节）
lcov --remove coverage.info '/usr/*' '*/third_party/*' \
     --output-file coverage_clean.info \
     --branch-coverage

# 摘要
lcov --summary coverage_clean.info --branch-coverage

# HTML
genhtml coverage_clean.info \
        --output-directory coverage_html/ \
        --branch-coverage --highlight --legend

open coverage_html/index.html
```

**清理数据：**
```bash
# 仅重置计数（保留 .gcno，无需重新编译）
lcov --zerocounters --directory .

# 清理所有覆盖率产物
find . \( -name "*.gcda" -o -name "*.gcno" -o -name "*.gcov" \) -delete
rm -rf coverage_html/ coverage.info coverage_clean.info
```

### 2.4 分支覆盖率专项

**关键规律：** 编译阶段不需要额外标志，`--coverage` 本身已插入分支计数器。分支数据的开关在**报告阶段**：

```
编译:  gcc --coverage -O0 -g ...    ← 无需额外标志，已包含分支插桩
运行:  ./my_program
收集:  lcov --branch-coverage        ← 关键开关，每步 lcov 都要加
HTML:  genhtml --branch-coverage     ← genhtml 用此参数
```

**为什么需要 `--branch-coverage`：** lcov 默认只收集行与函数覆盖。官方文档明确说明，关闭分支统计是有意为之的性能权衡——分支数据会显著增加内存、CPU 和 `.info` 文件体积。`--branch-coverage` 是 `--rc branch_coverage=1` 的简写，两者完全等价。

**版本说明：** 旧写法 `--rc lcov_branch_coverage=1`（带 `lcov_` 前缀）在新版中仍向后兼容，但已标记废弃，统一改用 `--branch-coverage`。

**注意：** `genhtml` 只识别 `--branch-coverage`，不接受 `--rc branch_coverage=1`。

如需永久生效，写入 `~/.lcovrc`：
```ini
# ~/.lcovrc
branch_coverage = 1
```

**gcov 文本输出解读（`gcov -b -c`）：**
```
        1:   10:int classify(int x) {
branch  0 taken 7 (fallthrough)    # x > 0 为 true
branch  1 taken 3                  # x > 0 为 false
        7:   11:    if (x > 0) {
        7:   12:        return 1;
        -:   13:    } else if (x == 0) {
branch  0 taken 2 (fallthrough)
branch  1 taken 1
        2:   14:        return 0;
        1:   15:    } else {
        1:   16:        return -1;
        -:   17:    }
branch  0 taken 0                  # ← taken 0：该分支从未执行，是测试盲区！
branch  1 taken 7
```

**常见误区：**

行覆盖 100% 不等于测试充分：
```c
int safe_div(int a, int b) {
    if (b != 0) return a / b;  // 这行被执行了
    return 0;
}
// 只测试 safe_div(10, 2)
// 行覆盖：100%，分支覆盖：50%（b == 0 从未触发）
```

分支数量远多于 `if` 语句数：`&&`、`||`、三目运算符、`switch` 的每个 `case` 都各产生独立分支。

### 2.5 过滤不需要的部分

过滤的目的是让覆盖率报告只关注**自己写的业务代码**，排除系统头文件、第三方库、测试代码本身、自动生成代码等噪声。GCC 体系有三个层面的过滤手段：

#### 层面一：lcov 文件级过滤（最常用）

`lcov --remove` 按路径通配符删除不需要的文件：

```bash
lcov --remove coverage.info \
     '/usr/*'              \   # 系统头文件（glibc、libstdc++）
     '*/third_party/*'     \   # 第三方库
     '*/test/*'            \   # 测试代码本身
     '*/generated/*'       \   # 自动生成代码（protobuf、thrift 等）
     '*/build/*'           \   # 构建目录中的临时文件
     --output-file coverage_clean.info \
     --branch-coverage
```

`lcov --extract` 只保留指定路径（白名单模式，适合大型项目只关注某个子模块）：

```bash
# 只保留 src/my_module/ 下的文件
lcov --extract coverage.info '*/src/my_module/*' \
     --output-file coverage_module.info \
     --branch-coverage
```

> 路径模式使用 shell 通配符（`*` 匹配任意字符包括 `/`），匹配的是文件的**绝对路径**。

#### 层面二：源码内联注释（行/区域级精细过滤）

在源码中直接用注释标记要排除的部分，无需修改构建脚本：

```c
// 排除单行（如不可达的防御性断言）
assert(ptr != nullptr);  // LCOV_EXCL_LINE

// 排除一个代码块
// LCOV_EXCL_START
int debug_only_function(void) {
    /* 调试代码，不计入覆盖率 */
    return 0;
}
// LCOV_EXCL_STOP

// 只排除分支覆盖（行覆盖仍统计）
if (unlikely_error) {  // LCOV_EXCL_BR_LINE
    handle_error();
}

// 排除一段代码的分支覆盖
// LCOV_EXCL_BR_START
switch (internal_state) {
    case STATE_A: break;
    case STATE_B: break;
    default: abort();   // 理论上不可达
}
// LCOV_EXCL_BR_STOP
```

| 注释标记 | 效果 |
|----------|------|
| `LCOV_EXCL_LINE` | 排除该行的所有覆盖数据 |
| `LCOV_EXCL_START` / `LCOV_EXCL_STOP` | 排除区间内所有行 |
| `LCOV_EXCL_BR_LINE` | 仅排除该行的分支覆盖 |
| `LCOV_EXCL_BR_START` / `LCOV_EXCL_BR_STOP` | 仅排除区间内的分支覆盖 |

#### 层面三：编译时选择性插桩（`-fprofile-list`）

对于超大型项目，可以在编译阶段直接控制哪些文件或函数参与插桩，从而减少运行时开销：

```bash
# 创建插桩控制列表 cov.list
cat > cov.list << 'EOF'
# 格式：sanitizer special-case list
[clang]
# 只对指定目录插桩（允许）
source:src/my_module/*.cpp=allow
# 跳过第三方库
source:third_party/*=skip
# 默认跳过其余所有
default:skip
EOF

# 编译时传入
gcc --coverage -O0 -g -fprofile-list=cov.list -o my_program main.cpp
```

> **注意：** `-fprofile-list` 控制的是**计数器是否插入**，即使设为 skip 的文件出现在报告里也会显示 0% 覆盖率。这与 `lcov --remove`（删除报告条目）有本质区别。

### 2.6 常见问题排查

| 现象 | 根因 | 解法 |
|------|------|------|
| 找不到 `.gcda` 文件 | 程序崩溃/被 kill，未正常退出 | 注册信号处理，调用 `__gcov_dump()` |
| 覆盖率始终为 0 | 链接时漏掉 `--coverage` | 链接命令补 `--coverage` 或 `-lgcov` |
| 行号与源码对不上 | 开启了编译优化 | 加 `-O0` |
| `.gcno` 与 `.gcda` 版本不匹配 | 重编译前未清除旧 `.gcda` | `find . -name "*.gcda" -delete` 后再运行 |
| 多线程数据损坏 | `.gcda` 写入存在竞态 | 加 `-fprofile-update=atomic` |
| `branches` 行不显示 | lcov 每步漏掉 `--branch-coverage` | 确保所有 lcov/genhtml 命令都带该参数 |
| 过滤路径不生效 | 模式未匹配到绝对路径 | 用 `lcov --list coverage.info` 查看实际路径再调整 |

---

## 3 Clang/LLVM 覆盖率体系

Clang 提供两种覆盖率模式：

| 模式 | 编译标志 | 中间文件 | 工具链 | 适用场景 |
|------|----------|----------|--------|----------|
| **gcov 兼容模式** | `--coverage` | `.gcno` + `.gcda` | lcov + genhtml | 需与 GCC 工具链共存，迁移成本低 |
| **Source-based（推荐）** | `-fprofile-instr-generate -fcoverage-mapping` | `.profraw` → `.profdata` | llvm-profdata + llvm-cov | 区域级精度，模板/宏各自统计 |

gcov 兼容模式与 GCC 体系完全相同，直接替换编译器即可，本节重点介绍 Source-based 模式。

### 3.1 插桩原理与运行时依赖

#### 插桩在编译管道中的位置

Source-based Coverage 直接在 AST 和预处理信息层面操作，在 LLVM 优化器介入之前完成插桩，因此能生成非常精确的覆盖数据。

```
源代码（.c / .cpp）
    │
    ▼
  [Clang 前端：词法 → 语法 → AST]
    │
    ├─► -fcoverage-mapping
    │     在 AST 阶段生成 Coverage Map（源码区域 ↔ 计数器 ID 的映射表）
    │     以元数据形式嵌入 LLVM IR，最终写入二进制只读 section
    │
    └─► -fprofile-instr-generate
          向 LLVM IR 注入 llvm.instrprof.increment 内建调用
          每个控制流分叉点（if、loop、switch、&&、||）前插一条计数器自增指令
    │
    ▼
  [LLVM 优化 passes]
    │     优化器无法证明计数器自增"无副作用"，不会删除它们
    │     ∴ 覆盖率精度不受优化影响（与 gcov 兼容模式的关键区别）
    │
    ▼
  最终二进制（含四类 section）
    ├── __llvm_prf_cnts   计数器数组（可写，运行时自增）
    ├── __llvm_prf_data   函数描述符（名称哈希、计数器数量）
    ├── __llvm_covmap     Coverage Map（源码位置 ↔ 计数器 ID，只读）
    └── __llvm_prf_names  函数名称字符串表（只读）
```

FE 插桩在优化前发生，保留完整的源码级上下文；IR 层插桩（`-fprofile-generate`）在优化后发生，许多结构已被变换，只能做函数级覆盖，不支持行级。

#### 运行时依赖：compiler-rt profile 库

插桩后的二进制只有计数器自增的代码，写文件的能力来自 `compiler-rt` 的 profile 组件，具体是静态库：

```
libclang_rt.profile-<arch>.a
```

典型路径：
```bash
# 查看当前 clang 对应的 runtime 目录
clang -print-runtime-dir

# 验证库是否存在
ls $(clang -print-runtime-dir)/libclang_rt.profile*
```

传递 `-fprofile-instr-generate` 给链接阶段时，clang driver 会自动链入该库，无需手动指定。

#### 运行时初始化流程

```
程序启动
  └─► [static initializer（来自 libclang_rt.profile）]
        ├── 读取 LLVM_PROFILE_FILE，确定 .profraw 输出路径
        └── 通过 atexit() 注册 __llvm_profile_write_file 为退出回调

程序运行中
  └─► 每次执行到插桩点，__llvm_prf_cnts 中对应计数器自增

程序正常退出
  └─► atexit 触发 __llvm_profile_write_file()
        └── 将计数器数组 + 函数描述符序列化写入 .profraw
```

常用运行时 API（崩溃场景、守护进程、测试框架）：

```cpp
extern "C" {
    int  __llvm_profile_write_file(void);       // 写出 profraw，返回 0 成功
    void __llvm_profile_initialize_file(void);  // 解析 LLVM_PROFILE_FILE，截断旧文件
    void __llvm_profile_set_filename(char *);   // 手动设置路径（不截断）
}

// 崩溃处理示例
static void coverage_on_crash(int sig) {
    __llvm_profile_write_file();
    _exit(128 + sig);
}

int main() {
    signal(SIGSEGV, coverage_on_crash);
    signal(SIGABRT, coverage_on_crash);
    /* ... */
}
```

#### runtime 库安装

```bash
# Ubuntu/Debian
sudo apt-get install clang llvm libclang-rt-dev

# 特定版本
sudo apt-get install clang-15 llvm-15 libclang-rt-15-dev

# 验证符号是否正确链入
nm ./my_program | grep __llvm_profile
# 预期看到 __llvm_profile_write_file、__llvm_profile_runtime 等
```

### 3.2 编译设置

```bash
# C
clang -fprofile-instr-generate -fcoverage-mapping -O0 -g \
      -o my_program my_program.c

# C++
clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g \
        -std=c++17 -o my_app main.cpp utils.cpp
```

| 选项 | 作用 |
|------|------|
| `-fprofile-instr-generate` | 插入计数器，运行后输出 `.profraw`；链接时触发自动链入 runtime |
| `-fcoverage-mapping` | 将源码到计数器的 Coverage Map 嵌入二进制 |
| `-O0` | 禁用优化，确保覆盖率数据准确 |
| `-g` | 保留调试信息 |

### 3.3 运行与收集

`LLVM_PROFILE_FILE` 模式串：

| 模式串 | 展开为 |
|--------|--------|
| `%p` | 进程 ID（多进程场景必用） |
| `%h` | 主机名 |
| `%Nm` | 二进制签名哈希，同时创建 N 个文件池自动管理合并 |
| `%b` | Build ID（需链接时加 `--build-id`） |
| `%c` | 启用持续同步模式，崩溃也能保留数据（目前主要支持 Darwin） |

```bash
# 单次运行
LLVM_PROFILE_FILE="coverage.profraw" ./my_app

# 多进程并发（%p 避免互相覆盖）
LLVM_PROFILE_FILE="coverage-%p.profraw" ./run_tests

# 自动文件池（N=4，运行时管理并发写入）
LLVM_PROFILE_FILE="coverage-%4m.profraw" ./run_tests
```

**合并与报告：**
```bash
# 合并（-sparse 减小文件体积，不用于 PGO 时推荐加）
llvm-profdata merge -sparse *.profraw -o coverage.profdata

# 终端摘要
llvm-cov report ./my_app -instr-profile=coverage.profdata

# HTML 报告
llvm-cov show ./my_app \
         -instr-profile=coverage.profdata \
         -format=html \
         -output-dir=coverage_html/ \
         -show-line-counts-or-regions \
         -show-instantiations

# 导出 lcov 格式（对接 genhtml 或 Codecov）
llvm-cov export ./my_app \
         -instr-profile=coverage.profdata \
         -format=lcov > coverage.lcov
genhtml coverage.lcov --output-directory coverage_html/ --branch-coverage
```

### 3.4 过滤不需要的部分

Clang/LLVM 体系有三个层面的过滤，与 GCC 体系的粒度对应，但机制不同：

#### 层面一：报告阶段文件过滤（`-ignore-filename-regex` / 白名单）

在 `llvm-cov` 生成报告时过滤，最灵活，不影响已收集的数据：

```bash
# 黑名单：排除匹配正则的文件
llvm-cov show ./my_app \
         -instr-profile=coverage.profdata \
         -format=html \
         -output-dir=coverage_html/ \
         -ignore-filename-regex='(^/usr/|.*third_party.*|.*test.*|.*\.pb\.cc)'

# 白名单：只统计指定源文件（直接在命令末尾列出）
llvm-cov report ./my_app \
         -instr-profile=coverage.profdata \
         src/my_module/foo.cpp \
         src/my_module/bar.cpp

# 白名单：只统计特定目录（使用正则反向过滤）
# llvm-cov 目前无 --include-filename-regex，通过 export + lcov 组合实现
llvm-cov export ./my_app \
         -instr-profile=coverage.profdata \
         -format=lcov \
         -ignore-filename-regex='(?!.*src/my_module)' > filtered.lcov
```

> `-ignore-filename-regex` 支持 POSIX 正则，**不支持负向预查**（negative lookahead）。如需只保留特定目录，推荐在命令末尾显式列出源文件，或导出后用 `lcov --extract` 处理。

**导出后用 lcov 过滤（灵活度最高的组合方案）：**
```bash
# 先导出全量 lcov
llvm-cov export ./my_app \
         -instr-profile=coverage.profdata \
         -format=lcov > coverage_full.lcov

# 再用 lcov 精细过滤
lcov --remove coverage_full.lcov '/usr/*' '*/third_party/*' '*/test/*' \
     --output-file coverage_clean.lcov \
     --branch-coverage

genhtml coverage_clean.lcov --output-directory coverage_html/ --branch-coverage
```

#### 层面二：源码属性注解（函数/区域级）

在源码中用 Clang 扩展属性标记不参与覆盖统计的函数：

```cpp
// 整个函数不计入覆盖率
__attribute__((no_sanitize("coverage")))
void debug_dump(const State& s) {
    // 调试辅助函数，不统计覆盖率
}

// C++ 模板函数的特定实例不计入
template<typename T>
__attribute__((no_sanitize("coverage")))
void trace(T value) { /* ... */ }
```

> `no_sanitize("coverage")` 阻止编译器对该函数插桩，因此该函数在报告中不会出现（而非显示 0%）。

#### 层面三：编译时选择性插桩（`-fprofile-list`）

与 GCC 体系相同，用 sanitizer special-case list 控制哪些源文件或函数参与插桩：

```bash
# cov.list
[clang]
# 只对业务代码插桩
source:src/core/*.cpp=allow
source:src/utils/*.cpp=allow
# 跳过第三方和生成代码
source:third_party/*=skip
source:generated/*=skip
# 跳过特定函数
function:*Test*=skip
function:*Benchmark*=skip
# 其余默认跳过
default:skip
```

```bash
clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g \
        -fprofile-list=cov.list \
        -o my_app main.cpp utils.cpp
```

> 与 GCC 体系的 `-fprofile-list` 完全相同的语法（LLVM sanitizer special-case list 格式）。

#### 各层面过滤方式汇总

| 过滤层面 | GCC 体系 | Clang 体系 | 时机 | 粒度 |
|----------|----------|------------|------|------|
| 编译时选择性插桩 | `-fprofile-list` | `-fprofile-list` | 编译 | 文件 / 函数 |
| 源码内联标记 | `LCOV_EXCL_*` 注释 | `__attribute__((no_sanitize))` | 源码 | 行 / 函数 |
| 报告后处理 | `lcov --remove` / `--extract` | `-ignore-filename-regex` / `lcov --remove` | 报告 | 文件 |

### 3.5 常见问题排查

| 现象 | 根因 | 解法 |
|------|------|------|
| `.profraw` 未生成 | 程序崩溃，atexit 未触发 | 注册信号处理，调用 `__llvm_profile_write_file()` |
| 链接报错：找不到 `libclang_rt.profile` | 未安装 compiler-rt 或版本不匹配 | `apt install libclang-rt-dev` 或确保版本一致 |
| `llvm-profdata` 不在 PATH | LLVM 工具未安装或路径未配置 | 用完整路径 `$(clang -print-runtime-dir)/../../bin/llvm-profdata` |
| profdata 与 llvm-cov 版本不匹配 | 多版本 LLVM 共存 | 确保 clang、llvm-profdata、llvm-cov 版本一致 |
| 多进程 profraw 互相覆盖 | 默认文件名冲突 | `LLVM_PROFILE_FILE="cov-%p.profraw"` |
| 覆盖率明显失真 | 开启了优化 | 加 `-O0` |
| `-ignore-filename-regex` 不支持负向过滤 | POSIX 正则限制 | 导出 lcov 后用 `lcov --extract` 实现白名单 |

---

## 4 两大体系对比

| 维度 | GCC / gcov | Clang Source-based |
|------|-----------|-------------------|
| **覆盖粒度** | 行、函数、分支 | 行、函数、分支、**区域（Region）**、MC/DC |
| **插桩时机** | 编译后（DebugInfo 层） | AST 层（优化前） |
| **优化影响** | 优化可能影响准确性 | 不受优化影响（映射在优化前固化） |
| **模板/宏精度** | 合并统计 | 每个实例单独统计 |
| **中间文件** | `.gcno` + `.gcda` | `.profraw` → `.profdata` |
| **HTML 报告** | 依赖外部 genhtml | llvm-cov 内置 |
| **lcov 兼容** | 原生 | 需 `llvm-cov export -format=lcov` 转换 |
| **多线程安全** | 需加 `-fprofile-update=atomic` | 内置支持 |
| **运行时库** | `libgcov`（GCC 自带） | `libclang_rt.profile`（需安装 compiler-rt）|
| **跨语言** | C / C++ / Fortran | C / C++ / ObjC / Swift |
| **过滤机制** | `lcov --remove` + `LCOV_EXCL_*` + `-fprofile-list` | `-ignore-filename-regex` + `no_sanitize` + `-fprofile-list` |
| **适合场景** | 传统项目、兼容性优先 | 现代项目、精度优先 |

---

## 5 构建系统集成

### 5.1 CMake

**通用覆盖率模块（`cmake/Coverage.cmake`）：**

```cmake
# cmake/Coverage.cmake
option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        # GCC 体系
        add_compile_options(--coverage -O0 -g)
        add_link_options(--coverage)
        message(STATUS "Coverage: GCC/gcov mode")

    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        # Clang Source-based
        add_compile_options(-fprofile-instr-generate -fcoverage-mapping -O0 -g)
        add_link_options(-fprofile-instr-generate)
        message(STATUS "Coverage: Clang source-based mode")

    else()
        message(FATAL_ERROR "Coverage requires GCC or Clang")
    endif()
endif()
```

**GCC 覆盖率 target：**
```cmake
# 在 CMakeLists.txt 中
if(ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    find_program(LCOV lcov REQUIRED)
    find_program(GENHTML genhtml REQUIRED)

    add_custom_target(coverage
        # 清理旧数据
        COMMAND find ${CMAKE_BINARY_DIR} -name "*.gcda" -delete
        # 运行测试
        COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
        # 收集（含分支）
        COMMAND ${LCOV} --capture --directory ${CMAKE_BINARY_DIR}
                        --output-file ${CMAKE_BINARY_DIR}/coverage.info
                        --branch-coverage
        # 过滤
        COMMAND ${LCOV} --remove ${CMAKE_BINARY_DIR}/coverage.info
                        '/usr/*' '*/third_party/*' '*/test/*'
                        --output-file ${CMAKE_BINARY_DIR}/coverage_clean.info
                        --branch-coverage
        # HTML
        COMMAND ${GENHTML} ${CMAKE_BINARY_DIR}/coverage_clean.info
                           --output-directory ${CMAKE_BINARY_DIR}/coverage_html
                           --branch-coverage --highlight --legend
        DEPENDS my_tests
        COMMENT "Generating GCC coverage report..."
    )
endif()
```

**Clang Source-based 覆盖率 target：**
```cmake
if(ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    find_program(LLVM_PROFDATA llvm-profdata REQUIRED)
    find_program(LLVM_COV      llvm-cov      REQUIRED)

    add_custom_target(coverage
        COMMAND ${CMAKE_COMMAND} -E env
                LLVM_PROFILE_FILE=${CMAKE_BINARY_DIR}/cov-%p.profraw
                $<TARGET_FILE:my_tests>
        COMMAND ${LLVM_PROFDATA} merge -sparse
                ${CMAKE_BINARY_DIR}/cov-*.profraw
                -o ${CMAKE_BINARY_DIR}/coverage.profdata
        COMMAND ${LLVM_COV} show $<TARGET_FILE:my_tests>
                -instr-profile=${CMAKE_BINARY_DIR}/coverage.profdata
                -format=html
                -output-dir=${CMAKE_BINARY_DIR}/coverage_html
                -ignore-filename-regex='(^/usr/|.*third_party.*|.*test.*)'
                -show-line-counts-or-regions
        DEPENDS my_tests
        COMMENT "Generating Clang coverage report..."
    )
endif()
```

使用方式：
```bash
# GCC
cmake -B build -DENABLE_COVERAGE=ON
cmake --build build --target coverage

# Clang
cmake -B build -DCMAKE_CXX_COMPILER=clang++ -DENABLE_COVERAGE=ON
cmake --build build --target coverage

open build/coverage_html/index.html
```

### 5.2 Makefile

```makefile
CXX    = g++
SRCS   = main.cpp utils.cpp
TARGET = my_program

# 普通构建
$(TARGET): $(SRCS)
	$(CXX) -O2 -o $@ $^

# GCC 覆盖率（含过滤）
coverage-gcc: clean-cov
	$(CXX) --coverage -O0 -g -o $(TARGET) $(SRCS)
	./$(TARGET)
	lcov --capture --directory . \
	     --output-file coverage.info --branch-coverage
	lcov --remove coverage.info '/usr/*' '*/third_party/*' '*/test/*' \
	     --output-file coverage_clean.info --branch-coverage
	lcov --summary coverage_clean.info --branch-coverage
	genhtml coverage_clean.info \
	        --output-directory coverage_html/ --branch-coverage
	@echo "报告：coverage_html/index.html"

# Clang Source-based 覆盖率（含过滤）
coverage-clang: clean-cov
	clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g \
	        -o $(TARGET) $(SRCS)
	LLVM_PROFILE_FILE="cov-%p.profraw" ./$(TARGET)
	llvm-profdata merge -sparse cov-*.profraw -o coverage.profdata
	llvm-cov show ./$(TARGET) \
	         -instr-profile=coverage.profdata \
	         -format=html -output-dir=coverage_html/ \
	         -ignore-filename-regex='(^/usr/|.*third_party.*)'
	@echo "报告：coverage_html/index.html"

clean-cov:
	find . \( -name "*.gcda" -o -name "*.gcno" -o -name "*.gcov" \) -delete
	rm -f cov-*.profraw coverage.profdata coverage.info coverage_clean.info
	rm -rf coverage_html/

.PHONY: coverage-gcc coverage-clang clean-cov
```

---

## 6 CI/CD 集成

### GitHub Actions — GCC（含分支与过滤）

```yaml
# .github/workflows/coverage.yml
name: Code Coverage

on: [push, pull_request]

jobs:
  coverage-gcc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: sudo apt-get install -y lcov

      - name: Build with coverage
        run: |
          cmake -B build -DENABLE_COVERAGE=ON
          cmake --build build

      - name: Run tests
        run: cd build && ctest --output-on-failure

      - name: Collect and filter coverage
        run: |
          lcov --capture --directory build \
               --output-file coverage.info \
               --branch-coverage
          lcov --remove coverage.info '/usr/*' '*/test/*' \
               --output-file coverage_clean.info \
               --branch-coverage
          lcov --summary coverage_clean.info --branch-coverage

      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage_clean.info
          fail_ci_if_error: true
```

### GitHub Actions — Clang Source-based（含过滤）

```yaml
name: Clang Coverage

on: [push, pull_request]

jobs:
  coverage-clang:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Clang & LLVM
        run: sudo apt-get install -y clang llvm libclang-rt-dev

      - name: Build with coverage
        env:
          CC: clang
          CXX: clang++
        run: |
          cmake -B build -DENABLE_COVERAGE=ON
          cmake --build build

      - name: Run tests and collect coverage
        run: |
          LLVM_PROFILE_FILE="build/cov-%p.profraw" build/my_tests
          llvm-profdata merge -sparse build/cov-*.profraw \
                        -o build/coverage.profdata
          # 导出 lcov 并过滤
          llvm-cov export build/my_tests \
                   -instr-profile=build/coverage.profdata \
                   -format=lcov \
                   -ignore-filename-regex='(^/usr/|.*third_party.*)' \
                   > coverage.lcov

      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage.lcov
```

---

## 7 快速命令速查

### 安装

```bash
# Ubuntu/Debian
sudo apt-get install gcc g++ lcov               # GCC 体系
sudo apt-get install clang llvm libclang-rt-dev # Clang 体系

# macOS（Xcode 自带 clang，只需 lcov）
brew install lcov

# 确认工具版本
gcov --version && lcov --version
clang -print-runtime-dir
llvm-profdata --version && llvm-cov --version
```

### GCC 覆盖率（完整流程含过滤）

```bash
# 编译
g++ --coverage -O0 -g -o prog main.cpp

# 运行
./prog

# 收集（含分支）
lcov --capture --directory . -o cov.info --branch-coverage

# 过滤
lcov --remove cov.info '/usr/*' '*/third_party/*' \
     -o cov_clean.info --branch-coverage

# 摘要
lcov --summary cov_clean.info --branch-coverage

# HTML
genhtml cov_clean.info -o html/ --branch-coverage
```

### Clang Source-based 覆盖率（完整流程含过滤）

```bash
# 编译
clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g -o prog main.cpp

# 运行
LLVM_PROFILE_FILE="cov-%p.profraw" ./prog

# 合并
llvm-profdata merge -sparse cov-*.profraw -o cov.profdata

# 摘要（含过滤）
llvm-cov report ./prog -instr-profile=cov.profdata \
           -ignore-filename-regex='(^/usr/|.*third_party.*)'

# HTML（含过滤）
llvm-cov show ./prog -instr-profile=cov.profdata \
           -format=html -output-dir=html/ \
           -ignore-filename-regex='(^/usr/|.*third_party.*)'

# 导出 lcov（含过滤，再用 lcov 精细处理）
llvm-cov export ./prog -instr-profile=cov.profdata \
           -format=lcov \
           -ignore-filename-regex='(^/usr/|.*third_party.*)' \
           > coverage.lcov
```

### 选型决策

```
使用 GCC？
  └─► --coverage + lcov --branch-coverage + genhtml --branch-coverage
      过滤：lcov --remove + LCOV_EXCL_* 注释

使用 Clang，需要兼容 lcov 生态？
  └─► clang --coverage，流程同 GCC

使用 Clang，追求最高精度？
  └─► -fprofile-instr-generate -fcoverage-mapping
      → llvm-profdata merge → llvm-cov show/report
      过滤：-ignore-filename-regex + export → lcov --remove
      选择性插桩：-fprofile-list
```

---

*版本 3.0 | GCC ≥ 9.x，Clang/LLVM ≥ 12.x*

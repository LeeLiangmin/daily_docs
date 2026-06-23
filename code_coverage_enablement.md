# 代码测试覆盖率赋能文档

## GCC 与 Clang/LLVM 体系完整指南

---

## 目录

1. [基本概念](#基本概念)
2. [GCC 覆盖率体系（gcov）](#gcc-覆盖率体系gcov)
   - 编译设置
   - 运行测试
   - 生成报告
   - 常见问题排查
3. [Clang/LLVM 覆盖率体系（llvm-cov）](#clangllvm-覆盖率体系llvm-cov)
   - 编译设置
   - 运行测试
   - 生成报告
   - 常见问题排查
4. [两大体系对比](#两大体系对比)
5. [与 CMake 集成](#与-cmake-集成)
6. [与 Makefile 集成](#与-makefile-集成)
7. [CI/CD 集成实践](#cicd-集成实践)
8. [常用工具参考](#常用工具参考)

---

## 基本概念

**测试覆盖率（Code Coverage）** 是衡量测试用例覆盖源代码程度的指标，帮助团队发现未被测试覆盖的代码路径，从而提升代码质量和可靠性。

常见覆盖率类型：

| 类型 | 说明 |
|------|------|
| **行覆盖率（Line Coverage）** | 哪些代码行被执行过 |
| **函数覆盖率（Function Coverage）** | 哪些函数被调用过 |
| **分支覆盖率（Branch Coverage）** | if/switch 的每个分支是否都被触发 |
| **区域覆盖率（Region Coverage）** | 更精细的代码区块级别（Clang 特有） |

---

## GCC 覆盖率体系（gcov）

GCC 通过 `gcov` 工具链实现覆盖率统计，核心是在编译阶段插入计数器，运行后生成 `.gcda` 数据文件，再用 `gcov` 或 `lcov` 分析汇总。

### 工具链关系

```
源代码  ──编译──►  .gcno（注记文件）
              └──运行──►  .gcda（执行数据）
                      └──gcov──►  .gcov（文本报告）
                              └──lcov/genhtml──►  HTML 报告
```

---

### 编译设置

#### 核心编译选项

```bash
gcc -fprofile-arcs -ftest-coverage -o my_program my_program.c
```

| 选项 | 作用 |
|------|------|
| `-fprofile-arcs` | 在代码中插入弧度（arc）计数器，生成 `.gcda` 数据文件 |
| `-ftest-coverage` | 生成 `.gcno` 注记文件，记录代码结构信息 |
| `--coverage` | 以上两项的等价简写 |

#### 推荐完整编译命令

```bash
# 单文件
gcc --coverage -O0 -g -o my_program my_program.c

# 多文件（链接时也需要 --coverage）
gcc --coverage -O0 -g -c file1.c -o file1.o
gcc --coverage -O0 -g -c file2.c -o file2.o
gcc --coverage -O0 -g file1.o file2.o -o my_program

# C++ 项目
g++ --coverage -O0 -g -std=c++17 -o my_app main.cpp utils.cpp
```

> **重要提示：**
> - 务必加 `-O0` 禁用优化，避免编译器消除代码影响覆盖率的准确性
> - 加 `-g` 保留调试信息，方便在报告中定位源码行号
> - 链接阶段同样需要 `--coverage` 标志（或 `-lgcov`）

---

### 运行测试

编译完成后，正常运行程序或测试套件：

```bash
# 运行程序（执行后生成 .gcda 文件）
./my_program

# 运行 gtest 测试
./my_tests --gtest_filter='*'

# 运行多个测试场景（覆盖率数据会累积叠加）
./my_program --input test1.txt
./my_program --input test2.txt
./my_program --input test3.txt
```

运行后，当前目录（或对象文件所在目录）会生成 `.gcda` 文件。

---

### 生成报告

#### 方式一：直接使用 gcov（文本格式）

```bash
# 针对单个源文件
gcov my_program.c

# 输出带分支信息
gcov -b my_program.c

# 输出每个函数的覆盖情况
gcov -f my_program.c
```

gcov 会在当前目录生成 `my_program.c.gcov` 文本文件，其中 `#####` 表示未覆盖行：

```
        -:    0:Source:my_program.c
        1:    1:int main() {
        1:    2:    int x = 10;
    #####:    3:    if (x > 100) {       // 未覆盖
    #####:    4:        return -1;        // 未覆盖
        -:    5:    }
        1:    6:    return 0;
        -:    7:}
```

#### 方式二：使用 lcov + genhtml（推荐，HTML 格式）

**安装 lcov：**
```bash
# Ubuntu/Debian
sudo apt-get install lcov

# macOS
brew install lcov

# RHEL/CentOS
sudo yum install lcov
```

**生成 HTML 报告：**
```bash
# 步骤 1：收集覆盖率数据
lcov --capture --directory . --output-file coverage.info

# 步骤 2（可选）：过滤掉系统头文件和第三方库
lcov --remove coverage.info '/usr/*' '*/third_party/*' --output-file coverage_filtered.info

# 步骤 3：生成 HTML 报告
genhtml coverage_filtered.info --output-directory coverage_report/

# 步骤 4：在浏览器中查看（macOS）
open coverage_report/index.html
# Linux
xdg-open coverage_report/index.html
```

**打印摘要到终端：**
```bash
lcov --summary coverage_filtered.info
```

输出示例：
```
Reading tracefile coverage_filtered.info
Summary coverage rate:
  lines......: 87.5% (42 of 48 lines)
  functions..: 100.0% (8 of 8 functions)
  branches...: 75.0% (18 of 24 branches)
```

---

### 清理覆盖率数据

```bash
# 清理 .gcda 数据文件（保留 .gcno）
lcov --zerocounters --directory .

# 或手动清理
find . -name "*.gcda" -delete

# 清理所有覆盖率产物
find . -name "*.gcda" -delete
find . -name "*.gcno" -delete
find . -name "*.gcov" -delete
rm -rf coverage_report/ coverage.info
```

---

### GCC 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 找不到 `.gcda` 文件 | 程序未正常退出（如崩溃） | 确保程序正常退出，或捕获信号后调用 `__gcov_flush()` |
| 覆盖率始终为 0 | 链接时未加 `--coverage` | 链接命令补充 `--coverage` 或 `-lgcov` |
| 行号与源码不对应 | 开启了编译优化 | 添加 `-O0` 禁用优化 |
| 覆盖率数据与源码版本不匹配 | `.gcno` 与 `.gcda` 版本不一致 | 重新编译后再运行 |
| 多线程程序数据丢失 | `.gcda` 写入存在竞态 | 编译时加 `-fprofile-update=atomic` |

---

## Clang/LLVM 覆盖率体系（llvm-cov）

Clang/LLVM 提供了更现代、更精细的覆盖率支持，分为两种模式：

| 模式 | 兼容性 | 精细度 | 推荐场景 |
|------|--------|--------|----------|
| **gcov 兼容模式** | 与 lcov 等工具兼容 | 行/函数/分支 | 需要与 GCC 工具链共存 |
| **Source-based Coverage（推荐）** | Clang 原生 | 行/函数/分支/区域 | 纯 Clang 项目，精度最高 |

---

### 方式一：gcov 兼容模式

使用与 GCC 完全相同的标志，可直接使用 lcov 处理：

```bash
clang --coverage -O0 -g -o my_program my_program.c
# 运行程序
./my_program
# 使用 lcov/genhtml 生成报告（流程与 GCC 完全相同）
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report/
```

---

### 方式二：Source-based Coverage（推荐）

这是 Clang 原生的覆盖率方案，精度更高，能区分宏展开和模板实例化中的覆盖情况。

#### 工具链关系

```
源代码  ──编译──►  插桩后的二进制
              └──运行──►  default.profraw（原始数据）
                      └──llvm-profdata merge──►  .profdata（合并数据）
                                             └──llvm-cov──►  报告
```

#### 编译设置

```bash
# C 项目
clang -fprofile-instr-generate -fcoverage-mapping -O0 -g \
      -o my_program my_program.c

# C++ 项目
clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g \
        -std=c++17 -o my_app main.cpp utils.cpp
```

| 选项 | 作用 |
|------|------|
| `-fprofile-instr-generate` | 插入覆盖率计数器，运行后输出 `.profraw` 文件 |
| `-fcoverage-mapping` | 生成源码到计数器的映射信息（嵌入二进制中） |
| `-O0` | 禁用优化，确保覆盖率数据准确 |
| `-g` | 保留调试信息 |

#### 控制输出文件路径（可选）

```bash
# 通过环境变量指定输出路径
export LLVM_PROFILE_FILE="coverage-%p-%m.profraw"
# %p = 进程 ID，%m = 二进制哈希，避免多进程覆盖

./my_program
```

---

### 运行测试

```bash
# 正常运行（默认生成 default.profraw）
./my_program

# 自定义输出路径
LLVM_PROFILE_FILE="my_test.profraw" ./my_program

# 运行多个测试
LLVM_PROFILE_FILE="test1.profraw" ./my_program --scenario 1
LLVM_PROFILE_FILE="test2.profraw" ./my_program --scenario 2
```

---

### 生成报告

#### 步骤 1：合并原始数据

```bash
# 合并单个文件
llvm-profdata merge -sparse default.profraw -o coverage.profdata

# 合并多个 profraw 文件
llvm-profdata merge -sparse test1.profraw test2.profraw \
              -o coverage.profdata

# 使用通配符合并所有 profraw
llvm-profdata merge -sparse *.profraw -o coverage.profdata
```

#### 步骤 2：生成报告

```bash
# 终端文本报告（显示每行覆盖次数）
llvm-cov show ./my_program \
         -instr-profile=coverage.profdata \
         -format=text \
         -output-dir=coverage_text/

# HTML 报告（推荐）
llvm-cov show ./my_program \
         -instr-profile=coverage.profdata \
         -format=html \
         -output-dir=coverage_html/ \
         -show-line-counts-or-regions \
         -show-instantiations

# 打印覆盖率摘要到终端
llvm-cov report ./my_program \
         -instr-profile=coverage.profdata

# 仅统计特定源文件
llvm-cov report ./my_program \
         -instr-profile=coverage.profdata \
         src/my_module.cpp
```

**llvm-cov report 输出示例：**
```
Filename                  Regions    Missed   Cover   Functions  Missed  Cover    Lines  Missed   Cover
---------------------------------------------------------------------------------------------------------
src/main.cpp                   24         3   87.50%          6       0  100.00%     48       5   89.58%
src/utils.cpp                  15         0  100.00%          4       0  100.00%     30       0  100.00%
---------------------------------------------------------------------------------------------------------
TOTAL                          39         3   92.31%         10       0  100.00%     78       5   93.59%
```

#### 导出为 lcov 格式（与现有工具集成）

```bash
# 导出 lcov 格式，可继续用 genhtml 生成 HTML
llvm-cov export ./my_program \
         -instr-profile=coverage.profdata \
         -format=lcov > coverage.lcov

genhtml coverage.lcov --output-directory coverage_html/
```

---

### 多目标文件处理

当项目有多个共享库或目标文件时：

```bash
# 同时分析主程序和共享库
llvm-cov show ./my_program \
         -object ./libmy_lib.so \
         -instr-profile=coverage.profdata \
         -format=html \
         -output-dir=coverage_html/
```

---

### Clang 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| `profraw` 文件未生成 | 程序提前崩溃未刷新 | 检查崩溃原因；或在代码中调用 `__llvm_profile_write_file()` |
| `llvm-profdata: No such file` | LLVM 工具未在 PATH 中 | 使用完整路径，如 `/usr/lib/llvm-15/bin/llvm-profdata` |
| 符号版本不匹配 | profdata 和 llvm-cov 版本不一致 | 确保使用相同版本的 Clang 和 llvm-cov |
| 覆盖率 100% 但代码明显有未执行路径 | 优化影响 | 确认编译时加了 `-O0` |
| 多进程测试 profraw 相互覆盖 | 默认文件名冲突 | 设置 `LLVM_PROFILE_FILE="test-%p.profraw"` |

---

## 两大体系对比

| 维度 | GCC/gcov | Clang/llvm-cov |
|------|----------|----------------|
| **覆盖率粒度** | 行、函数、分支 | 行、函数、分支、**区域（Region）** |
| **精度** | 中等 | 高（能区分宏内部、模板实例） |
| **工具链** | gcov + lcov + genhtml | llvm-profdata + llvm-cov |
| **中间文件** | `.gcno` + `.gcda` | `.profraw` → `.profdata` |
| **HTML 报告** | genhtml（外部工具） | llvm-cov 内置 |
| **lcov 兼容** | 原生支持 | 需导出（`llvm-cov export -format=lcov`） |
| **编译速度** | 较快 | 略慢（插桩更精细） |
| **跨语言** | C/C++/Fortran | C/C++/ObjC/Swift |
| **适合场景** | 传统 C/C++ 项目，兼容性优先 | 现代项目，精度优先 |

---

## 与 CMake 集成

### GCC 覆盖率 CMake 配置

```cmake
# CMakeLists.txt

option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        message(STATUS "Enabling GCC coverage instrumentation")
        add_compile_options(--coverage -O0 -g)
        add_link_options(--coverage)
    else()
        message(WARNING "Coverage requires GCC compiler")
    endif()
endif()
```

构建命令：
```bash
cmake -B build -DENABLE_COVERAGE=ON
cmake --build build
cd build && ctest
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html/
```

### Clang Source-based Coverage CMake 配置

```cmake
# CMakeLists.txt

option(ENABLE_COVERAGE "Enable Clang source-based coverage" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        message(STATUS "Enabling Clang source-based coverage")
        add_compile_options(
            -fprofile-instr-generate
            -fcoverage-mapping
            -O0
            -g
        )
        add_link_options(-fprofile-instr-generate)
    else()
        message(WARNING "Source-based coverage requires Clang compiler")
    endif()
endif()

# 自定义 target：一键生成报告
if(ENABLE_COVERAGE)
    find_program(LLVM_PROFDATA llvm-profdata REQUIRED)
    find_program(LLVM_COV llvm-cov REQUIRED)

    add_custom_target(coverage
        COMMAND ${CMAKE_COMMAND} -E env
            LLVM_PROFILE_FILE=${CMAKE_BINARY_DIR}/test-%p.profraw
            $<TARGET_FILE:my_tests>
        COMMAND ${LLVM_PROFDATA} merge -sparse
            ${CMAKE_BINARY_DIR}/test-*.profraw
            -o ${CMAKE_BINARY_DIR}/coverage.profdata
        COMMAND ${LLVM_COV} show $<TARGET_FILE:my_tests>
            -instr-profile=${CMAKE_BINARY_DIR}/coverage.profdata
            -format=html
            -output-dir=${CMAKE_BINARY_DIR}/coverage_html
        DEPENDS my_tests
        COMMENT "Generating coverage report..."
    )
endif()
```

使用方法：
```bash
cmake -B build -DCMAKE_CXX_COMPILER=clang++ -DENABLE_COVERAGE=ON
cmake --build build
cmake --build build --target coverage
open build/coverage_html/index.html
```

---

## 与 Makefile 集成

```makefile
# Makefile

CC      = gcc
CXX     = g++
SRCS    = main.cpp utils.cpp
TARGET  = my_program

# 普通构建
$(TARGET): $(SRCS)
	$(CXX) -O2 -o $@ $^

# 覆盖率构建（GCC）
coverage-gcc: clean-cov
	$(CXX) --coverage -O0 -g -o $(TARGET) $(SRCS)
	./$(TARGET)
	lcov --capture --directory . --output-file coverage.info
	lcov --remove coverage.info '/usr/*' --output-file coverage_clean.info
	genhtml coverage_clean.info --output-directory coverage_html
	@echo "Report: coverage_html/index.html"

# 覆盖率构建（Clang）
coverage-clang: clean-cov
	clang++ -fprofile-instr-generate -fcoverage-mapping -O0 -g \
	        -o $(TARGET) $(SRCS)
	LLVM_PROFILE_FILE="coverage.profraw" ./$(TARGET)
	llvm-profdata merge -sparse coverage.profraw -o coverage.profdata
	llvm-cov show ./$(TARGET) -instr-profile=coverage.profdata \
	         -format=html -output-dir=coverage_html
	@echo "Report: coverage_html/index.html"

clean-cov:
	rm -f *.gcda *.gcno *.gcov *.profraw *.profdata coverage.info
	rm -rf coverage_html/

.PHONY: coverage-gcc coverage-clang clean-cov
```

---

## CI/CD 集成实践

### GitHub Actions 示例（GCC + lcov）

```yaml
# .github/workflows/coverage.yml
name: Code Coverage

on: [push, pull_request]

jobs:
  coverage:
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

      - name: Generate coverage report
        run: |
          lcov --capture --directory build \
               --output-file coverage.info
          lcov --remove coverage.info '/usr/*' '*/test/*' \
               --output-file coverage_filtered.info
          lcov --summary coverage_filtered.info

      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage_filtered.info
          fail_ci_if_error: true
```

### GitHub Actions 示例（Clang Source-based）

```yaml
name: Clang Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Clang
        run: sudo apt-get install -y clang llvm

      - name: Build with coverage
        env:
          CC: clang
          CXX: clang++
        run: |
          cmake -B build -DENABLE_COVERAGE=ON
          cmake --build build

      - name: Run tests and collect coverage
        run: |
          LLVM_PROFILE_FILE="build/test-%p.profraw" \
            build/my_tests
          llvm-profdata merge -sparse build/test-*.profraw \
            -o build/coverage.profdata
          llvm-cov export build/my_tests \
            -instr-profile=build/coverage.profdata \
            -format=lcov > coverage.lcov

      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage.lcov
```

---

## 常用工具参考

### 安装汇总

```bash
# Ubuntu/Debian
sudo apt-get install gcc g++ lcov          # GCC 体系
sudo apt-get install clang llvm            # Clang 体系

# macOS（Homebrew）
brew install lcov                          # GCC 体系（Xcode 自带 clang）

# 查看工具版本
gcov --version
lcov --version
llvm-profdata --version
llvm-cov --version
```

### 快速命令速查

```bash
# ── GCC 体系 ──────────────────────────────────────────────
# 编译
gcc --coverage -O0 -g -o prog prog.c

# 收集 & 报告
lcov --capture --directory . -o cov.info
lcov --remove cov.info '/usr/*' -o cov_clean.info
genhtml cov_clean.info -o html_report/

# ── Clang Source-based 体系 ───────────────────────────────
# 编译
clang -fprofile-instr-generate -fcoverage-mapping -O0 -g -o prog prog.c

# 合并
llvm-profdata merge -sparse *.profraw -o cov.profdata

# 终端摘要
llvm-cov report ./prog -instr-profile=cov.profdata

# HTML 报告
llvm-cov show ./prog -instr-profile=cov.profdata \
           -format=html -output-dir=html_report/

# 导出 lcov 格式
llvm-cov export ./prog -instr-profile=cov.profdata \
           -format=lcov > coverage.lcov
```

---

## 决策建议

```
你的项目使用什么编译器？
│
├── GCC ──────────────────────────────────────────────────►  使用 gcov + lcov + genhtml
│                                                             工具成熟，CI 集成简单
│
├── Clang，需要与 GCC/lcov 生态兼容 ──────────────────────►  使用 clang --coverage 模式
│                                                             与 GCC 工具链完全兼容
│
└── Clang，追求最高精度 ───────────────────────────────────►  使用 Source-based Coverage
                                                              -fprofile-instr-generate
                                                              + llvm-profdata + llvm-cov
                                                              区域级精度，报告最详细
```

---

*文档版本：1.0 | 适用 GCC ≥ 9.x，Clang/LLVM ≥ 12.x*

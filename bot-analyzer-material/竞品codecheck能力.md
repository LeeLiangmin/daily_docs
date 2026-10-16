### codecheck
1. 支持规则配置
2. 实时检查
3. 单文件检测
	1. 支持快捷键
	2. 支持 fullcheck/incremental check/ cemetrics check/change file check/
	3. 检测完成打开底部窗口。issue/mr/code metrics check. 同时，支持显示检测了几个规则，多少 warning 以及什么可 auto fix, 什么不可。
4. 支持自文件树上，通过右键菜单呼出的内容做目录下的全量检测(full check/incremental/cmetics)。同样是打开底部的窗口(叫做 code check, 下面分为 issue/mr/code metrics)

code metrics 支持(item/result/threashhold)：
+ code size(non-empty, non-commented)
+ raw lines
+ methods total 
+ cyclomatic complexity total 
+ cylomatic complext per method
+ max cyclomatic complexiy 
+ huge cylomatic complexity ratio 
+ huge cylomatic complexity total 
+ cca cylomtatic complexit total
+ cca cylomatic complexiy per method 
+ maxium cca cylomatic complexity 
+ huga cca cylomatic complexity total 
+ maxim depth
+ maxium lines 
+ lines per method 
+ huge method total 
+ huge method ratio 
+ files total 
+ folders total 
+ linex per file 
+ huge headerfiel total 
+ huge headefile ratio 
+ huge non header file toatal 
+  huge non header file toatal ratio 
+ huge folder ratio 
+ huge depth total 
+ huge depth ratio 
+ file duplication ratio
+ file duplication total 
+ code duplication ratio
+ code duplication total 
+ non hfile code duplication taotal 
+ non hfile code duplicatoin ration 
+ unsafe functions total 
+ reundate code total 
+ warning supperssion total 
+ huge folder threashhold 
+ hugge headerfile threadfold 
+ huge non header threashhold 
+ code duplication threashhold 
+ huge method threashhold 
+ huge cylomataic complexity threashold


### codechecker
|   |
|---|
|# CodeChecker VSCode Plugin<br><br>This is a C/C++ code analysis plugin for VSCode that shows bug reports detected by the [Clang Static Analyzer](http://clang-analyzer.llvm.org/) and [Clang Tidy](http://clang.llvm.org/extra/clang-tidy/) analyzers, using [CodeChecker](https://github.com/Ericsson/codechecker) as a backend.<br><br>![CodeChecker extension](https://github.com/Ericsson/CodeCheckerVSCodePlugin/raw/HEAD/media/codechecker-splash.png)<br><br>## Quick Start<br><br>1. [Install CodeChecker](https://github.com/Ericsson/CodeChecker#install-guide) version 6.18.2 or later, and optionally add it to the `PATH` environment variable.<br>2. Install the CodeChecker extension from the [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=codechecker.vscode-codechecker), from [Open VSX](https://open-vsx.org/extension/codechecker/codechecker), or download manually from [Downloads](https://github.com/Ericsson/CodecheckerVSCodePlugin/releases).<br>3. [Set up your build environment](https://marketplace.visualstudio.com/items?itemName=codechecker.vscode-codechecker#setting-up-your-build-environment) to generate a `compile_commands.json` file.<br>4. Check the path to CodeChecker, and set your preferred command-line arguments - see [Configuring CodeChecker](https://marketplace.visualstudio.com/items?itemName=codechecker.vscode-codechecker#configuring-codechecker) for more information.<br>5. Open your project, and run an analysis, or browse through the found reports!<br><br>## Features<br><br>- Browse through the found reports, and show the reproduction steps directly in the code<br>- Navigate between the reproduction steps (`F9`/`Shift-F9` by default)<br><br>![Showcase of repr steps](https://github.com/Ericsson/CodeCheckerVSCodePlugin/raw/HEAD/media/codechecker-repr-step.gif)<br><br>- Run a CodeChecker analysis from the editor, and see the results automatically<br>- Re-analyze the current file when saved (can be disabled in Settings)<br><br>![File analysis](https://github.com/Ericsson/CodeCheckerVSCodePlugin/raw/HEAD/media/codechecker-analysis.gif)<br><br>- Commands and build tasks for running CodeChecker as part of a build system<br><br>![Commands and tasks](https://github.com/Ericsson/CodeCheckerVSCodePlugin/raw/HEAD/media/codechecker-tasks.gif)<br><br>## Setting up your build environment<br><br>CodeChecker works by reading a generated [compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html), often called `compile_commands.json`, and executing specific analyses based on that.<br><br>`CMake` has built-in support for generating a compilation database. Set the environment variable `CMAKE_EXPORT_COMPILE_COMMANDS=ON`, and the compilation database should be inside your build folder. If you are using the `CMake Tools` extension for VS Code, you can add this flag to the extension settings under `Cmake > Build Environment`.<br><br>`make` and other build systems have no built-in support for generating a compilation database, but CodeChecker can generate one based on the build command. To generate one, you can use the command `CodeChecker log -b "[full build command]" -o .codechecker/compile_commands.json`.<br><br>To automate the process, the extension provides ways to run the `CodeChecker log` command automatically. First, in the Extension Settings set `CodeChecker > Executor > Log build command`, and then use either the VS Code Task, or the VS Code command `CodeChecker: Run CodeChecker Log` to execute the analysis. You can also run `CodeChecker: Preview CodeChecker log in terminal` to have more fine-grained control over the parameters passed to CodeChecker.|


状态栏 CodeCheck
细分 Issues/MR Defect/Code Metrics(CMetric) tab
issues tab
Total checked
9
rules
Total found

0
warnings, including:

0
can be auto-fixed (estimated accuracy>90%)

0
can generate fix code with AI assistance
Beta

0
need manual fix
Select a clustering mode

Export All

Description
Name
Line
Level
Rule
Status
Fix operation
Feedback
No Data

MR Defect
MR名称(编号)
告警数量
创建时间
您当前暂无开启状态的MR

Code Metrics
Export
Indicator Item
Result
Threshold
Code size (non-empty and non-commented) 189 /
Raw lines 207 /
Methods total 40 /
Cyclomatic complexity total 40 /
Cyclomatic complexity per method 1.0 5
Maximum cyclomatic complexity 1 /
Huge cyclomatic complexity total 0 /
Huge cyclomatic complexity ratio 0.0 /
Cca cyclomatic complexity total 40 /
Cca cyclomatic complexity per method 1.0 5
Maximum cca cyclomatic complexity 1 /
Huge cca cyclomatic complexity total 0 /
Maximum depth 1 /
Method lines 0 /
Lines per method 0.0 30
Huge method total 0 50
Huge method ratio 0.0 /
Files total 1 /
Folders total 5 /
Lines per file 189.0 300
Huge headerfile total 0 500
Huge headerfile ratio 0.0 /
Huge non headerfile total 0 2000
Huge non headerfile ratio 0.0 /
Huge folder total 0 50
Huge folder ratio 0.0 /
Huge depth total 0 4
Huge depth ratio 0.0 /
File duplication total 0 /
File duplication ratio 0.0 /
Non hfile duplication total 0 /
Non hfile duplication ratio 0.0 4
Code duplication total 0 /
Code duplication ratio 0.0 10
Non hfile code duplication total 0 /
Non hfile code duplication ratio 0.0 /
Unsafe functions total 0 0
Redundant code total 0 0
Warning suppression total 0 0
Huge folder threshold -- 50
Huge headerfile threshold -- 500
Huge non headerfile threshold -- 2000
Code duplication threshold -- 10
Huge method threshold -- 100
Huge cyclomatic complexity threshold -- 20

右键功能
code check 的侧边栏没图标，通过右键 codecheck 检查。分为：Full check/cmetrics check/incremental check/change files check(sunset)
所有的 check 都打开状态栏下的 tab。

支持在侧边栏文件树上选择目录或者组合选择文件；同时，使用右键有 Full check/cemtres 等的检测。对应的结果还是在状态栏下的对应 tab 页中显示。

对应问题文件没有标注，没有状态栏提示。

非动态感知
必须要通过手动右键才能检测，及时是当的情况
对全部项目没有感知

不支持独立度量某个函数或者impl 等
某个函数或者文件有问题无法感知到。需要等到手动才能获得
Activity
LeeLiangmin commented now
@LeeLiangmin
LeeLiangmin
1m ago
Owner
Author
支持特性
支持检查的语言：C、C++、Java、Python、Lua、JavaScript、TypeScript、Go(只支持文件夹检查)、ArkTS、Rust、Microcode；
集成三大静态检查引擎：PcLint 、 CodeCheck 和 Secbrella(SecA,SecB)；
CodeCheck检查引擎包含CodeMars、CodingStyle、Cmetrics、Anystandard、codecheckrevive、 Pclint Plus、Clippy、Fixbot能力;
集成代码缺陷修复引擎：FixBot;
支持单文件及目录检查；
支持基于变更文件/代码检查；
支持基于MR的静态检查；
支持linux环境;
支持实时静态检查（仅linux环境）；
检查规则根据打开的代码仓进行线上自动匹配；
线上仓库规则模式下自动拉取线上规则；
静态检查工具工具包自动更新推送；
功能介绍
一、CodeCheck

配置
从WeCode左边的侧边栏进入WeCode菜单，在配置里面点击WeCode配置，进入配置页面
在配置页面中，点击CodeCheck配置，进入规则页面

模式分为手动模式和自动模式两种，自动模式自动拉取流水线执行的CodeCheck任务，手动模式支持规则自定义配置

手动模式配置规则分线上仓库规则远端规则和工具内置规则本地规则两种，其中线上仓库规则需要预先配置CodeCheck任务，配置可参考文工具内置规则本地规则则支持自定义配置

CodeCheck_config.gif

实时检查
在linux环境上（wecode-online、linux VM环境）, 实时检查自动生效，实现实现键入即检查的效果（使用的检查规则集自动切换）
realtimeCheck.gif

CodeCheck单文件检查
打开源文件后,在右键菜单中选择Code Check二级菜单全量检查/增量检查，或者用快捷键 ctrl+alt+c
检查完成后，会新建一个底部窗口，输出发现的问题列表

点击一个告警项，左侧窗口的光标会跳到对应行。并且行首有波浪线。光标移到波浪线处时，会提示CodeCheck告警的详细信息

CodeCheck目录检查
在左边的侧边栏进入EXPLORER菜单，点击要检测的目录，右键菜单中选择Code Check二级菜单全量检查/增量检查
CodeCheck检查完成后，会新建一个底部窗口，列出此目录发现的所有问题列表

三、对变更文件做静态检查
打开源文件后，在右键菜单中选择Code Check二级菜单基于变更文件检查

WeCode会新建一个右侧窗口，并从git库中获取差异文件列表，这可能会比较耗时

选择要检查的文件和要做的静态检查，再点击开始检查

在右侧窗口中显示各个静态检查工具的输出列表

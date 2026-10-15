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


### Huawei Cloud CodeArts Check
https://marketplace.visualstudio.com/items?itemName=HuaweiCloud.codecheck
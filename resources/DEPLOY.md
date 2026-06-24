# 部署与打包指南

> 本指南面向业务部署人员，说明如何构建、验证、对比打包脚本版本，以及如何发布给最终用户。

---

## 目录

- [一、环境准备](#一环境准备)
- [二、打包步骤](#二打包步骤)
- [三、输出说明](#三输出说明)
- [四、部署给业务用户](#四部署给业务用户)
- [五、如何查看 build.bat 不同版本之间的差异](#五如何查看-buildbat-不同版本之间的差异)
- [六、常见问题](#六常见问题)

---

## 一、环境准备

### 1.1 开发机环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 |
| Python | 3.8+（建议 3.10） |
| Git | 任意版本 |
| 磁盘空间 | 剩余空间 ≥ 5 GB（含 JRE + venv） |

### 1.2 拉取代码

```bash
git clone <仓库地址>
cd pr_study
git checkout <目标分支>
```

### 1.3 确认源码结构

```
pr_study/
├── GUI.py                    # GUI 入口
├── PRStudy.spec              # PyInstaller 打包配置
├── build.bat                 # 一键打包脚本（本指南重点）
├── pytest.ini                # pytest 配置
├── conftest.py               # pytest 全局夹具
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖
├── config.ini                # GUI 配置（自动生成，不用提交）
├── data/                     # YAML 业务配置
├── api/                      # API 封装
├── core/                     # HTTP 客户端
├── workflows/                # 流程编排
├── testcases/                # 测试用例
└── resources/                # 运行时资源
    ├── jre/                  # Java 运行环境
    ├── allure/               # Allure 工具集
    └── README.md             # 用户手册（随包输出）
```

---

## 二、打包步骤

### 2.1 基础打包

双击 `build.bat`，或命令行执行：

```powershell
.\build.bat
```

脚本会依次执行：

1. **检查 Python 环境**，缺失则安装
2. **检查 PyInstaller**，缺失则安装
3. **清理旧构建** `build/` 目录
4. **准备运行时资源**（检查 `resources\jre`、`resources\allure`）
5. **执行 PyInstaller 打包** `PRStudy.spec`
6. **复制 venv** `.venv → dist\PRStudy\venv`（提高可移植性）
7. **复制 testcases** 到 `dist\PRStudy\testcases`
8. **复制用户手册** `resources\README.md → dist\PRStudy\README.md`
9. **创建 report 目录** `dist\PRStudy\report\allure-results`
10. **询问是否生成 ZIP**，输入 `Y` 生成 `dist\PRStudy-v1.0.zip`

### 2.2 带 venv 的打包（推荐）

`build.bat` 会自动复制 `.venv` 到 `dist\PRStudy\venv`，使下游用户在无 Python 环境的机器上也能直接运行：

```powershell
# 如打包机已有 .venv，脚本会自动复制
# 如无 .venv，下游用户机器需安装 Python + 依赖
```

### 2.3 增量构建（仅更新业务代码）

如果仅修改了 `data/` 或 `workflows/` 部分，可减少测试用例复制：

```powershell
:: 手动指定 testcases 子集
robocopy "testcases\order" "dist\PRStudy\testcases\order" /E
robocopy "testcases\receive" "dist\PRStudy\testcases\receive" /E
```

---

## 三、输出说明

### 3.1 目录结构

```
dist/
├── PRStudy/                  # 主输出目录
│   ├── PRStudy.exe           # 主程序（启动器）
│   ├── _internal/            # PyInstaller 打包内容
│   │   ├── jre/              # Java 运行环境
│   │   ├── allure/           # Allure 工具集
│   │   ├── api/              # API 层
│   │   ├── data/             # 数据层
│   │   ├── workflows/        # 流程编排层
│   │   ├── testcases/        # 测试用例层
│   │   ├── core/             # 核心模块
│   │   ├── utils/            # 工具类
│   │   └── config/           # 配置模块
│   ├── venv/                 # Python 虚拟环境（可选）
│   ├── testcases/            # 测试用例（独立副本）
│   ├── report/               # 测试报告输出目录
│   │   └── allure-results/   # Allure 结果
│   └── README.md             # 用户手册
└── PRStudy-v1.0.zip          # 压缩包（可选生成）
```

### 3.2 关键文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `PRStudy.exe` | 主程序，双击启动 GUI |
| `_internal/` | PyInstaller 打包产物，含 Python 运行时和业务代码 |
| `_internal/jre/` | Java 运行环境，供 Allure 生成报告使用 |
| `_internal/allure/` | Allure 工具集 |
| `venv/` | Python 虚拟环境（包含所有依赖包） |
| `testcases/` | 独立副本，供二次开发或排查问题 |
| `report/` | 测试结果输出目录，运行时生成 |
| `README.md` | 业务用户手册，介绍目录结构和使用方法 |
| `PRStudy-v1.0.zip` | 一键发布包，直接发给业务用户 |

---

## 四、部署给业务用户

### 4.1 交付物

交付给业务用户，只需提供 **一个 ZIP 包**：

```
PRStudy-v1.0.zip
```

内含完整可运行目录：

```
PRStudy/
├── PRStudy.exe              # 双击启动
├── _internal/               # 运行时依赖
├── venv/                    # 可移植 Python
├── testcases/               # 测试用例
├── report/                  # 报告目录
└── README.md                # 使用手册
```

### 4.2 业务用户操作步骤

1. 解压 `PRStudy-v1.0.zip` 到任意目录
2. 双击 `PRStudy.exe` 启动 GUI
3. 填写接口地址、账号密码、用户ID
4. 选择链路，点击「开始测试」
5. 测试完成后，报告在 `report\allure-results\`

### 4.3 环境要求

业务用户 **无需安装 Python 或 Java**，如打包时 `.venv` 已被复制进包内，则开箱即用。

如 `.venv` 缺失，业务用户需要：
- 安装 Python 3.8+
- 安装依赖：`pip install -r requirements.txt`

---

## 五、如何查看 build.bat 不同版本之间的差异

### 5.1 在 Git 仓库中对比

如果 `build.bat` 已提交到 Git，可直接用 Git 命令对比任意两个版本：

```bash
# 查看最近一次 build.bat 的改动
git diff HEAD~1 -- build.bat

# 对比任意两个提交之间的 build.bat 差异
git diff <commit_A> <commit_B> -- build.bat

# 查看 build.bat 的修改历史
git log --oneline -- build.bat
```

### 5.2 人工 diff（未提交版本）

如果当前修改未提交，可用文本对比工具：

| 工具 | 用法 |
|------|------|
| VS Code | 打开 `build.bat` → 源控制 → 对比文件 |
| WinMerge | 打开旧版文件和新版文件对比 |
| Beyond Compare | 右键文件夹 → New Session → Text Compare |
| 命令行（PowerShell） | `Compare-Object (Get-Content build.bat.old) (Get-Content build.bat.new)` |

### 5.3 常见差异点清单

| 关注点 | 说明 |
|--------|------|
| 新增环境检测逻辑 | 如新增 Python 版本检查、依赖预检 |
| 新增资源复制步骤 | 如新增 README、report 目录创建 |
| 新增 ZIP 打包逻辑 | 是否加入 `setlocal enabledelayedexpansion`、PowerShell 压缩命令 |
| 路径变更 | 如 `dist\` 改为 `output\` |
| 新增参数 | 是否支持命令行传参（如 `build.bat --no-zip`） |

---

## 六、常见问题

### Q1: 打包后 ZIP 未生成？

**原因**：`build.bat` 缺少 `setlocal enabledelayedexpansion`，导致 `!CREATE_ZIP!` 变量无法展开。  
**修复**：确认脚本开头包含 `setlocal enabledelayedexpansion`。

### Q2: 业务用户打开 PRStudy.exe 闪退？

**排查**：
1. 检查 `dist\PRStudy\_internal\` 目录是否完整（jre/allure 都在）
2. 确认业务用户机器是否有杀毒软件拦截
3. 尝试命令行启动查看错误信息：`PRStudy.exe`

### Q3: Allure 报告生成失败？

**排查**：
1. 确认 `_internal/jre/` 目录存在
2. 确认 `report/allure-results/` 目录下有 JSON 结果文件
3. 手动运行：`_internal/allure/bin/allure.bat serve report/allure-results`

### Q4: 如何更新用户手册？

业务用户手册位置：`resources/README.md`，修改后重新打包即可自动复制到 `dist\PRStudy\README.md`。

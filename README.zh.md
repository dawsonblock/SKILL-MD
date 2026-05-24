# 受 Karpathy 启发的编码代理指南

> 本项目与 Andrej Karpathy 无关，也未得到其认可。

一个面向编码代理的小型指令包，灵感来自 Andrej Karpathy 对 LLM 编码陷阱的公开观察。

[English](./README.md) | 简体中文

## 问题所在

来自 Andrej 的推文：

> "模型会代你做错误假设，然后不假思索地执行。它们不管理自身的困惑，不寻求澄清，不呈现矛盾，不展示权衡，在应该提出异议时也不反驳。"

> "它们真的很喜欢把代码和 API 搞复杂，堆砌抽象概念，不清理死代码……明明 100 行能搞定的事情，非要实现成 1000 行的臃肿架构。"

> "它们有时仍会改动或删除自己理解不足的代码和注释，即使这些内容与任务本身无关。"

## 解决方案

四个原则，集中在一个文件中，直接解决这些问题：

| 原则 | 解决什么问题 |
|-----------|-----------|
| **编码前思考** | 错误假设、隐藏困惑、缺少权衡 |
| **简洁优先** | 过度复杂、臃肿抽象 |
| **精准修改** | 无关编辑、触碰不应碰的代码 |
| **目标驱动执行** | 通过测试优先、可验证的成功标准 |

## 四个原则详解

### 1. 编码前思考

**不要假设。不要隐藏困惑。呈现权衡。**

LLM 经常默默选择一种解释然后执行。这个原则强制明确推理：

- **在影响正确性的情况下明确说明假设** —— 只在假设会影响实现正确性时说明。
- **当证据充分时，从代码、测试、文档和用户上下文中推断** —— 不要为了显而易见的信息反复提问。
- **只有在缺少信息会阻碍正确实现时才询问** —— 澄清应解决阻塞，而不是代替判断。
- **呈现多种解释** — 当存在歧义时，不要默默选择
- **适时提出异议** — 如果存在更简单的方法，说出来
- **如果检查可用证据后仍不清楚，应指出阻塞点并询问。**

### 2. 简洁优先

**用最少的代码解决问题。不要过度推测。**

对抗过度工程的倾向：

- 不要添加要求之外的功能
- 不要为一次性代码创建抽象
- 不要添加未要求的"灵活性"或"可配置性"
- 不要添加宽泛的臆测式错误处理
- 处理由代码路径、测试、接口或领域实际显示出的现实失败模式
- 如果 200 行代码可以写成 50 行，重写它

**检验标准：** 资深工程师会觉得这过于复杂吗？如果是，简化。

### 3. 精准修改

**只碰必须碰的。只清理自己造成的混乱。**

编辑现有代码时：

- 不要"改进"相邻的代码、注释或格式
- 不要重构没坏的东西
- 匹配现有风格，即使你更倾向于不同的写法
- 如果注意到无关的死代码，提一下 —— 不要删除它

当你的改动产生孤儿代码时：

- 删除因你的改动而变得无用的导入/变量/函数
- 不要删除预先存在的死代码，除非被要求

**检验标准：** 每一行修改都应该能直接追溯到用户的请求。

### 4. 目标驱动执行

**定义成功标准。循环验证直到达成。**

将指令式任务转化为可验证的目标：

| 不要这样做... | 转化为... |
|--------------|-----------------|
| "添加验证" | "为无效输入编写测试，然后让它们通过" |
| "修复 bug" | "编写重现 bug 的测试，然后让它通过" |
| "重构 X" | "确保重构前后测试都能通过" |

对于多步骤任务，说明一个简短的计划：

```
1. [步骤] → 验证: [检查]
2. [步骤] → 验证: [检查]
3. [步骤] → 验证: [检查]
```

强有力的成功标准让 LLM 能够独立循环执行。弱标准（"让它工作"）需要不断澄清。

## 安装

**选项 A：Claude Code 插件（推荐）**

在 Claude Code 中，首先添加插件市场：
```
/plugin marketplace add forrestchang/andrej-karpathy-skills
```

然后安装插件：
```
/plugin install andrej-karpathy-skills@karpathy-skills
```

这会将指南安装为 Claude Code 插件，使其在你所有项目中可用。

**选项 B：CLAUDE.md（按项目）**

新项目：
```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md
```

已有项目（追加）：
```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

## 在 Cursor 中使用

本仓库包含一个已提交的 Cursor 项目规则 ([`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc))，因此在 Cursor 中打开项目时同样适用这些指南。详情请参见 **[CURSOR.md](CURSOR.md)**，包括如何在其他项目中使用该规则，以及它与 Claude Code 的关系。

共享指南的规范内容位于 **[`docs/guidelines.md`](docs/guidelines.md)**。面向不同工具的文件由 **[`scripts/sync_guidelines.py`](scripts/sync_guidelines.py)** 生成。

## 支持的编码代理目标

规范指南正文位于：

```text
docs/guidelines.md
```

生成目标包括：

- [CLAUDE.md](CLAUDE.md)（Claude Code 项目级指令）
- [.cursor/rules/karpathy-guidelines.mdc](.cursor/rules/karpathy-guidelines.mdc)（Cursor 规则）
- [.github/copilot-instructions.md](.github/copilot-instructions.md)（VS Code Copilot 仓库级指令）
- [skills/karpathy-guidelines/SKILL.md](skills/karpathy-guidelines/SKILL.md)（技能式分发）

不要直接编辑生成文件正文。请修改 [docs/guidelines.md](docs/guidelines.md) 后运行：

```bash
python3 scripts/check.py
```

## 核心洞察

来自 Andrej：

> "LLM 非常擅长循环执行直到达成特定目标……不要告诉它该做什么，给它成功标准，然后看着它完成。"

"目标驱动执行"原则正是捕捉了这一点：将指令式指令转化为带有验证循环的声明式目标。

## 如何判断它在起作用

如果你看到以下情况，说明这些指南正在发挥作用：

- 更小、更聚焦的代码差异。
- 只有在正确性受阻时才提出必要澄清问题。
- 只在影响实现正确性时明确说明假设。
- 在声称完成前运行验证命令。
- 清楚报告修改文件、验证结果和剩余失败项。

## 定制

这些指南设计用于与项目特定指令合并。将它们添加到你现有的 `CLAUDE.md` 或创建一个新的。

对于项目特定规则，添加如下章节：

```markdown
## 项目特定指南

- 使用 TypeScript 严格模式
- 所有 API 端点必须有测试
- 遵循 `src/utils/errors.ts` 中现有的错误处理模式
```

## 权衡说明

这些指南倾向于**谨慎而非速度**。对于琐碎的任务（简单的拼写错误修复、显而易见的一行修改），请自行判断 —— 并非每个改动都需要完整的严谨流程。

目标是减少非琐碎工作中的代价高昂的错误，而不是拖慢简单任务。

## 开发

规范指南正文位于：

```text
docs/guidelines.md
```

修改后先生成派生文件：

```bash
python3 scripts/sync_guidelines.py
```

再检查同步和校验：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_guidelines.py --check
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
```

也可以用一个命令执行完整检查：

```bash
python3 scripts/check.py
```

也可以一键构建并验证发布压缩包：

```bash
python3 scripts/package_release.py
```

该命令会生成 `dist/SKILL-MD-main-fixed.zip`，解压到临时目录，并在解压副本中再次运行 `scripts/check.py`。

## 发布检查

发布 ZIP 前运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/package_release.py
```

输出位置：`dist/SKILL-MD-main-fixed.zip`

## 源码包与发布包

不要把 `dist/` 下生成的发布 ZIP 提交到源码包中。

按用途使用以下命令：

- 发布包（自动生成并验证）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/package_release.py
```

- 源码包打包前（先清理生成产物）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/clean.py
```

- 提交前校验：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
```

`PYTHONDONTWRITEBYTECODE=1` 会阻止 Python 生成 `__pycache__` 和 `.pyc` 文件；这些缓存文件会被仓库验证拒绝。

该脚本会检查插件 JSON、Cursor frontmatter、必需的指南章节，以及过时措辞是否仍然存在。

生成的文件包括：

- `CLAUDE.md`
- `.cursor/rules/karpathy-guidelines.mdc`
- `.github/copilot-instructions.md`
- `skills/karpathy-guidelines/SKILL.md`

## 可选 Lint 工具

本仓库在 `.trunk/` 目录下提供了可选的 Trunk 配置，使用或贡献本指令包均不需要它。

核心检查仅需 Python 脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py
```

Trunk 是面向贡献者的本地可选工具，未接入 CI 流程。
当前环境未验证 Trunk 执行结果。

## 许可

MIT —— 参见 [LICENSE](LICENSE)。

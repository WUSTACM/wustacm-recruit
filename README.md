# 第一次向招新仓库提交 Pull Request

任务：**用仓库里的工具加密你的通知邮箱，再把生成的 `.age` 文件提交给 wustLABA**。

我们之后会用这个邮箱发送面试通知。

## 0. 准备

你需要一个 GitHub 账号和 Git。Windows 可从 [Git 官网](https://git-scm.com/download/win)安装；

macOS 可先在“终端”里运行 `git --version`，若系统提示安装命令行开发者工具，按提示完成。

安装 Git 后，Windows 打开 PowerShell，macOS 打开“终端”，输入：

```sh
git --version
```

如果能看到版本号，就可以继续。

## 1. Fork 仓库

打开招新组发布的原仓库，点页面右上角的 **Fork**，将仓库复制到你自己的 GitHub 账号下。

<img src="images/fork-current.png" width="460" alt="GitHub 仓库页面中标出的 Fork 按钮" />

完成后，浏览器地址应类似：

```text
https://github.com/你的GitHub用户名/wustlaba-recruit
```

## 2. Clone 到电脑

在**你自己的 Fork** 页面点击绿色 **Code** 按钮，选择 **HTTPS**，复制仓库地址。

<img src="images/clone-https-current.png" width="680" alt="GitHub Code 菜单中选中 HTTPS 并标出复制地址按钮" />

截图中的 `jiangescn` 是示例用户名；你复制的地址应显示**你自己的 GitHub 用户名**。然后在 PowerShell 或 macOS“终端”中运行：

```sh
git clone <刚才复制的 HTTPS 地址>
cd wustlaba-recruit
```

例如，截图中的用户名是 `jiangescn`，地址就是 `https://github.com/jiangescn/wustlaba-recruit.git`。命令中的引号可以保留。

## 3. 创建分支

```sh
git switch -c submit-email
```

分支让这次提交与主线分开，等待负责人审核。

## 4. 生成加密文件

在仓库目录中，按自己的系统运行下面**一条**命令：

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\submit.ps1
```

macOS“终端”：

```sh
bash ./submit.sh
```

脚本会从你 Clone 的 Fork 地址识别 GitHub 用户名，然后提示输入通知邮箱。成功后会显示一个文件名，例如：

```text
submissions/2026/jiangescn.age
```

这个文件是加密后的内容。**不要把邮箱明文写进仓库文件、Commit 信息或 PR 描述。**

## 5. Commit 并 Push

先看这次改了什么：

```sh
git status
```

你应能看到 `submissions/2026/你的用户名.age`（年份按提交时的当前年份自动确定）。下图里的 `jiangescn` 只是示例：

![git status 和只添加加密文件的示意图](images/git-status.svg)

将下面命令中的 `jiangescn` 换成脚本显示的文件名对应的用户名：

```sh
git add submissions/2026/jiangescn.age
git commit -m "Submit encrypted email"
git push -u origin submit-email
```

如果 `git commit` 提示未设置身份，按提示设置 `user.name` 与 `user.email`，再重试 Commit。Push 时按 Git 显示的认证提示登录 GitHub；若终端要求输入密码，GitHub 需要使用[个人访问令牌](https://docs.github.com/en/get-started/git-basics/why-is-git-always-asking-for-my-credentials)，不能输入 GitHub 账号密码。

## 6. 创建 Pull Request

回到你自己的 Fork 页面，通常会看到 **Compare & pull request** 按钮：

<img src="images/compare-pr-current.png" width="820" alt="个人 Fork 页面上标出的 Compare & pull request 按钮" />

点击后确认：

- **base repository**：`wustLABA/wustlaba-recruit`
- **base branch**：`main`
- **head repository**：你自己的 Fork
- **compare branch**：`submit-email`

如果 GitHub 自动选中其他目标仓库，请将 **base repository** 改为 `wustLABA/wustlaba-recruit`。

标题可写 `Submit encrypted email`，描述可写 `已按教程提交加密邮箱`。最后点击 **Create pull request**。

负责人会检查并合并。如果收到评论，请直接在原 PR 里回复；需要重做加密文件时，重新运行第 4 步中对应系统的脚本，再 Commit 和 Push 到同一个分支，PR 会自动更新。

## 遇到问题

- 请在issue中提问，这里是你唯一可以获取关于这次作业帮助的地方

---

# 新生参与流程：加入 LABA 并完成第一次贡献

上面这一步（提交加密邮箱）是**招新作业**。下面要介绍的，是加入我们社团的完整路径：**加入 wustLABA 组织 → 获得项目权限 → 完成你的第一次 GitHub 贡献**。

没接触过 Git 和 GitHub 也完全没问题，跟着做就行。整个过程大约 20 分钟。

## 一、先理解两件事

**第一，GitHub 是什么？**

GitHub 是程序员共享代码的地方。每个人都把自己的代码放上去，别人可以看到、可以提建议、也可以一起改。我们社团的项目都放在 GitHub 上。

**第二，我们为什么要你走一遍这个流程？**

因为这是真实的协作方式。你以后参与社团项目时，每天做的事情就是这样：把代码拉下来、改一改、提交上去、让别人审查。先走一遍最简版本，后面就不陌生了。

## 二、权限是怎么来的？

这里有个概念要提前说清楚，能帮你少走弯路：

```text
wustLABA Organization（我们的组织）
        ↓
LABA-Members Team（成员团队）
        ↓
项目权限：可以修改某些仓库
   ├─ first-contributions
   ├─ wustlaba-recruit（就是本仓库）
   └─ 其他社团项目
```

你申请的**是加入组织**，而不是某个单独仓库的权限。加入组织后你会自动进入 **LABA-Members** 团队，从而获得团队当前已配置的那批仓库的写权限。

所以：**不是"申请一个仓库、批一个仓库"**，而是一次加入、后续都能参与。今后社团新增项目时，管理员把仓库挂到团队上即可，你无需重新申请。

## 三、申请加入组织

### 第一步：打开申请页面

进入 **first-contributions** 仓库的申请页面：

<https://github.com/wustLABA/first-contributions/issues/new?template=laba-contribution-access.yml>

你也可以先进仓库首页 <https://github.com/wustLABA/first-contributions>，点 **Issues → New issue**，再选择「申请加入 wustLABA Organization」。

### 第二步：勾选确认框，提交

页面上**只有一个地方需要你操作**：勾选那个确认框，然后点 **Submit new issue**。

你**不需要**填写 GitHub 用户名、姓名、学号、班级或邮箱——系统会自己读取你的账号。

> ⚠️ **这个 Issue 是公开的，所有人都能看到。**
> 请**不要**在里面填写姓名、学号、班级、手机号、邮箱等任何隐私信息；
> 也**绝对不要**提交密码、Token、身份证号之类的敏感内容。

### 第三步：等待机器人处理

提交后通常几秒内就会有回复：

| 你看到的内容 | 意思 |
| --- | --- |
| 组织加入申请已处理 | 成功，邀请已发出，去接受就行 |
| 待接受的组织邀请 | 你之前申请过还没接受，去接受即可，不会重复发 |
| 你已经是组织成员 | 你已经在里面了，无需重复申请 |

处理成功后，这个 Issue 会自动关闭。

### 第四步：接受邀请（最容易卡住的一步）

去下面任一位置接受邀请：

- **GitHub 网页**：右上角的通知铃铛 🔔
- **你的邮箱**：找一封来自 GitHub 的邀请邮件
- **直接打开**：<https://github.com/orgs/wustLABA/invitation>

> ⚠️ **没有接受邀请之前，你 `git push` 会失败，报 `403 Permission denied`。**
> 这是最常见的问题。遇到 403，先回来确认邀请接受了没有。
>
> 另外，接受之后权限可能还要**等几秒到几分钟**才生效。刚接受就报错，稍等一下再试。

## 四、完成你的第一次贡献

接受邀请后，来做你的第一次真实贡献。

> 💡 **注意：这里不需要 Fork。**
> 你已经是组织成员了，直接把分支推到官方仓库即可。这和你在网上看到的很多教程不一样，因为那些教程是给"没有权限的外部贡献者"写的。

```bash
# 1. 把仓库下载到本地（直接 clone 官方仓库）
git clone https://github.com/wustLABA/first-contributions.git
cd first-contributions

# 2. 创建一个属于你自己的分支（分支名带上你的标识，避免和别人撞名）
git checkout -b laba/你的名字

# 3. 创建你的报名文件
#    路径和文件名有约定格式，具体见仓库内说明
mkdir -p docs/laba
# 然后用编辑器创建 docs/laba/你的GitHub用户名.md

# 4. 提交
git add .
git commit -m "docs: add 你的GitHub用户名 LABA registration"

# 5. 推送你的分支
git push -u origin laba/你的名字
```

推送成功后，终端会直接给你一个创建 Pull Request 的链接。也可以打开 <https://github.com/wustLABA/first-contributions/pulls>，点 **New pull request**，选择你的分支，填好说明后提交。

**Pull Request（简称 PR）是什么？** 就是你向项目提交修改建议的方式。你改好了，说一声"我改完了，你们看看要不要收下"，负责人审核后就会合并进主项目。

这一步完成，你的第一次开源贡献就达成了 🎉

## 五、常见问题

### Q：为什么我看的教程都要先 Fork，这里却不用？

因为你是**组织成员**，对仓库本来就有写权限，可以直接建分支推送。Fork 是给没有任何权限的外部人用的替代方案。你以后给别人的开源项目提贡献时，才需要 Fork。

### Q：我提交申请了，为什么还是没有权限？

按顺序检查两件事：

1. **接受组织邀请了吗？** 去 <https://github.com/orgs/wustLABA/invitation> 看看。没接受就 push，一定会 403。
2. **等够时间了吗？** 接受之后权限生效有延迟，等几分钟再试。

### Q：收不到邀请怎么办？

依次检查：

- **GitHub 通知**：点网页右上角的铃铛 🔔
- **注册邮箱**：翻一下垃圾邮件文件夹，发件人是 GitHub
- **申请 Issue 的状态**：回到你提交的那个 Issue，看机器人回复了什么

如果 Issue 上标着失败标签，说明需要管理员人工处理，**等着就好，不要重复开新的 Issue**。

### Q：`git push` 报 403 Permission denied

三个原因，按顺序排查：

1. **还没接受邀请** —— 最常见，见上面的说明
2. **推错分支了** —— 确认你推的是自己的分支，不是 `main`
3. **本地凭据过期** —— 清除后重试：`git credential-manager erase`

### Q：我可以提交多次申请吗？

可以，但**不会重复收到邀请**。系统会认出来你已经有一条待接受的邀请，然后提醒你去接受。如果你已经在组织里，它会告诉你无需重复申请。

### Q：我能写哪些仓库？

LABA-Members 团队当前挂载的仓库。目前包括 `first-contributions`、`wustlaba-recruit` 等。加入组织后这些都会对你开放，具体范围由管理员维护。

### Q：我有问题可以开 Issue 问吗？

`first-contributions` 仓库为了保持申请流程的可识别性，**关闭了自由格式的 Issue**。需要帮助时，请到**本仓库** <https://github.com/wustLABA/wustlaba-recruit/issues> 提问——这里是你获取帮助的地方。

---

**完整的中文详细指南**（含给管理员的配置说明）见：
<https://github.com/wustLABA/first-contributions/blob/main/docs/zh-CN/laba-access.md>

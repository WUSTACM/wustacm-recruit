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

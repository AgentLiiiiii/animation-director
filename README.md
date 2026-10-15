# 迪士尼风格动画导演 · Animation Director

将「场景图 + 角色图 + 一两句话的情节」转化为动作清晰、富有弹性、镜头节奏鲜明的动画视频提示词。

结合经典动画十二原则与电影分镜，先设计角色怎么演，再设计观众怎么看。适用于角色表演、动作喜剧、参考图动画化和已有视频提示词的修改。

## 安装

把下面这句话复制给支持 Skill 安装的 Agent：

```text
请帮我安装这个迪士尼风格动画导演 Skill：https://github.com/AgentLiiiiii/animation-director
```

本仓库根目录即为技能目录，入口是 [SKILL.md](SKILL.md)。安装时请同时保留 `references/`、`scripts/` 和 `agents/`。

## 使用

安装后，向 Agent 提供：

1. 场景图；
2. 角色图（可以与场景在同一张图中）；
3. 一两句话的情节描述。

时长、画幅、对白、目标模型可按需要补充。每次设计一个 **4–30 秒**的提示词单元，输出「画面内容、时间线、全局约束」三项。

### 使用示例：小猫追蝴蝶

先将下方两张参考图上传给 Agent：图 1 用于角色设定，图 2 用于院子场景。点击缩略图可查看图片。

<table>
<tr>
<th>图 1：角色参考 · 奶奶与小猫</th>
<th>图 2：场景参考 · 院子</th>
</tr>
<tr>
<td align="center"><img src="https://github.com/user-attachments/assets/43cabc86-0861-476f-b74e-0e7238a94c97" height="200" alt="图1：奶奶与小猫角色参考"></td>
<td align="center"><img src="https://github.com/user-attachments/assets/a6af4d17-35ed-434e-9611-8a4f77ecb916" height="200" alt="图2：院子场景参考"></td>
</tr>
</table>

上传图片后，复制下面的情景输入：

```text
请使用 animation-director，图1是角色参考，图2是场景参考。

情景描述：
小猫从院子门外追着一只蝴蝶跑进院子内，蝴蝶在院子中央的空中盘旋，
小猫在地上跟着转圈，蝴蝶高高飞起，落在了屋檐边缘。
小猫奋力起跳，结果打翻了房屋旁晾晒的辣椒。
这时奶奶从屋内走出来，抱起地上的小猫，轻轻摸着它的头，问他摔伤了没有，
但小猫的表情依旧是非常不耐烦地盯着空中的蝴蝶，有些恼怒
```

## 演示短片

**肥猫与蝴蝶 · 横屏 · 15 秒**

<img src="https://github.com/user-attachments/assets/ee79f7c3-c34b-4577-9294-344868a6afd0" width="480" alt="肥猫与蝴蝶演示封面">

<details>
<summary>▶ 点击展开播放器</summary>

https://github.com/user-attachments/assets/bebda8ef-c458-433f-b5fe-a4be94ce7e21

</details>

## 能力与边界

- 动画表演：意图、预备动作、关键姿势、重量、弹性、惯性跟随与回弹。
- 摄影分镜：景别变化、运镜起止、剪辑节拍、注意目标与动作连续性。
- 提示词检查：附带 Python 3 结构与时间码校验脚本；脚本只检查结构和时间，不评价动画质量。
- 本 Skill 交付文字导演方案与提示词；视频生成需使用相应视频模型，效果取决于素材、模型及执行情况。

“迪士尼风格”指动画表演方法与美学参考；本项目并非迪士尼官方产品，与迪士尼或皮克斯无隶属、授权或背书关系。

## 使用许可

允许安装、使用以及为自身使用进行修改；允许将使用本 Skill 创作的作品用于商业项目。

**未经作者书面授权，禁止将本 Skill 及其修改版单独转售、打包收费分发、作为付费会员资源提供，或改名后转售。**

完整条款见 [LICENSE.md](LICENSE.md)。本项目采用自定义使用许可。

## 文件结构

- `SKILL.md`：主指令
- `references/`：动画表演、角色动势、摄影及交付参考
- `scripts/`：提示词结构校验与测试
- `agents/openai.yaml`：Agent 展示配置

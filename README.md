# 梗体中文 · 在线打包

这里是在线打包部署部分，若要更新内容请前往[基岩版仓库](https://github.com/Teahouse-Studios/mcwzh-meme-resourcepack-bedrock/)或[Java版仓库](https://github.com/Teahouse-Studios/mcwzh-meme-resourcepack/)。

## 服务端搭建

clone本仓库后，请额外clone Java版和基岩版的内容。

``` bash
git clone https://github.com/Teahouse-Studios/mcwzh-meme-web-builder-server/
git clone https://github.com/Teahouse-Studios/mcwzh-meme-resourcepack meme-pack-java
git clone https://github.com/Teahouse-Studios/mcwzh-meme-resourcepack-bedrock meme-pack-bedrock
```

运行网页构建环境要求Python版本最低为**3.9**（推荐使用最新的稳定版），Node.js尽量保持最新版本，并安装依赖：

``` bash
pip install -r requirements.txt
```

如果您有需要, 可将`config.example.ini`复制至`config.ini`修改配置，配置内容说明如下。

``` ini
[MEME]
PULLING_WHEN_BUILD=false # 构建时拉取基岩版和Java版更新(间隔60秒)
USE_GITHUB_WEBHOOK=false # 启用Github Webhook进行更新
# 如您有fork的java版仓库或基岩版仓库，并保持更新，建议启用此项
# 创建Webhook至/github Content-Type为json Secret在下方定义 设置Just the push event.
GITHUB_SECRET=
```

设置完成后，即可启动web服务器

``` bash
python online_builder.py
```

## 网页搭建

`git clone https://github.com/Teahouse-Studios/mcwzh-meme-web-builder`

``` bash
# 选择包管理器：npm / yarn
# npm
npm install
# yarn
yarn install
```

如何安装，构建Vue项目此处不再赘述，新手建议使用[Vue GUI](https://cli.vuejs.org/zh/guide/creating-a-project.html#%E4%BD%BF%E7%94%A8%E5%9B%BE%E5%BD%A2%E5%8C%96%E7%95%8C%E9%9D%A2)。

`src/main.js`中，将`https://meme.wd-api.com/`修改为自己的服务器地址。

目前Teahouse Studios采用的部署方式是网站内容置于服务器，静态资源置于cdn，如果不需要静态文件分离，请按照以下方法操作：

`vue.config.js`中，`publicPath`修改为`/`。

随后自行上传dist文件到服务器。

如果您需要静态文件分离，请复制`.env.example`到`.env`，并修改其中内容。

## 法律

我们根据 Apache 2.0 协议，在 2020 年 10 月 2 日规定以下附加协议：

Based on Apache 2.0 License, we added the following additional license on October 2, 2020:

使用本仓库搭建的公开网站，除非拥有 Teahouse Studios 的书面授权，均应声明其与 Teahouse Studios 无关，并链接到官方下载链接 <https://dl.meme.teahou.se/>.

Any public website built on this repository should clarify that the website is not affiliated with Teahouse Studios and should provide a link to the official link <https://dl.meme.teahou.se>, except with written permission from Teahouse Studios.

本附加协议具有追溯性，即在 2020 年 10 月 2 日之前本仓库的版本也同样受本附加协议的限制。

This additional license is retrospective, that is versions of this repository before October 2, 2020, are also restricted by this license.

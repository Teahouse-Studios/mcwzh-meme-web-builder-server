import asyncio
import configparser
import json
import os
import time
import pathlib
from concurrent.futures import ThreadPoolExecutor
from os.path import join, dirname

import aiohttp
from memepack_builder import JEPackBuilder, BEPackBuilder, ModuleChecker

from aiohttp import web

app = web.Application()
executor = ThreadPoolExecutor(8)
build_time = 0.0
builder_lock = asyncio.Lock()
env = {"update": 0.0, "data": {}}

config = configparser.ConfigParser()
config.read('config.ini')

PULLING_WHEN_BUILD = True
USE_GITHUB_WEBHOOK = False
GITHUB_SECRET = ''
GITHUB_ACCESS_TOKEN = ''
if 'MEME' in config.sections():
    section = config['MEME']
    PULLING_WHEN_BUILD = section.getboolean('PULLING_WHEN_BUILD', True)
    USE_GITHUB_WEBHOOK = section.getboolean('USE_GITHUB_WEBHOOK', False)
    GITHUB_SECRET = section.get('GITHUB_SECRET', '')
    GITHUB_ACCESS_TOKEN = section.get('GITHUB_ACCESS_TOKEN', '')


def get_env():
    t = time.time()
    timing = []
    timing.append(f'import module: {time.time() - t}')
    t = time.time()
    mods = map(lambda file: f"mods/{file}", os.listdir('meme-pack-java/mods'))
    enmods = map(lambda file: f"en-mods/{file}",
                 os.listdir('meme-pack-java/en-mods'))
    je_checker = ModuleChecker.ModuleChecker(join('meme-pack-java', "modules"))
    je_checker.check_module()
    timing.append(f'je check modules: {time.time() - t}')
    je_modules = je_checker.module_info['modules']
    be_checker = ModuleChecker.ModuleChecker(join('meme-pack-bedrock', "modules"))
    be_checker.check_module()
    timing.append(f'be check modules: {time.time() - t}')
    be_modules = be_checker.module_info['modules']

    jeStat = pathlib.Path(join('meme-pack-java', 'meme_resourcepack', 'assets', 'minecraft', 'lang', 'zh_meme.json'))
    beStat = pathlib.Path(join('meme-pack-bedrock', 'meme_resourcepack', 'texts', 'zh_ME.lang'))

    print(timing)
    return dict(mods=list(mods), enmods=list(enmods),
                je_modules=je_modules, be_modules=be_modules, je_modified=int(jeStat.stat().st_mtime * 1000),
                be_modified=int(beStat.stat().st_mtime * 1000))


async def api(request: web.Request):
    return web.json_response(get_env(), headers={'Access-Control-Allow-Origin': '*'})


async def pull():
    log = []
    await asyncio.create_subprocess_exec("git", "--git-dir=./meme-pack-bedrock/.git", "checkout", "master",
                                         stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                                         stdin=asyncio.subprocess.DEVNULL)
    await asyncio.create_subprocess_exec("git", "--git-dir=./meme-pack-java/.git", "checkout", "master",
                                         stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                                         stdin=asyncio.subprocess.DEVNULL)
    proc = await asyncio.create_subprocess_exec("git", "--git-dir=./meme-pack-java/.git", "pull",
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                                                stdin=asyncio.subprocess.DEVNULL)
    log.append(str((await proc.communicate())[0], encoding="utf-8", errors="ignore"))
    proc = await asyncio.create_subprocess_exec("git", "--git-dir=./meme-pack-bedrock/.git", "pull",
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                                                stdin=asyncio.subprocess.DEVNULL)
    log.append(str((await proc.communicate())[0], encoding="utf-8", errors="ignore"))
    return log


async def ajax(request: web.Request):
    data = await request.json()
    log = []
    async with builder_lock:
        if PULLING_WHEN_BUILD:
            global build_time
            if build_time + 60 < time.time():
                build_time = time.time()
                pull_logs = await pull()
                log.extend(pull_logs)
            else:
                log.append("A cache within 60 seconds is available, skipping update")
        if not data["_be"]:
            submodule_path = 'meme-pack-java'
            module_checker = ModuleChecker.ModuleChecker(join(submodule_path, "modules"))
        else:
            submodule_path = 'meme-pack-bedrock'
            module_checker = ModuleChecker.ModuleChecker(join(submodule_path, "modules"))
        data.setdefault('output', 'builds')
        current_dir = dirname(__file__)
        module_checker.check_module()
        if not data["_be"]:
            builder = JEPackBuilder.JEPackBuilder(
                join(current_dir, submodule_path, "meme_resourcepack"), module_checker.module_info,
                join(current_dir, submodule_path, "mods"),
                join(current_dir, submodule_path, "mappings"))
        else:
            builder = BEPackBuilder.BEPackBuilder(
                join(current_dir, submodule_path, "meme_resourcepack"), module_checker.module_info)
        builder.build_args = data
        await asyncio.get_event_loop().run_in_executor(executor, builder.build)
        log.extend(builder.build_log)
    return web.json_response({"code": 200, "argument": data,
                              "logs": '\n'.join(log),
                              "filename": builder.file_name}, headers={
        'Access-Control-Allow-Origin': '*'
    })


async def ajax_preflight(request: web.Request):
    return web.json_response({}, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'content-type'
    })


async def github(request: web.Request):
    body = await request.text()
    body_data = json.loads(body)
    if GITHUB_SECRET:
        from hashlib import sha256
        import hmac
        should_be = 'sha256=' + hmac.new(GITHUB_SECRET.encode('utf-8'), body.encode('utf-8'),
                                         digestmod=sha256).hexdigest()
        client_sign = request.headers.get('X-Hub-Signature-256', '')
        if not hmac.compare_digest(should_be, client_sign):
            return web.HTTPForbidden(headers={
                'X-Client-Sign': client_sign
            })
    pull_logs = await pull()
    async with aiohttp.ClientSession(headers={
        'authorization': f'token {GITHUB_ACCESS_TOKEN}'
    }) as session:
        async with session.post(body_data['deployment']['statuses_url'], json={"state": "success"}, ) as res:
            print(await res.json())
    return web.json_response(pull_logs)


if not os.path.exists("./builds"):
    os.mkdir("builds")

routes = [
    web.static("/builds/", "./builds"),
    web.route("GET", "/", api),
    web.route("POST", "/ajax", ajax),
    web.route("OPTIONS", "/ajax", ajax_preflight)
]
if USE_GITHUB_WEBHOOK:
    routes.append(web.route("POST", "/github", github))
app.add_routes(routes)

if __name__ == '__main__':
    import sys

    if sys.hexversion < 0x030900F0:
        raise RuntimeError(
            "This program uses features introduced in Python 3.9, please update your Python interpreter.") from None
    '''elif sys.hexversion < 0x030800F0:
        if sys.platform == "win32":  # <- Special version
            asyncio.set_event_loop(
                asyncio.ProactorEventLoop()
            )'''
    web.run_app(app, host="0.0.0.0", port=8000)

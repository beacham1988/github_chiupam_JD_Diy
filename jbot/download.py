#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author   : Chiupam
# @Data     : 2021-06-13
# @Version  : v 1.0
# @Updata   :
# @Future   :


from .. import chat_id, jdbot, _ConfigDir, _ScriptsDir, _OwnDir, logger, _JdbotDir
from ..bot.utils import cmd, press_event, backfile, jdcmd, V4, QL, _ConfigFile, mycron, split_list, row, qlcron, _Auth, upcron
from telethon import events, Button
from asyncio import exceptions
import requests, re, os, asyncio


@jdbot.on(events.NewMessage(from_users=chat_id, pattern=r'^https?://(raw)?.*(js|py|sh)$'))
async def mydownload(event):
    try:
        SENDER = event.sender_id
        btn = [Button.inline('下载此文件', data='confirm'), Button.inline('取消对话', data='cancel')        ]
        async with jdbot.conversation(SENDER, timeout=60) as conv:
            msg = await conv.send_message('检测到你发送了一条链接，请做出你的选择：\n', buttons=btn)
            convdata = await conv.wait_event(press_event(SENDER))
            await jdbot.delete_messages(chat_id, msg)
            res = bytes.decode(convdata.data)
            if res == 'cancel':
                await jdbot.send_message(chat_id, '对话已取消，感谢你的使用')
                conv.cancel()
                return
            furl = event.raw_text
            speeds = ["http://ghproxy.com/", "https://mirror.ghproxy.com/", ""]
            for speed in speeds:
                resp = requests.get(f"{speed}{furl}").text
                if resp:
                    break
            if resp:
                fname = furl.split('/')[-1]
                fname_cn, cron = "", False
                if furl.endswith(".js"):
                    fname_cn, cron = re.findall(r"(?<=new\sEnv\(').*(?=')", resp, re.M), mycron(resp)
                    if fname_cn != []:
                        fname_cn = fname_cn[0]
                if V4:
                    btns = [
                        Button.inline('放入config目录', data=_ConfigDir),
                        Button.inline('放入jbot/diy目录', data=f'{_JdbotDir}/diy'),
                        Button.inline('放入scripts目录', data=_ScriptsDir),
                        Button.inline('放入own目录', data=_OwnDir ),
                        Button.inline('请帮我取消对话', data='cancel')
                    ]
                else:
                    btns = [
                        Button.inline('放入config目录', data=_ConfigDir),
                        Button.inline('放入scripts目录', data=_ScriptsDir),
                        Button.inline('请帮我取消对话', data='cancel')
                    ]
                write, cmdtext = True, False
                msg = await conv.send_message(f'成功下载{fname_cn}脚本\n现在，请做出你的选择：', buttons=split_list(btns, row))
                convdata = await conv.wait_event(press_event(SENDER))
                await jdbot.delete_messages(chat_id, msg)
                res1 = bytes.decode(convdata.data)
                if res1 == 'cancel':
                    await jdbot.send_message(chat_id, '对话已取消，感谢你的使用')
                    conv.cancel()
                    return
                elif res1 == _ScriptsDir:
                    fpath = f"{_ScriptsDir}/{fname}"
                    btns = [Button.inline("是", data="confirm"), Button.inline("否", data="cancel")]
                    msg = await conv.send_message(f"请问需要运行{fname_cn}脚本吗？", buttons=btns)
                    convdata = await conv.wait_event(press_event(SENDER))
                    await jdbot.delete_messages(chat_id, msg)
                    res2 = bytes.decode(convdata.data)
                    if res2 == 'cancel':
                        await jdbot.send_message(chat_id, f'那好吧，文件将保存到{res1}目录')
                    else:
                        cmdtext = f'{jdcmd} {_ScriptsDir}/{fname} now'
                        await jdbot.send_message(chat_id, f"文件将保存到{res1}目录，并随后执行它")
                    msg = await conv.send_message(f"请问需要添加定时吗？", buttons=btns)
                    convdata = await conv.wait_event(press_event(SENDER))
                    res2 = bytes.decode(convdata.data)
                    if res2 == 'cancel':
                        await jdbot.edit_message(msg, f'那好吧')
                    else:
                        await mycronup(jdbot, conv, resp, fname, msg, SENDER, btns, _ScriptsDir)
                elif res1 == _OwnDir:
                    fpath = f"{_OwnDir}/raw/{fname}"
                    btns = [Button.inline("是", data="confirm"), Button.inline("否", data="cancel")]
                    msg = await conv.send_message(f"请问需要运行{fname_cn}脚本吗？", buttons=btns)
                    convdata = await conv.wait_event(press_event(SENDER))
                    res2 = bytes.decode(convdata.data)
                    if res2 == 'cancel':
                        await jdbot.edit_message(msg, f'那好吧，文件将保存到{_OwnDir}/raw目录')
                    else:
                        cmdtext = f'{jdcmd} {_OwnDir}/{fname} now'
                        await jdbot.edit_message(msg, f'文件将保存到{res1}目录，且已写入配置中，准备拉取单个脚本，请耐心等待')
                    with open(_ConfigFile, 'r', encoding="utf-8") as f1:
                        configs = f1.readlines()
                    for config in configs:
                        if config.find("OwnRawFile") != -1 and config.find("## ") == -1:
                            line = configs.index(config) + 1
                            configs.insert(line, f"\t{event.raw_text}\n")
                            with open(_ConfigFile, 'w', encoding="utf-8") as f2:
                                f2.write(''.join(configs))
                        elif config.find("第五区域") != -1:
                            break
                    await cmd("jup own")
                else:
                    fpath = f"{res1}/{fname}"
                    await jdbot.send_message(chat_id, f"文件将保存到{res1}目录")
            conv.cancel()
        backfile(fpath)
        with open(fpath, 'w+', encoding='utf-8') as f:
            f.write(resp)
        if cmdtext:
            await cmd(cmdtext)
    except Exception as e:
        await jdbot.send_message(chat_id, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))


# 修改原作者的 cronup() 函数便于我继续进行此功能的编写
async def mycronup(jdbot, conv, resp, filename, msg, SENDER, markup, path):
    try:
        cron = mycron(resp)
        msg = await jdbot.edit_message(msg, f"这是我识别的定时\n```{cron}```\n请问是否需要修改？", buttons=markup)
    except:
        msg = await jdbot.edit_message(msg, f"我无法识别定时，将使用默认定时\n```0 0 * * *```\n请问是否需要修改？", buttons=markup)
    convdata3 = await conv.wait_event(press_event(SENDER))
    await jdbot.delete_messages(chat_id, msg)
    res3 = bytes.decode(convdata3.data)
    if res3 == 'confirm':
        convmsg = await conv.send_message("请回复你需要设置的 cron 表达式，例如：0 0 * * *")
        cron = await conv.get_response()
        cron = cron.raw_text
        msg = await jdbot.edit_message(convmsg, f"```{cron}```\n好的，你将使用这个定时")
        await asyncio.sleep(1.5)
        await jdbot.delete_messages(chat_id, msg)
    if QL:
        crondata = {"name":f'{filename.split(".")[0]}',"command":f'task {path}/{filename}',"schedule":f'{cron}'}
        with open(_Auth, 'r', encoding='utf-8') as f:
                auth = json.load(f)
        qlcron('add', crondata, auth['token'])
    else:
        upcron(f'{cron} mtask {path}/{filename}')
    await jdbot.send_message(chat_id, '添加定时任务成功')


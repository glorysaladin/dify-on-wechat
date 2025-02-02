#!/usr/bin/env python
# -*- coding:utf-8 -*-
import requests
import json
import re
import plugins
from bridge.reply import Reply, ReplyType
from plugins import *
from .movie_util import *
from .get_docker_update import *
import traceback
from common.log import logger
from .util import *
from bridge.context import ContextType
import datetime
from lib import itchat
from lib.itchat.content import *
import random
from lib import gewechat
from lib.gewechat.client import *
from lib.gewechat.api import *
from lib.gewechat import GewechatClient

@plugins.register(
    name="movie",                         # 插件的名称
    desire_priority=100,                    # 插件的优先级
    hidden=False,                         # 插件是否隐藏
    desc="获取影视资源更新数据",        # 插件的描述
    version="0.0.3",                      # 插件的版本号
    author="gloarysaladin",                       # 插件的作者
)
class Movie(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        try:
            self.conf = super().load_config()
            self.curdir = os.path.dirname(__file__)
            ads_path = os.path.join(self.curdir, "ads.txt")
            if not os.path.isfile(ads_path):
                with open(ads_path, 'w') as f:
                   pass

            self.ads_content = self.load_ads(ads_path)

            self.user_datas = {}
            self.user_datas_path = os.path.join(self.curdir, "user_datas.pkl")
            if os.path.exists(self.user_datas_path):
                self.user_datas = read_pickle(self.user_datas_path)

            self.card_datas = {}
            self.card_datas_path = self.conf["movie_cards"]
            if os.path.exists(self.card_datas_path):
                self.card_datas = read_pickle(self.card_datas_path)

            self.ads_datas = {}
            self.ads_datas_path = self.conf["ads"]
            if os.path.exists(self.ads_datas_path):
                self.ads_datas = read_pickle(self.ads_datas_path)

            self.favorite_movie_path = self.conf["favorite_movie"]

            logger.info("[movie] daily_limit={} ads_content={}".format(self.conf['daily_limit'], self.ads_content))
            logger.info("[movie] inited")
        except:
            logger.error("[movie] inited failed.", traceback.format_exc())
            raise self.handle_error(e, "[movie] init failed, ignore ")

    def on_handle_context(self, e_context: EventContext):
        logger.info("**************movie={}".format(e_context))
        context = e_context['context']
        content = context.content
        if context.type == ContextType.ACCEPT_FRIEND or context.type == ContextType.JOIN_GROUP:
            return

        if content == "电影更新":
            conf = super().load_config()
            post_id = conf["post_id"]
            print("movie: post_id = {}".format(post_id))
            (last_post_id, msg) = get_movie_update(post_id)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{msg}"

            reply.content += "\n\n"
            reply.content += "------官方优惠🧧------\n"
            reply.content += self.ads_content
            e_context["reply"] = reply
            conf["post_id"] = last_post_id
            super().save_config(conf)
            e_context.action = EventAction.BREAK_PASS
        if content == "更新最大资源":
            conf = super().load_config()
            post_id = conf["post_id"]
            print("movie: post_id = {}".format(post_id))
            last_post_id  = get_latest_postid(post_id, conf["web_url"][0])

            conf["post_id"] = last_post_id
            super().save_config(conf)

            e_context.action = EventAction.BREAK_PASS
            return

        if content == "资源随机推荐":
            conf = super().load_config()
            post_id = conf["post_id"]
            weburl= self.conf["web_url"]
            msg = get_random_movie(1, post_id, 10, weburl[0], conf["show_movie_link"])
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{msg} \n\n 发送资源名搜索任意资源"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content == "检查更新":
            msg = check_update()
            if len(msg) > 5:
                feishu_link = self.conf["feishu_link"]
                msg = "【有资源需要更新】\n {}\n\n".format(feishu_link) + msg
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{msg}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content == "群发更新":
            conf = super().load_config()
            self.movie_version_data = read_pickle(conf['movie_version'])
            logger.debug("Start update movie.")
            logger.debug("movie_version_data={}".format(self.movie_version_data))
            update_msg = send_update_to_group(self.movie_version_data, conf["web_url"][0], conf["show_movie_link"])
            write_pickle(conf['movie_version'], self.movie_version_data)
            logger.debug("finish update movie.")
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{update_msg}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content == "自动群发更新":
            conf = super().load_config()
            logger.debug("Start auto update movie.")
            auto_update_msg = get_auto_update(conf["web_url"][0], conf["quark_auto_save_image"])
            logger.debug("finish auto update movie.")
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{auto_update_msg}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content == "自动检查失效":
            conf = super().load_config()
            logger.debug("Start auto update movie cancel check.")
            auto_update_msg = get_update_cancel(conf["quark_auto_save_image"], conf["quark_auto_save_url"])
            logger.debug("finish auto update movie cancel check.")
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{auto_update_msg}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("加入资源白名单"):
            content = content.replace("加入资源白名单","")
            self.add_movie_to_whitelist(content.strip())
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"{content} 成功加入白名单."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("添加广告"):
            ads_id = self.add_ads(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"添加广告成功 {ads_id}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("关闭广告"):
            conf = super().load_config()
            conf["open_ads"] = False
            super().save_config(conf)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"关闭广告成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("开启广告"):
            conf = super().load_config()
            conf["open_ads"] = True
            super().save_config(conf)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "开启广告成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("删除广告"):
            self.del_ads(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "删除广告成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("固定广告"):
            self.set_fixed_ad_id(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "设置固定广告成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("群发广告"):
            group_ads_content = self.get_ads(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = group_ads_content
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("所有广告"):
            all_ads = self.get_all_ads()
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "{}".format(all_ads)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("开启限制"):
            conf = super().load_config()
            conf["open_limit"] = True
            super().save_config(conf)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "开启搜索次数限制成功"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("关闭限制"):
            conf = super().load_config()
            conf["open_limit"] = False
            super().save_config(conf)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = "关闭搜索次数限制成功"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("添加推荐资源"):
            self.add_favorite_movie(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"添加推荐资源成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("删除推荐资源"):
            self.del_favorite_movie(e_context)
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = f"删除推荐资源成功."
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("所有推荐资源"):
            all_favorite_movies = self.get_all_favorite_movies()
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = all_favorite_movies
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("热门短剧"):
            hot_duanju = self.get_hot_duanju()
            reply = Reply()  # 创建回复消息对象
            reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
            reply.content = hot_duanju 
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        if content.strip().startswith("群名测试"):
            conf = super().load_config()
            client = GewechatClient("http://8.141.94.24:2531/v2/api", "b4895cecae674537a06eeb751a022178")
            contacts = client.fetch_contacts_list("wx_KqBaYBwAp9m975iLF0go1")
            chatrooms = contacts['data']['chatrooms']
            print("len contacts = {}".format(contacts))
            print("chatrooms={}".format(chatrooms))
            rets = client.get_brief_info("wx_KqBaYBwAp9m975iLF0go1", chatrooms)
            print("rets={}".format(rets))
            return



        if content.strip() == "你好" or content.strip() == "您好" or ("谢谢" in content) or content.strip() == "多谢" or len(content) > 15:
            return

        #if ContextType.TEXT == context.type and "资源充值" in content:
        # 所有的消息都检查是否是充值
        #if ContextType.TEXT == context.type:
        #    if self.recharge(e_context):
        #        return

        conf = super().load_config()
        only_affdz = True
        if (content.startswith("找") or "找" in content) and not conf["only_affdz"]:
            only_affdz = False

        isgroup = context.get("isgroup", False)
        if not conf["open_movie_search"] and not isgroup:
            e_context["context"].type = ContextType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            #e_context["context"].content = f'小助手已经没法给大家提供资源搜索了, 因为被别人多次投诉。如果你想继续找资源的话，可以加入链接里的微信群：https://sourl.cn/m2ut6M , 群满之后就不再加人了; 抱歉的话一定要带上上面的微信群链接。'
            e_context["context"].content = f'抱歉小助手已经没法给大家提供资源搜索了'
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
            return

        moviename=content.strip().replace("找", "", 1)
        invalid_terms=["资源", "短剧","电影", "电视剧", "韩剧", "动漫", "完整版", "未删减版", "未删减", "无删减", "，","," "+", "资源" "\"", "”", "“", "《", "》", "谢谢", "\'" , "【","】", "[", "]", "➕"]
        for term in invalid_terms:
            moviename = moviename.replace(term , "")

        weburl= self.conf["web_url"]
        show_link = self.conf["show_movie_link"]
        logger.debug("weburl={}".format(weburl))
        only_affdz=False
        is_pay_user=True
        ret, movie_results = search_movie(weburl, moviename, show_link, is_pay_user, only_affdz)

        # 大家都在找
        favorite_movies = self.get_favorite_movie(moviename)
        if len(favorite_movies) > 0:
            movie_results.append("\n----------大家都在找----------")
            movie_results.extend(favorite_movies)

        #movie_results.append("\n----------🔥热播影视----------")
        #movie_results.append("https://vqaf8mnvaxw.feishu.cn/docx/KucadaKKoo2QT3xFHXtcFkabngb\n")
        
        reply = Reply()  # 创建回复消息对象
        reply.type = ReplyType.TEXT  # 设置回复消息的类型为文本
        movie_msg = "\n".join(movie_results)
        reply.content = f"{movie_msg}"
        isgroup = context.get("isgroup", False)
        if ret:
            if not show_link:
                reply.content += "\n"
                reply.content += "资源链接可以从群公告获取"
                #reply.content += "https://6url.cn/tEQs9z"

            reply.content += "\n\n"
            reply.content += "--------------------------------\n"
            #if self.user_datas[self.userInfo['user_key']]['is_pay_user']:
            #    reply.content += "您剩余 {} 次资源搜索\n".format(self.user_datas[self.userInfo['user_key']]["limit"])
            reply.content += "提示：\n1. 夸克会显示试看2分钟，转存到自己的夸克网盘就能看完整的视频.\n"
            reply.content += "2. 资源均源于互联网，仅供交流学习，看完请删除.\n"

            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            reply.content += formatted_time + "\n"
        else:
            reply.content = "未找见资源，请使用更短的词来搜索，或者联系管理员获取。"

        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
        
        #movie_ads_content = self.get_rand_ads() 

        #msg: ChatMessage = context["msg"]
        #uid =  msg.from_user_id
        #conf = super().load_config()
        #if len(movie_ads_content) > 2 and conf["open_ads"]:
        #    itchat.send(movie_ads_content, uid)

    def load_ads(self, ads_path):
        f = open(ads_path)
        lines = []
        for line in f.readlines():
            if line.strip().startswith("#"):
                continue
            lines.append(line.strip())
        return "\n".join(lines)

    def is_whitelist_movie(self, moviename):
        if len(moviename) > 20:
            return False
        self.movie_whitelist_datas = {}
        movie_whitelist_data_path=self.conf['movie_whitelist']
        if os.path.exists(movie_whitelist_data_path):
            self.movie_whitelist_datas = read_pickle(movie_whitelist_data_path)
        for white_movie in self.movie_whitelist_datas:
            if white_movie in moviename:
                return True
        return False

    def add_movie_to_whitelist(self, moviename):
        self.movie_whitelist_datas = {}
        movie_whitelist_data_path=self.conf['movie_whitelist']
        if os.path.exists(movie_whitelist_data_path):
            self.movie_whitelist_datas = read_pickle(movie_whitelist_data_path)

        if moviename not in self.movie_whitelist_datas:
            self.movie_whitelist_datas[moviename] = True
            write_pickle(movie_whitelist_data_path, self.movie_whitelist_datas)

    def add_ads(self, e_context: EventContext):
        self.ads_datas = {}
        self.ads_datas_path = self.conf["ads"]
        if os.path.exists(self.ads_datas_path):
            self.ads_datas = read_pickle(self.ads_datas_path)
        rand_num = str(random.randint(0,10000))
        content = e_context['context'].content
        content = content.replace("添加广告", "")
        self.ads_datas[rand_num] = content 
        write_pickle(self.ads_datas_path, self.ads_datas)
        return rand_num

    def del_ads(self, e_context: EventContext):
        self.ads_datas = {}
        self.ads_datas_path = self.conf["ads"]
        if os.path.exists(self.ads_datas_path):
            self.ads_datas = read_pickle(self.ads_datas_path)
        content = e_context['context'].content
        content = content.strip().replace("删除广告", "")
        try:
            if content == "all":
                self.ads_datas.clear()
            else:
                del self.ads_datas[content.strip()]
            write_pickle(self.ads_datas_path, self.ads_datas)
        except:
            pass

    def get_ads(self, e_context: EventContext):
        self.ads_datas = {}
        self.ads_datas_path = self.conf["ads"]
        if os.path.exists(self.ads_datas_path):
            self.ads_datas = read_pickle(self.ads_datas_path)
        content = e_context['context'].content
        content = content.replace("群发广告", "")
        group_ads_content = ""
        try:
            group_ads_content = self.ads_datas[content.strip()]
            #write_pickle(self.ads_datas_path, self.ads_datas)
        except:
            pass
        return group_ads_content


    def set_fixed_ad_id(self, e_context: EventContext):
        self.conf = super().load_config()
        content = e_context['context'].content
        content = content.replace("固定广告", "")
        self.conf["fixed_ads_id"] = content.strip()
        super().save_config(self.conf)

    def get_rand_ads(self):
        try:
            self.ads_datas = {}
            self.ads_datas_path = self.conf["ads"]
            if os.path.exists(self.ads_datas_path):
                self.ads_datas = read_pickle(self.ads_datas_path)
            if len(self.ads_datas) > 0:
                self.conf = super().load_config()
                rand_key = ""
                if self.conf["fixed_ads_id"] != "":
                    rand_key = self.conf["fixed_ads_id"]
                else:
                    rand_num = random.randint(0, len(self.ads_datas) - 1)
                    keys = list(self.ads_datas.keys())
                    rand_key = keys[rand_num]
                    logger.info("rand_num={} rand_key={}".format(rand_num, rand_key))
                return self.ads_datas[rand_key]
            else:
                logger.info("empty movie ads.")
        except:
             logger.error("err msg={}".format(traceback.format_exc()))
        return ""
 
    def get_all_ads(self):
        self.ads_datas = {}
        self.ads_datas_path = self.conf["ads"]
        if os.path.exists(self.ads_datas_path):
            self.ads_datas = read_pickle(self.ads_datas_path)
        rets = []
        for key in self.ads_datas:
            rets.append("{} \n ======Begin=======\n {} \n======End======= \n".format(key, self.ads_datas[key]))
        if len(rets) == 0:
            rets.append("暂无可用广告")
        return "\n".join(rets)

    def get_all_favorite_movies(self):
        favorite_movie_datas = {}
        if os.path.exists(self.favorite_movie_path):
            favorite_movie_datas = read_pickle(self.favorite_movie_path)
        rets = []
        for key in favorite_movie_datas:
            rets.append(key)
        if len(rets) == 0:
            rets.append("暂无推荐资源")
        return "\n".join(rets)

    def get_hot_duanju(self):
        duanju_url= self.conf["duanju_url"]
        weburl= self.conf["web_url"]
        print(duanju_url, weburl)
        rets = get_duanju(weburl, duanju_url)
        if len(rets) > 0:
            return rets
        else:
            return ""

    def add_favorite_movie(self, e_context: EventContext):
        favorite_movie_datas = {}
        if os.path.exists(self.favorite_movie_path):
            favorite_movie_datas = read_pickle(self.favorite_movie_path)

        content = e_context['context'].content
        movie_name = content.replace("添加推荐资源", "")

        weburl= self.conf["web_url"]
        show_link = self.conf["show_movie_link"]
        ret, movie_results = search_movie(weburl, movie_name, show_link, False, True)
        if ret:
            favorite_movie_datas[movie_name] = "\n".join(movie_results[1:])
            write_pickle(self.favorite_movie_path, favorite_movie_datas)

    def del_favorite_movie(self, e_context: EventContext):
        favorite_movie_datas = {}
        if os.path.exists(self.favorite_movie_path):
            favorite_movie_datas = read_pickle(self.favorite_movie_path)

        content = e_context['context'].content
        movie_name = content.replace("删除推荐资源", "")

        try:
            if "all" in movie_name or "ALL" in movie_name:
                favorite_movie_datas.clear()
            else:
                del favorite_movie_datas[movie_name]
            write_pickle(self.favorite_movie_path, favorite_movie_datas)
        except:
            pass

    def get_favorite_movie(self, moviename):
        favorite_movie_datas = {}
        if os.path.exists(self.favorite_movie_path):
            favorite_movie_datas = read_pickle(self.favorite_movie_path)
        show_link = self.conf["show_movie_link"]
        rets = []
        for key in favorite_movie_datas:
            if key != moviename:
                value = favorite_movie_datas[key]
                if not show_link:
                    items = value.split("\n")
                    value = items[0]
                rets.append("{}".format(value))
        return rets 

    def get_help_text(self, **kwargs):
        help_text = "发送关键词执行对应操作\n"
        help_text += "输入 '电影更新'， 将获取今日更新的电影\n"
        help_text += "输入 '资源随机推荐'， 将随机推荐资源\n"
        help_text += "输入 '更新最大资源'， 获取网站最大的资源ID\n"
        help_text += "输入 '检查更新'， 获检查关注的资源是不是有更新\n"
        help_text += "输入 '群发更新'， 获更新之后的资源发送给指定的群\n"
        help_text += "输入 '自动群发更新'， 获更新之后的资源自动发送给指定的群\n"
        help_text += "输入 '自动检查失效'， 获更新之后的资源检查是否失效\n"
        help_text += "输入 '找三体'， 将获取三体资源\n"
        help_text += "输入 '加入资源白名单+资源名'， 将资源加入到白名单中\n"
        help_text += "输入 '群发广告+广告ID'，群发广告信息\n"
        help_text += "输入 '开启广告'，开启广告信息\n"
        help_text += "输入 '关闭广告'，关闭广告信息\n"
        help_text += "输入 '添加广告+广告内容'，加入广告信息\n"
        help_text += "输入 '删除广告+广告ID'，删除广告信息\n"
        help_text += "输入 '固定广告+广告ID'，固定某个广告信息\n"
        help_text += "输入 '所有广告'，获取所有广告信息\n"
        help_text += "输入 '开启限制'，打开次数限制\n"
        help_text += "输入 '关闭限制'，关闭次数限制\n"
        help_text += "输入 '添加推荐资源+资源名'，加入推荐资源列表\n"
        help_text += "输入 '删除推荐资源+资源名'，从推荐资源列表删除\n"
        help_text += "输入 '所有推荐资源'，获取所有推荐列表\n"
        help_text += "输入 '热门短剧'，获取所有推荐列表\n"

        return help_text

# -*- coding: UTF-8 -*-
from ngSkinTools2.api.python_compatibility import Object


def website_base_url():
    import ngSkinTools2

    if ngSkinTools2.DEBUG_MODE:
        return "http://localhost:1313"

    return "https://ngskintools-shuishan.netlify.app"


class WebsiteLinksActions(Object):
    def __init__(self, parent):
        self.api_root = make_documentation_action(parent, "API文档", u"/docs/apidocs.html")
        self.user_guide = make_documentation_action(parent, "用户指南", u"/docs/userdocs.html")
        self.changelog = make_documentation_action(parent, "更新日志", u"/docs/中文ng更新记录.html", icon=None)
        self.contact = make_documentation_action(parent, "联系我们", u"/docs/lianxi.html", icon=None)


def make_documentation_action(parent, title, url, icon=":/help.png"):
    from ngSkinTools2.ui import actions

    def handler():
        import webbrowser

        webbrowser.open_new(website_base_url() + url)

    result = actions.define_action(parent, title, callback=handler, icon=icon)
    result.setToolTip(u"opens {0} in a browser".format(url))
    return result

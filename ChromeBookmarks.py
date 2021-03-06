import json
import logging
import os

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

logging.basicConfig()
logger = logging.getLogger(__name__)


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = extension.get_items(event.get_argument())
        return RenderResultListAction(items)


class ChromeBookmarks(Extension):
    matches_len = 0

    def __init__(self):
        self.bookmarks_path = self.find_bookmarks_path()
        super(ChromeBookmarks, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

    @staticmethod
    def find_bookmarks_path():
        f = os.popen('locate google-chrome | grep Bookmarks')
        res = f.read()
        res = res.split('\n')
        if len(res) == 0:
            logger.exception('Path to the Chrome Bookmarks was not found')
        if len(res) > 1:
            for i in range(0, len(res)):
                if res[i][-9:] == 'Bookmarks':
                    return res[i]

        logger.exception('Path to the Chrome Bookmarks was not found')

    def find_rec(self, data, query, matches):

        if self.matches_len >= 10:
            return

        if data['type'] == 'folder':
            for i in range(0, len(data['children'])):
                self.find_rec(data['children'][i], query, matches)
        else:
            res = data['name'].lower().find(query, 0, len(data['name']))
            if res != -1:
                matches.append(data)
                self.matches_len += 1

        return matches

    def get_items(self, query):

        items = []
        matches = []
        self.matches_len = 0

        if query is None:
            query = ''

        with open(self.bookmarks_path) as data_file:

            data = json.load(data_file)
            matches = self.find_rec(data['roots']['bookmark_bar'], query, matches)
            max_len = self.matches_len

            if self.matches_len < 10:
                max_len = self.matches_len
            for i in range(0, max_len):
                bookmark_name = matches[i]['name'].encode('utf-8')
                bookmark_url = matches[i]['url'].encode('utf-8')
                items.append(ExtensionResultItem(icon='images/chrome.png',
                                                 name='%s' % bookmark_name,
                                                 description='%s' % bookmark_url,
                                                 on_enter=OpenUrlAction(bookmark_url)))

        return items

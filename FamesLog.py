#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys
import json
import getpass
import codecs
from PTTLibrary import PTT

def PostHandler(Post):
    date = Post.getDate()[4:10]
    filename = date.replace(' ','_') + '.log'
    fame = 'zesonpso'
    filepath = './' + fame + '_log/'
    with codecs.open( filepath + filename, 'w', 'utf-8') as ResultFile:
        ResultFile.write( '\n' + Post.getDate() + '\n\n')
        for Push in Post.getPushList():
            if Push.getAuthor() == fame:        
                ResultFile.write( Push.getContent() + '\n' )


if __name__ == '__main__':

    try:
        with open('Account.txt') as AccountFile:
            Account = json.load(AccountFile)
            ID = Account['ID']
            Password = Account['Password']
    except FileNotFoundError:
        ID = input('請輸入帳號: ')
        Password = getpass.getpass('請輸入密碼: ')


    PTTBot = PTT.Library(kickOtherLogin=False)

    ErrCode = PTTBot.login(ID, Password)

    if ErrCode != PTT.ErrorCode.Success:
        PTTBot.Log('登入失敗')
        sys.exit()

    CrawPost = 1

    EnableSearchCondition = True
    inputSearchType = PTT.PostSearchType.Keyword
    inputSearch = '盤中閒聊'

    if EnableSearchCondition:
        ErrCode, NewestIndex = PTTBot.getNewestIndex(Board='Stock', SearchType=inputSearchType, Search=inputSearch)
    else:
        ErrCode, NewestIndex = PTTBot.getNewestIndex(Board='Stock')

    if ErrCode == PTT.ErrorCode.Success:
        PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號成功: ' + str(NewestIndex))
    else:
        PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號失敗')
        sys.exit()


    if EnableSearchCondition:
        ErrCode, SuccessCount, DeleteCount = PTTBot.crawlBoard('Stock', PostHandler, StartIndex=NewestIndex - CrawPost + 1, EndIndex=NewestIndex, SearchType=inputSearchType, Search=inputSearch)
    else:
        ErrCode, SuccessCount, DeleteCount = PTTBot.crawlBoard('Stock', PostHandler, StartIndex=NewestIndex - CrawPost + 1, EndIndex=NewestIndex)

    if ErrCode == PTT.ErrorCode.Success:
        PTTBot.Log('爬行成功共 ' + str(SuccessCount) + ' 篇文章 共有 ' + str(DeleteCount) + ' 篇文章被刪除')

    # 登出
    PTTBot.logout()
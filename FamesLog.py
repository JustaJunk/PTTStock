#!/usr/bin/python
#-*- coding: UTF-8 -*-

import os, sys, time
import json
import getpass
import codecs
from PTTLibrary import PTT

class PTTfames:
	def __init__(self):
		try:
			with open('Account.txt') as AccountFile:
				Account = json.load(AccountFile)
				ID = Account['ID']
				Password = Account['Password']
		except FileNotFoundError:
			ID = input('請輸入帳號: ')
			Password = getpass.getpass('請輸入密碼: ')

		self.PTTBot = PTT.Library(kickOtherLogin=False)

		ErrCode = self.PTTBot.login(ID, Password)

		if ErrCode != PTT.ErrorCode.Success:
			self.PTTBot.Log('登入失敗')
			sys.exit()

		self.famelist = []

	def addFame(self,pttID):
		self.famelist.append(pttID)

	def addFameFile(self,filename):
		if not os.path.exists(filename):
			print(filename, 'does not exist')
		else:
			with codecs.open(filename,'r','utf-8') as FamesFile:
				for pttID in FamesFile:
					if pttID:
						self.famelist.append(pttID)


	def writeLog(self,Post,fame):
		date = Post.getDate()[4:10]
		filename = date.replace(' ','_') + '.log'
		filepath = './' + fame + '_log/'
		if not os.path.exists(filepath):
			os.makedirs(filepath)
		with codecs.open( filepath + filename, 'w', 'utf-8') as LogFile:
			LogFile.write( '\n' + Post.getDate() + '\n\n')
			for Push in Post.getPushList():
				if Push.getAuthor() == fame:        
					LogFile.write( Push.getContent() + '\n' )

	def PostHandler(self,Post):
		for fame in self.famelist:
			self.writeLog(Post,fame)

	def getChat(self,CrawPost):
		inputSearchType = PTT.PostSearchType.Keyword
		inputSearch = '盤中閒聊'
		ErrCode, NewestIndex = self.PTTBot.getNewestIndex(Board='Stock', SearchType=inputSearchType, Search=inputSearch)
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號成功: ' + str(NewestIndex))
		else:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號失敗')
			sys.exit()

		ErrCode, SuccessCount, DeleteCount = self.PTTBot.crawlBoard('Stock', self.PostHandler, StartIndex=NewestIndex - CrawPost + 1, EndIndex=NewestIndex, SearchType=inputSearchType, Search=inputSearch)
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('爬行成功共 ' + str(SuccessCount) + ' 篇文章 共有 ' + str(DeleteCount) + ' 篇文章被刪除')



if __name__ == '__main__':
	pttFames = PTTfames()
	pttFames.addFameFile('famesID.txt')

	if len(sys.argv) < 2:
		while True:
			try:
				pttFames.getChat(1)
				time.sleep(300)
			except KeyboardInterrupt:
				break
	else:
		pttFames.getChat(int(sys.argv[1]))



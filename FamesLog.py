#!/usr/bin/python
#-*- coding: UTF-8 -*-

import os, sys, time
import json
import getpass
import codecs
from PTTLibrary import PTT # version=0.7.28

class PTTfames:
	def __init__(self,outputPath):
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

		self.timing = 'intrade'
		self.famelist = []
		self.outputPath = outputPath

	def addFame(self,pttID):
		self.famelist.append(pttID)

	def addFameFile(self,filename):
		if not os.path.exists(filename):
			print(filename, 'does not exist')
		else:
			with codecs.open(filename,'r','utf-8') as FamesFile:
				famelist = FamesFile.readlines()
				for pttID in famelist:
					pttID = pttID.replace('\n','').replace('\r','')
					if pttID:
						self.famelist.append(pttID)

	def isNotEmpty(self):
		return len(self.famelist)>0


	def PostHandler(self,Post):
		date = Post.getDate()[4:10]
		filename = date.replace(' ','_') + '_' + self.timing + '.log'
		if not os.path.exists(self.outputPath):
			os.makedirs(self.outputPath)
		with codecs.open( self.outputPath + filename, 'w', 'utf-8') as LogFile:
			LogFile.write( '\n' + Post.getDate() + '\n\n')
			for Push in Post.getPushList():
				push_author = Push.getAuthor()
				if Push.getAuthor() in self.famelist:
					if len(push_author) > 8:
						push_author = push_author[0:8]
						pre_space = ' '
					else:
						pre_space = ' '*(8-len(push_author)+1)
					LogFile.write( push_author + pre_space + Push.getContent() + '\n' )

	def getChat(self,CrawPost,timing):
		inputSearchType = PTT.PostSearchType.Keyword
		self.timing = timing
		if timing == 'intrade':
			inputSearch = '盤中閒聊'
		elif timing == 'offtrade':
			inputSearch = '盤後閒聊'
		else:
			inputSearch = ''
		ErrCode, NewestIndex = self.PTTBot.getNewestIndex(Board='Stock', SearchType=inputSearchType, Search=inputSearch)
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號成功: ' + str(NewestIndex))
		else:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號失敗')
			sys.exit()

		ErrCode, SuccessCount, DeleteCount = self.PTTBot.crawlBoard('Stock', self.PostHandler, StartIndex=NewestIndex - CrawPost + 1, EndIndex=NewestIndex, SearchType=inputSearchType, Search=inputSearch)
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('爬行成功共 ' + str(SuccessCount) + ' 篇文章 共有 ' + str(DeleteCount) + ' 篇文章被刪除')

	def run(self,CrawPost,timing):
		if CrawPost == 0:
			for i in range(100):
				try:
					self.getChat(1,timing)
					print('更新第'+str(i+1)+'次，Ctrl-C 可中斷更新...')
					time.sleep(300)
				except KeyboardInterrupt:
					break
		else:
			self.getChat(CrawPost,timing)


if __name__ == '__main__':
	pttFames_exist = False
	output_path = 'output_log/'
	while True:
		choice = input('\n 1.盤中聊天\n 2.盤後聊天\n 3.清除紀錄\n 4.離開程式\n\n 執行選項: ')

		if choice == '1' or choice == '2':
			try:
				crawNum = int(input(' 爬文數: '))
			except ValueError:
				print(' 請輸數字！')
				continue

			if not pttFames_exist:
				pttFames = PTTfames(output_path)
				pttFames_exist = True
			pttFames.addFameFile('trackID.txt')
			if choice == '1' and pttFames.isNotEmpty():
				pttFames.run(crawNum,'intrade')
			elif choice == '2' and pttFames.isNotEmpty():
				pttFames.run(crawNum,'offtrade')
			else:
				print('No fames to track')

		elif choice == '3':
			if os.path.exists(output_path):
				for file in os.listdir(output_path):
					os.remove(output_path + file)
			else:
				print('\n 尚未建立輸出路徑')

		else:
			break
			







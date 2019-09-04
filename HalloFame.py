#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys
import json
import getpass
import codecs
from PTTLibrary import PTT
from Stockist import Stockist

class PTTBoard:
	def __init__(self):
		self.dict = {}

	def add(self, pttID, pttDate, sid, Long_or_Short):
		if pttID not in self.dict:
			self.dict[pttID] = Stockist(pttID)

		self.dict[pttID].promot(pttDate, sid, Long_or_Short)

	def saveAll(self,log):
		wins, proms = self.winrateAll()
		log.write('\nWhole PTTStock Winrate\n')
		log.write('wins: ' + str(wins) + '  proms: ' + str(proms) + '\n\n')
		for fame in self.dict:
			self.dict[fame].saveRecord(log)


	def winrateAll(self):
		prom = win = 0
		for fame in self.dict:
			i, j = self.dict[fame].winrate()
			win  += i
			prom += j
		return win, prom



class PTTStockBot:
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

		self.Board 	= PTTBoard()
		self.CrawPost   = 0
		self.RepoNum 	= 0
		self.PromNum 	= 0
		self.OtherNum	= 0


	def save(self):
		with codecs.open( 'HalloFameRecord.log', 'w', 'utf-8') as log:
			log.write('總共：'+str(self.CrawPost)+'  有效：'+str(self.PromNum)+'  無效：'+str(self.OtherNum)+'　　RePo：'+str(self.RepoNum)+'\n')
			self.Board.saveAll(log)


	def PostHandler(self,Post):
		if 'Re:' not in Post.getTitle():
			content = Post.getContent().split('1. 標的：')[1].split('2. 分類：')
			content1 = content[0]
			content2 = content[1].split('3. 分析/正文')[0]
			sid   = self.getSid(content1)
			trend = self.getTrend(content2)
			print('\n')
			print(Post.getTitle())
			if sid and trend:
				print(sid,trend,'\n')
				self.Board.add(Post.getAuthor(), Post.getDate(), sid, trend)
				self.PromNum += 1
			else:
				self.OtherNum += 1
		else:
			self.RepoNum += 1


	def getSid(self, plaintext):
		digits = ''
		for char in plaintext:
			if char.isdigit():
				digits += char
		if len(digits) == 4:
			return digits
		else:
			return False

	def getTrend(self, plaintext):
		long_count 	= plaintext.count('多')
		short_count = plaintext.count('空')
		if long_count == short_count:
			return False
		elif long_count > short_count:
			return 'Long'
		else:
			return 'Short'


	def getPromotions(self,CrawPost):
		self.CrawPost = CrawPost
		ErrCode, NewestIndex = self.PTTBot.getNewestIndex(Board='Stock', SearchType=PTT.PostSearchType.Keyword, Search='[標的]')
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號成功: ' + str(NewestIndex))
		else:
			self.PTTBot.Log('取得 ' + 'Stock' + ' 板最新文章編號失敗')
			sys.exit()

		ErrCode, SuccessCount, DeleteCount = self.PTTBot.crawlBoard('Stock', self.PostHandler, StartIndex=NewestIndex - CrawPost + 1, EndIndex=NewestIndex, SearchType=PTT.PostSearchType.Keyword, Search='[標的]')
		if ErrCode == PTT.ErrorCode.Success:
			self.PTTBot.Log('爬行成功共 ' + str(SuccessCount) + ' 篇文章 共有 ' + str(DeleteCount) + ' 篇文章被刪除')





if __name__ == '__main__':

	postCounts = input('\n你要爬幾篇標的文: ')
	postCounts = int(postCounts)
	HallofFame = PTTStockBot()
	HallofFame.getPromotions(postCounts)
	HallofFame.save()

	#board = PTTBoard()
	#board.add('zesonpso', 'xxx Mar 19 09:25 2019', '1722', 'Long')
	#board.add('doliny', 'Mon Jul 22 07:20 2019', '2330', 'Long')
	#board.add('dersonhome', 'Thu Jul 25 16:25 2019', '5269', 'Short')
	#board.add('zesonpso', 'Thu May 16 11:30 2019', '2356', 'Long')
	#board.saveAll()






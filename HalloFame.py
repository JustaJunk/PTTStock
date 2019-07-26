#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys
import json
import getpass
import codecs
from PTTLibrary import PTT

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

month2num = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

req = requests.session()
retries = Retry(total=10,backoff_factor=1,status_forcelist=[ 500, 502, 503, 504 ])
req.mount('http://', HTTPAdapter(max_retries=retries))


class StockPoint:
	def __init__(self, pttDate, sid, Long_or_Short):
		self.sid = sid
		self.day = pttDate[0:3]
		month = month2num[pttDate[4:7]]
		date  = pttDate[8:10]
		year  = pttDate[-4:]
		self.inDate = year + '/' + month + '/' + date
		self.trend = Long_or_Short

	def setup(self):
		if self.day == 'Sat' or self.day == 'Sun':
			return False
		else:
			res = req.get('http://djinfo.cathaysec.com.tw/Z/ZC/ZCW/CZKC1.djbcd?a='+self.sid+'&b=D&c=300')
			if res:
				resp = res.text.split()
				dateline = resp[0].split(',')
				try:
					when = dateline.index(self.inDate)
				except IndexError:
					return False
				priceline = resp[4].split(',')
				afterDate = dateline[when:]
				if len(afterDate) < 3:
					return False
				afterPri  = [ float(pri) for pri in priceline[when:] ]
				self.inPrice = afterPri[0]
				self.nowDate = dateline[-1]
				self.nowPrice = afterPri[-1]
				self.highestPrice = max(afterPri)
				self.highestDate  = afterDate[afterPri.index(self.highestPrice)]
				self.lowestPrice = min(afterPri)
				self.lowsetDate  = afterDate[afterPri.index(self.lowestPrice)]
				return True
			else:
				return False

	def ifwin(self):
		ifLongWin  = ( self.trend == 'Long'  and self.highestPrice > self.inPrice*1.02 )
		ifShortWin = ( self.trend == 'Short' and self.lowestPrice  < self.inPrice*0.98 )
		return ( ifLongWin or ifShortWin )


	def save(self,logfile):
		logfile.write('----------------\n')
		logfile.write( self.sid + '  ' + self.trend + '\n')
		logfile.write( '進場: ' + self.inDate + '  ' + str(self.inPrice) + '\n')
		logfile.write( '最高: ' + self.highestDate + '  ' + str(self.highestPrice) + '\n')
		logfile.write( '最低: ' + self.lowsetDate + '  ' + str(self.lowestPrice) + '\n')
		logfile.write( '現在: ' + self.nowDate + '  ' + str(self.nowPrice) + '\n')

		if self.ifwin():
			logfile.write( 'Nice!\n')
		else:
			logfile.write( 'Booo!\n')
		logfile.write('----------------\n')


class Stockist:
	def __init__(self, pttID):
		self.pttID = pttID
		self.promotions = []

	def promot(self, pttDate, sid, Long_or_Short):
		stk = StockPoint(pttDate, sid, Long_or_Short)
		if stk.setup():
			self.promotions.append(stk)

	def winrate(self):
		winNum = 0
		if self.promotions:
			for stk in self.promotions:
				if stk.ifwin():
					winNum += 1
		return winNum, len(self.promotions)

	def saveRecord(self,logfile):
		if self.promotions:
			wins, proms = self.winrate()
			logfile.write('\n#########################\n')
			logfile.write(self.pttID + '\n')
			logfile.write('wins: ' + str(wins) + '  proms: ' + str(proms) + '\n')
			for stk in self.promotions:
				logfile.write('\n')
				stk.save(logfile)
			logfile.write('\n')



class PTTBoard:
	def __init__(self):
		self.dict = {}

	def add(self, pttID, pttDate, sid, Long_or_Short):
		if pttID not in self.dict:
			self.dict[pttID] = Stockist(pttID)

		self.dict[pttID].promot(pttDate, sid, Long_or_Short)

	def saveAll(self):
		wins, proms = self.winrateAll()
		with codecs.open( 'HalloFameRecord.log', 'w', 'utf-8') as log:
			log.write('Whole PTTStock Winrate\n')
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

		self.Board = PTTBoard()


	def save(self):
		self.Board.saveAll()


	def PostHandler(self,Post):
		result = self.breakdownTitle(Post.getTitle())
		if result:
			self.Board.add(Post.getAuthor(), Post.getDate(), result[0], result[1])


	def breakdownTitle(self,title):
		digits = ''
		words  = ''
		chars  = title
		for char in chars:
			if char.isdigit():
				digits += char
			else:
				words  += char

		if len(digits) != 4:
			return []
		elif 'Re:' in words:
			return []
		else:
			if '多' in words:
				return [digits, 'Long']
			if '空' in words:
				return [digits, 'Short']
			else:
				return [] 


	def getPromotions(self,CrawPost):
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
	#board.add('zesonpso', 'xxx Mar 19 2019', '1722', 'Long')
	#board.add('doliny', 'Mon Jul 22 2019', '2330', 'Long')
	#board.add('dersonhome', 'Thu Jul 25 2019', '5269', 'Short')
	#board.add('zesonpso', 'Thu May 16 2019', '2356', 'Long')
	#board.saveAll()






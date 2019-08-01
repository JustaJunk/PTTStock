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
				if len(afterDate) < 1:
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






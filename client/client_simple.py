from tkinter import * # tkinter에서 모든 정의를 임포트한다.
import time
import pygame
import random
import time

import socket
import ast
import json
import threading

class GameClient:
	def __init__(self,user,host,port):
		#네트워크 초기화 및 서버 연결
		#		
		self.port = port		# 연결 포트설정
		self.host = host		#서버 IP		
		self.user = user		#사용자 아이디 설정

		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect((self.host, self.port))

		#서버 연결 확인을 위한 패킷 송수신
		self.client_socket.sendall(self.user.encode())#서버에 사용자 아이디 전송
		
		
		#서버에서 전송된 사용자 데이터를 저장하는 변수
		self.user_data={}
		
		#
		self.receive_thread = threading.Thread(target=self.handle_receive)
		self.receive_thread.daemon = True
		self.receive_thread.start()


		#게임윈도우 만들기 시작...
		print("게임윈도우를 생성합니다.")

		window = Tk() # 윈도우 생성
		window.title("네트워크게임예제") # 제목을 설정
		window.geometry("1440x960") # 윈도우 크기 설정
		window.resizable(0,0) # 윈도우 크기 조절 X
		
		self.lightingTimer = time.time() # 일정 주기로 lighting effect 효과를 위한 타임 변수

		
		self.keys=set() # 중복된 사용자 입력 키 값을 쉽게 제거하기 위해 set 타입으로 선언
		self.canvas = Canvas(window, bg = "white")
		self.canvas.pack(expand=True,fill=BOTH)

		window.bind("<KeyPress>",self.keyPressHandler)
		window.bind("<KeyRelease>",self.keyReleaseHandler)
		
		
		self.img_dragon = [PhotoImage(file='image/dragon-animated-gif.gif',format = 'gif -index %i' %(i)).subsample(3) for i in range(40)]
		self.img_light_effect = PhotoImage(file="image/lightning-effect-png2.png")		
		self.img_bg = PhotoImage(file="image/bgimage2.png")		
		

		#배경 그리기.
		self.canvas.create_image(0,0, image = self.img_bg,anchor = NW,tags="bg")

								
        #배경사운드
		pygame.init()
		pygame.mixer.music.load("sound/bgm.wav") #Loading File Into Mixer
		pygame.mixer.music.play(-1) #Playing It In The Whole Device
				

		self.canvas.create_text(150,60,fill="white",font="Times 15 italic bold",text="입력키: ↑ , ↓ , ← , → , space")
		self.canvas.create_text(720,810,fill="white",font="Times 20 italic bold",text="Network Game Example")
		self.canvas.create_text(720,850,fill="white",font="Times 20 italic bold",text="Major of computer software, Gyeongsang National Universityty")

		#
		while True:

			#사용자 입력이 있을 경우 서버로 데이터 전송
			if(len(self.keys)>0):#각 키값을 ',' 구분된 아스키 코드 값으로 전송
				self.client_socket.sendall(','.join(str(e) for e in self.keys).encode())

			fire_obj_idx = 0			

			for key, value in self.user_data.items():				
				try:
					obj = self.canvas.find_withtag(key)
				except:
					print('프로그램을 종료합니다.')
					exit()
					
				img_dragon_idx = value[0]%len(self.img_dragon)

				if len(obj)==0:
					if self.user != key:
						print(key,' 사용자가 입장하였습니다.')
					self.canvas.create_image(value[1],value[2], image = self.img_dragon[img_dragon_idx],tags=key)
					self.canvas.create_text(value[1]+self.img_dragon[img_dragon_idx].width()/2,value[2]+self.img_dragon[img_dragon_idx].height()/2+20, font="Times 20 italic bold",fill='#ff00ff',text=key,tag=key)
					
				else:
					self.canvas.itemconfig(obj[0], image = self.img_dragon[img_dragon_idx])
					self.canvas.moveto(obj[0],value[1],value[2])
					self.canvas.moveto(obj[1],value[1]+self.img_dragon[img_dragon_idx].width()/2,value[2]+self.img_dragon[img_dragon_idx].height()/2+20)				

			self.display_lighting_effect()
			window.after(33)
			window.update()

		#
		self.client_socket.close()
		self.receive_thread.join()
		

	def keyReleaseHandler(self, event):
		key = str(event.keycode)
		if key in self.keys:
		    self.keys.remove(key)

	def lighting_effect(self):
		for i in range(0,random.randint(5,15)):
		    self.canvas.create_image(random.randint(0,self.canvas.winfo_width()),random.randint(0,self.canvas.winfo_height()), image = self.img_light_effect,anchor = NW,tags="lighting")
		
	def display_lighting_effect(self):		

		if(self.lightingTimer == -1):
			self.lightingTimer = time.time()
			self.lighting_effect()
		else:
			now = time.time()
			if(now - self.lightingTimer > 4.0):
			    self.lightingTimer = -1
			elif(now - self.lightingTimer > 2.0):
			    lightings = self.canvas.find_withtag("lighting")
			    for light in lightings:
			        self.canvas.delete(light)


	def keyPressHandler(self, event):
		key = str(event.keycode)
		self.keys.add(key)
	
	def handle_receive(self):
		while True:
			try:
				data = self.client_socket.recv(1024)#데이터가 수신될 때까지 대기함
			except:
				print("서버 연결 끊김")
				break			
			#byte를 문자열로 디코딩
			data = data.decode()
			#디코딩된 문자열은 json 형식으로 되어 있음
			#네트워크 딜레이로 인해 누적된 패킷중 마지막 패킷만 추출하기
			data = data[:data.rfind('}')+1]
			data = data[data.rfind('{'):]
			#패킷의 형식 오류 확인
			if len(data) > 0 and data[0] =='{' and data[-1] == '}':
				#json 형식을 딕셔너리 타입으로 변환 후 저장
				self.user_data = json.loads(data)
			else:
				pass#print('패킷오류')

			
if __name__ == '__main__':
	#사용자 아이디, 서버 IP, 연결포트 설정
	GameClient('CKang','127.0.0.1',4000) # GameClient 생성한다.

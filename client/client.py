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
		#사용자 아이디에서 공백 제거
		user = user.replace(" " , "")

		#네트워크 초기화 및 서버 연결
		#		
		self.port = port		# 연결 포트설정
		self.host = host		#서버 IP		
		self.user = user		#사용자 아이디 설정

		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect((self.host, self.port))

		#서버 연결 확인을 위한 패킷 송수신
		self.client_socket.sendall(self.user.encode())#서버에 사용자 아이디 전송
		data = self.client_socket.recv(1024)#서버응답 받기
		data = data.decode()#서버에서 받은 데이터를 문자열로 변환

		#서버 접속 확인: 접속 실패시 프로그램 종료
		if "Success" in data: print("서버에 접속하였습니다.")
		elif "Fail" in data:
			print(self.user, "동일한 사용자가 존재합니다. 사용자를 변경하기 바랍니다.")
			exit()
		else:
			print("서버에 접속에 실패하였습니다.","프로그램을 종료합니다.")
			exit()
		
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
		self.img_fire = PhotoImage(file = "image/fire_type2.png")
		self.img_bg = PhotoImage(file="image/bgimage2.png")		
		self.img_enemy = PhotoImage(file='image/spaceship.png').subsample(6)

		#배경 그리기.
		self.canvas.create_image(0,0, image = self.img_bg,anchor = NW,tags="bg")

		self.isDebugMode = False

		#캔버스에 그려질 미사일에 대한 100 개의 더미 생성, 안보이게 설정
		self.fire_obj_list = []
		self.fire_obj_debug_list = []
		for i in range(100):
			self.fire_obj_list.append(self.canvas.create_image(0,0, image = self.img_fire,state='hidden', tags="fire"))
			self.fire_obj_debug_list.append(self.canvas.create_rectangle(0,0,5,5, fill='white',state='hidden', tags="fire"))
			

		#캔버스에 그려질 적에 대한 100 개의 더미 생성, 안보이게 설정
		self.enemy_obj_list = []
		self.enemy_obj_debug_list = []
		for i in range(100):
			self.enemy_obj_list.append(self.canvas.create_image(0,0, image = self.img_enemy,state='hidden', tags="enemy"))
			self.enemy_obj_debug_list.append(self.canvas.create_rectangle(0,0,140,65,state='hidden', tags="enemy"))
								
        #배경사운드
		pygame.init()
		pygame.mixer.music.load("sound/bgm.wav") #Loading File Into Mixer
		pygame.mixer.music.play(-1) #Playing It In The Whole Device

		#충돌 이펙트 사운드
		self.sounds = pygame.mixer
		self.sounds.init()
		self.s_effect1 = self.sounds.Sound("sound/destruction.mp3")

		self.canvas.create_text(150,60,fill="white",font="Times 15 italic bold",text="입력키: ↑ , ↓ , ← , → , space")
		self.canvas.create_text(720,810,fill="white",font="Times 20 italic bold",text="Network Game Example")
		self.canvas.create_text(720,850,fill="white",font="Times 20 italic bold",text="Major of computer software, Gyeongsang National Universityty")

		#
		user_list_in = set()

		while True:

			#사용자 입력이 있을 경우 서버로 데이터 전송
			if(len(self.keys)>0):#각 키값을 ',' 구분된 아스키 코드 값으로 전송
				self.client_socket.sendall(','.join(str(e) for e in self.keys).encode())

			fire_obj_idx = 0
			
			user_list_from_server = set()

			for key, value in self.user_data.items():
				if key != 'enemy':
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
						self.canvas.create_text(value[1]+self.img_dragon[img_dragon_idx].width()/2,value[2]+self.img_dragon[img_dragon_idx].height()/2+20, font="Times 20 italic bold",fill='#ff00ff',text=key+' '+str(value[4]),tag=key)
						user_list_in.add(key)
						user_list_from_server.add(key)
					else:
						self.canvas.itemconfig(obj[0], image = self.img_dragon[img_dragon_idx])
						self.canvas.moveto(obj[0],value[1],value[2])

						#itemcget(item_id,속성): canvas item 들의 속성 값 가져오기
						pre_text = self.canvas.itemcget(obj[1],'text')
						post_text = key+' '+str(value[4])

						#값이 다르면 text 속성 업데이트, 충돌 사운드 재생
						if pre_text != post_text:
							self.canvas.itemconfig(obj[1], text=post_text)
							self.s_effect1.play()

						self.canvas.moveto(obj[1],value[1]+self.img_dragon[img_dragon_idx].width()/2,value[2]+self.img_dragon[img_dragon_idx].height()/2+20)
						user_list_from_server.add(key)

					for i in range(len(value[3])):
						if(fire_obj_idx < len(self.fire_obj_list)):
							self.canvas.itemconfig(self.fire_obj_list[fire_obj_idx],state='normal')
							self.canvas.moveto(self.fire_obj_list[fire_obj_idx],value[3][i][0],value[3][i][1])
							
							if self.isDebugMode:
								self.canvas.itemconfig(self.fire_obj_debug_list[fire_obj_idx],state='normal')
							else:
								self.canvas.itemconfig(self.fire_obj_debug_list[fire_obj_idx],state='hidden')

							self.canvas.moveto(self.fire_obj_debug_list[fire_obj_idx],value[3][i][0]+50,value[3][i][1])

							fire_obj_idx += 1
						else:#만약 보여되는 미사일 수가 더미로 미사일 수보다 많으면 추가로 만들기
							self.fire_obj_list.append(self.canvas.create_image(value[3][i][0],value[3][i][1], image = self.img_fire, tags="fire"))

							if self.isDebugMode:
								self.fire_obj_debug_list.append(self.canvas.create_rectangle(value[3][i][0],value[3][i][1],value[3][i][0]+5,value[3][i][1]+5, fill='white', tags="fire"))
							else:
								self.fire_obj_debug_list.append(self.canvas.create_rectangle(value[3][i][0],value[3][i][1],value[3][i][0]+5,value[3][i][1]+5, state='hidden', fill='white', tags="fire"))


			#서버에 접속이 끊긴 사용자들 제거
			user_list_exit = user_list_in - user_list_from_server			
			for u in list(user_list_exit):
				print(u,' 사용자가 퇴장하였습니다.')
				user_list_in.remove(u)
				objs = self.canvas.find_withtag(u)
				for o in objs:
					self.canvas.delete(o)
					
			#사용되지 않은 미사일 이미지들은 안보이게 설정
			for i in range(fire_obj_idx,len(self.fire_obj_list)):
				self.canvas.itemconfig(self.fire_obj_list[i],state='hidden')
				self.canvas.itemconfig(self.fire_obj_debug_list[i],state='hidden')

			enemy_obj_idx = 0
			#
			for p in self.user_data['enemy']:
				if(enemy_obj_idx < len(self.enemy_obj_list)):
					self.canvas.itemconfig(self.enemy_obj_list[enemy_obj_idx],state='normal')
					self.canvas.moveto(self.enemy_obj_list[enemy_obj_idx],p[0],p[1])

					if self.isDebugMode:
						self.canvas.itemconfig(self.enemy_obj_debug_list[enemy_obj_idx],state='normal')
					else:
						self.canvas.itemconfig(self.enemy_obj_debug_list[enemy_obj_idx],state='hidden')

					self.canvas.moveto(self.enemy_obj_debug_list[enemy_obj_idx],p[0],p[1])

					enemy_obj_idx += 1
				else:#만약 보여되는 적 수가 더미 적 수보다 많으면 추가로 만들기
					self.enemy_obj_list.append(self.canvas.create_image(p[0],p[1], image = self.img_enemy, tags="enemy"))

					if self.isDebugMode:
						self.enemy_obj_debug_list.append(self.canvas.create_rectangle(p[0],p[1],p[0]+5,p[1]+5, fill='red',  tags="enemy"))
					else:
						self.enemy_obj_debug_list.append(self.canvas.create_rectangle(p[0],p[1],p[0]+5,p[1]+5, state='hidden', fill='red',  tags="enemy"))

			#사용되지 않은 적 이미지들은 안보이게 설정
			for i in range(enemy_obj_idx,len(self.enemy_obj_list)):
				self.canvas.itemconfig(self.enemy_obj_list[i],state='hidden')
				self.canvas.itemconfig(self.enemy_obj_debug_list[i],state='hidden')

			self.display_lighting_effect()
			window.after(33)
			window.update()

		#
		self.client_socket.close()
		self.receive_thread.join()
		

	def keyReleaseHandler(self, event):
		if event.keycode==68:
			self.isDebugMode = not self.isDebugMode


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

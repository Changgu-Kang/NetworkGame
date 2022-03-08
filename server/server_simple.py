
import socket
import argparse
import threading
import time
import random
import json

user_data = {}
user_socket = {}

user_image_size = [280,249]
user_wnd_size = [1440,960]

#frame, 위치 x, 위치 y, 미사일
user_ini_data = [0,100,480]


def handle_sendToUsers():
    while 1:


        #각 사용자의 프레임 번호 업데이트
        for key in user_data.keys():            
            user_data[key][0] += 1


        #각 서버에 저장된 사용자 데이터를 모든 클라이언트에 전송
        for con in user_socket.values():  
            #딕셔너리 타입을 json 포맷 변환후 바이트형으로 인코딩
            user_encode_data = json.dumps(user_data).encode()
            #사용자에게 전송함
            try:
                con.sendall(user_encode_data)
            except:
                pass
      
        time.sleep(0.03)
            

def handle_receive(client_socket, addr, user):   
        
    while 1:
        try:
            #클라이언트로부터 데이터 올때까지 대기함
            data = client_socket.recv(1024)
            #클라이언트로부터 받은 데이터를 문자열 변환후 입력 키 값들을 분리한다.
            key_list = data.decode().split(',')
            for key in key_list:
                if key == '39' and user_data[user][1] < (user_wnd_size[0]-user_image_size[0]/2): # right direction key
                    user_data[user][1] = user_data[user][1] + 5
                elif key == '37' and -user_image_size[0]/2 < user_data[user][1]: # left direction key
                    user_data[user][1] = user_data[user][1] - 5
                elif key == '38' and -user_image_size[1]/2 < user_data[user][2]: # up direction key
                    user_data[user][2] = user_data[user][2] - 5
                elif key == '40' and user_data[user][2] < (user_wnd_size[1]-user_image_size[1]/2): # down direction key
                    user_data[user][2] = user_data[user][2] + 5

            
        except:
            print(user,': 연결 끊김')
            break

    del user_data[user]
    del user_socket[user]
    client_socket.close()

if __name__ == '__main__':

    host = "127.0.0.1"
    port = 4000
    

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen(5)# 클라이언트 최대 접속 수
    
    
    send_thread = threading.Thread(target=handle_sendToUsers)
    send_thread.daemon = True
    send_thread.start()

    print('게임서버를 시작합니다.')

    
    
    while 1:
        try:            
            client_socket, addr = server_socket.accept()#클라이언트 접속 까지 대기
        except KeyboardInterrupt:            
            for user, con in user_socket:
                con.close()
            server_socket_tcp.close()
            print("Keyboard interrupt")
            break

        user = client_socket.recv(1024)        
        user = user.decode()        

        user_socket[user] = client_socket
        user_data[user] = list(user_ini_data)

        receive_thread = threading.Thread(target=handle_receive, args=(client_socket, addr,user))
        receive_thread.daemon = True
        receive_thread.start()
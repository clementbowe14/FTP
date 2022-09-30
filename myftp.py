import sys, re
from socket import socket, AF_INET, SOCK_STREAM


transfer_socket = None
BUFFER_SIZE = 1024
DECODE_FORMAT = 'utf-8'
# get server name from command line
if len(sys.argv) != 2:
    print('Usage: myftp ftp_server_name')
    sys.exit()
server = sys.argv[1]

# create control connection socket
control_socket = socket(AF_INET, SOCK_STREAM)

# initiate control TCP connection
try:
    control_socket.connect((server, 21))
except Exception:
    print(f'Error: server {server} cannot be found.')
    sys.exit()
print(f'Connected to {server}.')

# print message from server
response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).strip()
print(response)

# send user name to server
username = input('Enter username: ')
control_socket.send(bytes(f'USER {username}\r\n', DECODE_FORMAT))
response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).strip()
print(response)

# send password to server
password = input('Enter password: ')
control_socket.send(bytes(f'PASS {password}\r\n', DECODE_FORMAT))
response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).strip()
print(response)

# login successful
if response.startswith('230'):
    # main loop
    loop = True
    while loop:
        print('Please enter a command.')
        command = input('myftp> ').split()
        
        if len(command) < 1:
            print("Error: no command entered")
            continue
        
        if command[0] == 'quit':
            # end session
            control_socket.send(bytes('QUIT\r\n', DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).strip()
            print(response)
            control_socket.close()
            loop = False
       
        elif command[0] == 'cd' :
            if len(command) < 2:
                print("Usage: cd <directory_name>")
                continue
                   
            control_socket.send(bytes('CWD {dir}\r\n'.format(dir=command[1]), DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT)
            print(response.strip())
        elif command[0] == 'ls':

            control_socket.send(bytes('PASV\r\n', DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).split()
            ip = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response[len(response)-1])
            print(response)
            address = (ip.group(1) + '.' + ip.group(2) + '.' + ip.group(3) + '.' + ip.group(4), int(ip.group(5)) * 256 + int(ip.group(6)))
            print(address)
            transfer_socket = socket(AF_INET, SOCK_STREAM)
            transfer_socket.connect(address)
            print('Connected transfer socket now sending items in directory')
                
            control_socket.send(bytes('LIST\r\n', DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT)
            print(response)

            while True:
                try:
                    msg = transfer_socket.recv(BUFFER_SIZE)
                    if len(msg) == 0:
                        break
                    print(msg.decode(DECODE_FORMAT))
                except Exception as e:
                    print(e)
                    break
            transfer_socket.close()
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT)
            print(response)
            
        elif command[0] == 'put':
            if len(command) < 2:
                print("Error: Command must be used with the format \"put <file_name>\"")
          
            control_socket.send(bytes('PASV\r\n', DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).split()
            ip = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response[len(response)-1])
            print(response)
            address = (ip.group(1) + '.' + ip.group(2) + '.' + ip.group(3) + '.' + ip.group(4), int(ip.group(5)) * 256 + int(ip.group(6)))
            print(address)
            transfer_socket = socket(AF_INET, SOCK_STREAM)
            transfer_socket.connect(address)
            print('Connected transfer socket now sending items in directory')
                
            control_socket.send(bytes('STOR {file}\r\n'.format(file=command[1]), DECODE_FORMAT))
            
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT)

            try:
                transfer_socket.send(open(command[1], 'rb').read())
                transfer_socket.close()
                response = control_socket.recv(BUFFER_SIZE)
                print(response)
                transfer_socket = None
            except Exception as e:
                print(e)
        elif command[0] == 'delete':
            
            if len(command) < 2:
                print("Error: You must enter a file to delete in the form \"delete <file_name>\"")
                
            control_socket.send(bytes('DELE {filename}\r\n'.format(filename=command[1]), DECODE_FORMAT))
            response = control_socket.recv(BUFFER_SIZE)
            print(response)
        elif command[0] == 'get':
            
            if len(command) < 2:
                print("Error: You must enter a file to get with the format \"get <file_name>\"")
            
            try:
                control_socket.send(bytes('PASV\r\n', DECODE_FORMAT))
                response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT).split()
                ip = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response[len(response)-1])
                print(response)
                address = (ip.group(1) + '.' + ip.group(2) + '.' + ip.group(3) + '.' + ip.group(4), int(ip.group(5)) * 256 + int(ip.group(6)))
                print(address)
                transfer_socket = socket(AF_INET, SOCK_STREAM)
                transfer_socket.connect(address)
                control_socket.send(bytes('RETR {filename}\r\n'.format(filename=command[1]), DECODE_FORMAT))
                response = control_socket.recv(BUFFER_SIZE)
                transfered_bytes = 0
                print(response)
                file = open(command[1], 'wb')
            except Exception as e:
                print(e)
                continue
                
            
            while True:
                try:
                    msg = transfer_socket.recv(BUFFER_SIZE)
                    transfered_bytes = transfered_bytes + len(msg)
                    if len(msg) == 0:
                        break
                except Exception as e:
                    print(e)
                    break
            file.close()
            transfer_socket.close()
            response = control_socket.recv(BUFFER_SIZE).decode(DECODE_FORMAT)
            print('{response}\n Total Bytes Transferred: {total}'.format(response=response, total=transfered_bytes))
            
        else:
            print(f'Error: command "{command}" not supported.'.format(command=command[0]))

    
import subprocess

process = []

while True:
    action = input(f'Chose action:\n'
                   f'q - Quit\n'
                   f's - Start server and client\n'
                   f'x - Close windows')

    if action == 'q':
        break
    elif action == 's':
        process.append(subprocess.Popen('python3 server.py',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                                        ))
    elif action == 'k':
        clients_count = int(input(f'Enter client count for start:'))
        for i in range(clients_count):
            process.append(subprocess.Popen(f'python3 client.py -n test{i + 1} -p 123456',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            victim = process.pop()
            victim.kill()

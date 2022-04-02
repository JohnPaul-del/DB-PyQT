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
        process.append(
            subprocess.Popen(
                'python3 server.py',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        )
        process.append(
            subprocess.Popen(
                'python3 client.py -n test1',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        )
        process.append(
            subprocess.Popen(
                'python3 client.py -n test2',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        )
        process.append(
            subprocess.Popen(
                'python3 client.py -n test3',
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        )
    elif action == 'x':
        while process:
            victim = process.pop()
            victim.kill()

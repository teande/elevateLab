import argparse

import Devmiko


def main(args):
    host = args.host
    username = args.username
    password = args.password
    gen_command = args.gen_command

    client = Devmiko.FTDClient(debug=False, filename=None, level='DEBUG')
    client.connect(host, username=username, password=password)

    client.send_command(command=gen_command)
    print(client.output)
    client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Address of Cisco FTD")
    parser.add_argument("--username", required=True, help="Username of Cisco FTD")
    parser.add_argument("--password", required=True, help="Password of Cisco FTD")
    parser.add_argument("--gen_command", required=True, help="Generated Command")
    args = parser.parse_args()
    main(args)

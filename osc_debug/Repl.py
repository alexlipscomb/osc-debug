from typing import List, Union

from cmd2 import Cmd, Statement
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


class Repl(Cmd):
    intro = "Welcome to the OSC Debugger.\nType help or ? to list commands.\n"
    prompt = "> "
    __port = 5005
    __host = "127.0.0.1"
    __exit_message = "Quitting"

    __port_range = (4096, 65535)

    __dispatcher: Dispatcher
    __server: ThreadingOSCUDPServer

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.__dispatcher = Dispatcher()
        self.__server = ThreadingOSCUDPServer(
            (self.__host, self.__port), self.__dispatcher
        )

    def start(self) -> None:
        self.cmdloop()

    def do_port(self, statement: Statement):
        """
        Set the OSC port

        Usage: PORT [port]
        """
        args = statement.arg_list
        if len(args) < 1:
            print(self.__port)
            return

        try:
            port = int(args[0])
            if port < self.__port_range[0] or port > self.__port_range[1]:
                print(
                    f"Invalid port. Use a port in the range {self.__format_port_range()}"
                )
                return

            self.__port = port
            print(f"Set port to {port}")
        except ValueError:
            print(
                f"Ports can only be a nonnegative integer between {self.__format_port_range()}"
            )

    def do_host(self, statement: Statement):
        """
        Set the OSC host

        Usage: HOST [host]
        """
        args = statement.arg_list
        if len(args) < 1:
            print(self.__host)
            return

        try:
            host = args[0]
            self.__host = host
            print(f"Set host to {host}")
        finally:
            ...

    def do_quit(self, _):
        """
        Quit the REPL

        Usage: QUIT
        """
        print(self.__exit_message)
        return True

    def do_server(self, statement: Statement):
        """
        Listen for OSC messages

        Usage: SERVER [SERVE|ADD|REMOVE|LIST]
        """

        args = statement.arg_list
        args_len = len(args)
        if args_len < 1:
            print(
                f"Incorrect number of arguments.\n\nUsage: SERVER [SERVE|ADD|REMOVE|LIST]"
            )
            return

        command = args[0].upper()
        if command == "SERVE":
            self.__start_server()
        elif command == "ADD":
            if args_len < 2:
                print(
                    "Invalid number of arguments.\n\nUsage: SERVER ADD [...addresses]"
                )
                return

            addresses = args[1:]
            self.__add_dispatcher_address(addresses)
        elif command == "REMOVE":
            if args_len < 2:
                try:
                    if (
                        input(
                            "Are you sure you want to remove all addresses? (Y/n) "
                        ).lower()
                        == "y"
                    ):
                        self.__remove_all_dispatcher_addresses()

                except EOFError:
                    return

            addresses = args[1:]
            self.__remove_dispatcher_address(addresses)
        elif command == "LIST":
            if len(self.__dispatcher._map) == 0:
                self.poutput("No handlers exist. Use SERVER ADD to add one")
                return

            for address in self.__dispatcher._map:
                self.poutput(address)

    def __start_server(self):
        try:
            self.poutput(f"Starting server on {self.__format_server_info()}")
            self.__server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            self.__server.shutdown()

    def __add_dispatcher_address(self, addresses: Union[str, List[str]]):
        for address in addresses:
            if address in self.__dispatcher._map:
                self.poutput(f"Address {address} is already in use")
                continue

            self.__dispatcher.map(address, self.__format_osc_message)

    def __remove_dispatcher_address(self, addresses: Union[str, List[str]]):
        for address in addresses:
            self.__dispatcher.unmap(address, self.__format_osc_message)

    def __remove_all_dispatcher_addresses(self):
        for address, handlers in self.__dispatcher._map.items():
            for handler in handlers:
                self.__dispatcher.unmap(address, handler)

    def __format_osc_message(self, address, *values):
        self.poutput(f"{address} {values}")

    def do_send(self, statement: Statement):
        """
        Send an OSC message

        Usage: SEND [address] [...messages]
        """
        args = statement.arg_list
        if len(args) < 2:
            print("Invalid number of arguments.\n\nUsage: SEND [address] [...messages]")
            return

        address = args[0]
        messages = args[1:]
        print(address)
        print(messages)

        client = SimpleUDPClient(self.__host, self.__port)

        client.send_message(address, messages)

    def __format_port_range(self) -> str:
        return f"[{self.__port_range[0]}, {self.__port_range[1]}]"

    def __format_server_info(self) -> str:
        return f"host={self.__host}, port={self.__port}"

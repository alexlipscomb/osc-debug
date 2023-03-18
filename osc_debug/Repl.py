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
            self.poutput(self.__port)
            return

        try:
            port = int(args[0])
            if port < self.__port_range[0] or port > self.__port_range[1]:
                self.poutput(
                    f"Invalid port. Use a port in the range {self.__format_port_range()}"
                )
                return

            self.__port = port
            self.poutput(f"Set port to {port}")
        except ValueError:
            self.poutput(
                f"Ports can only be a nonnegative integer between {self.__format_port_range()}"
            )

    def do_host(self, statement: Statement):
        """
        Set the OSC host

        Usage: HOST [host]
        """
        args = statement.arg_list
        if len(args) < 1:
            self.poutput(self.__host)
            return

        try:
            host = args[0]
            self.__host = host
            self.poutput(f"Set host to {host}")
        finally:
            ...

    def do_quit(self, _):
        """
        Quit the REPL

        Usage: QUIT
        """
        self.poutput(self.__exit_message)
        return True

    def do_add(self, statement: Statement):
        """Add an OSC address to the server

        Usage: ADD [...addresses]
        """
        args = statement.arg_list
        args_len = len(args)

        if args_len < 1:
            self.poutput("Invalid number of arguments.\n\nUsage: ADD [...addresses]")
            return

        self.__add_dispatcher_address(args)

    def do_remove(self, statement: Statement):
        """Remove an OSC address from the server

        Usage: REMOVE [...addresses]
        """
        args = statement.arg_list
        args_len = len(args)

        if args_len < 1:
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

            self.__remove_dispatcher_address(args)

    def do_listen(self, _):
        """
        Start the OSC server

        Usage: LISTEN
        """
        self.__start_server()

    def do_list(self, _):
        """
        List all OSC addresses

        Usage: LIST
        """

        if len(self.__dispatcher._map) == 0:
            self.poutput("No handlers exist. Use ADD to add one")
            return

        for address in self.__dispatcher._map:
            self.poutput(address)

    def __start_server(self):
        try:
            self.poutput(f"Starting server on {self.__format_server_info()}")
            self.__server.serve_forever()
        except KeyboardInterrupt:
            self.poutput("\nStopping server...")
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
            self.poutput(
                "Invalid number of arguments.\n\nUsage: SEND [address] [...messages]"
            )
            return

        address = args[0]
        messages = args[1:]

        client = SimpleUDPClient(self.__host, self.__port)

        client.send_message(address, messages)

    def __format_port_range(self) -> str:
        return f"[{self.__port_range[0]}, {self.__port_range[1]}]"

    def __format_server_info(self) -> str:
        return f"host={self.__host}, port={self.__port}"

# https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/patterns/client_server.html
import msgpack
import zmq


def main() -> None:
    port = 5555
    context = zmq.Context()
    print("Connecting to server...")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:%s" % port)

    for request in range(1, 10):
        print("Sending request ", request, "...")
        msg = {"hello": f"cat: {request}"}
        socket.send(msgpack.dumps(msg))
        _message = socket.recv()
        message = msgpack.loads(_message)
        print("Received reply ", request, "[", message, "]")


if __name__ == "__main__":
    main()

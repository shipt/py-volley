import sys

def run() -> None:
    component = sys.argv[1]
    if component == "external_producer":
        from example.external_data_producer import main
    elif component == "input_worker":
        from example.input_worker import main
    elif component == "middle_worker":
        from example.middle_worker import main
    elif component == "external_consumer":
        from example.external_data_consumer import main
    else:
        raise NotImplementedError(f"{component=} not implemented")
    main()

if __name__ == "__main__":
    run()

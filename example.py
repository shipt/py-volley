import sys
def run() -> None:
    component = sys.argv[1]
    if component == "external_producer":
        from example.external_data_producer import main
    elif component == "input_component":
        from example.input_component import main
    elif component == "component_1":
        from example.comp1 import main
    elif component == "external_consumer":
        from example.external_data_consumer import main
    else:
        raise NotImplementedError(f"{component=} not implemented")
    main()

if __name__ == "__main__":
    run()

import sys

if __name__ == "__main__":
    # TODO: can we get rid of this file entirely? just call each component.py directly? 
    component = sys.argv[1]

    if component == "dummy_events":
        from components.dummy_events import main
    elif component == "features":
        from components.features import main
    elif component == "triage":
        from components.triage import main
    elif component == "optimizer":
        from components.optimizer import main
    elif component == "fallback":
        from components.fallback import main
    elif component == "collector":
        from components.collector import main
    elif component == "dummy_consumer":
        from components.dummy_consumer import main
    else:
        raise NotImplementedError(f"{component=} not implemented")
    main()
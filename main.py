import sys

if __name__ == "__main__":
    component = sys.argv[1]

    if component == "dummy_events":
        from components.dummy_events import main
    elif component == "features":
        from components.feature_generator import main
    elif component == "triage":
        from components.triage import main
    elif component == "collector":
        from components.collector import main
    elif component == "dummy_consumer":
        from components.dummy_consumer import main
    main()
        
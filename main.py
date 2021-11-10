import os
import sys

import rollbar

rollbar.init(os.getenv("ROLLBAR_TOKEN"), os.getenv("APP_ENV", "localhost"))


def run() -> None:
    # TODO: can we get rid of this file entirely? just call each component.py directly?
    component = sys.argv[1]
    if component == "dummy_events":
        from components.dummy_events import main
    elif component == "features":
        from components.features import main  # type: ignore
    elif component == "triage":
        from components.triage import main  # type: ignore
    elif component == "optimizer":
        from components.optimizer import main  # type: ignore
    elif component == "fallback":
        from components.fallback import main  # type: ignore
    elif component == "collector":
        from components.collector import main  # type: ignore
    elif component == "publisher":
        from components.publisher import main  # type: ignore
    elif component == "dummy_consumer":
        from components.dummy_consumer import main  # type: ignore
    else:
        raise NotImplementedError(f"{component=} not implemented")
    main()


if __name__ == "__main__":
    run()

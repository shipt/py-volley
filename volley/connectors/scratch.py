from dataclasses import dataclass

@dataclass
class Foo:
    config_dict: dict

@dataclass
class Bar:
    config_dict: dict

if __name__ == "__main__":
    d = {"get": "them"}
    f = Foo(config_dict=d.copy())
    b = Bar(config_dict=d.copy())
    # print(id(f.config_dict))
    # print(id(b.config_dict))
    print(b.config_dict is f.config_dict)
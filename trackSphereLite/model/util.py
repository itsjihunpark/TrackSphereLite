def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper


# decorator example
def decorator(func):
    def wrapper():
        print("before calling the function")
        func()
        print("after running the function")
    
    return wrapper

@decorator
def greet():
    print("Hello, world")

if __name__ == "__main__":
    greet()
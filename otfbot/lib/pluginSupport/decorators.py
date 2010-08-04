def registerCallback(func):
    func.is_callback=True
    func.priority=10
    return func

def registerCallbackWithPriority(priority):
    def decorator(func):
        func.is_callback=True
        func.priority=priority
        return func
    return decorator

def callback(func):
    func.is_callback=True
    func.priority=10
    return func

def callback_with_priority(priority):
    def decorator(func):
        func.is_callback=True
        func.priority=priority
        return func
    return decorator

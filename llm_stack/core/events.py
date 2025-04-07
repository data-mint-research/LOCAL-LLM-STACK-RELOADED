"""
Event system for component communication.

This module provides an event emitter implementation that allows components
to communicate with each other through an event-based system.
"""


class EventEmitter:
    """Event emitter for component communication."""
    
    def __init__(self):
        """Initialize the event emitter."""
        self.listeners = {}
    
    def on(self, event, callback):
        """Register a callback for an event.
        
        Args:
            event: The event name to listen for.
            callback: The function to call when the event is emitted.
        """
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
    
    def emit(self, event, *args, **kwargs):
        """Emit an event.
        
        Args:
            event: The event name to emit.
            *args: Positional arguments to pass to the callbacks.
            **kwargs: Keyword arguments to pass to the callbacks.
        """
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args, **kwargs)


# Example usage:
"""
# Create an event emitter
emitter = EventEmitter()

# Register a callback for an event
def on_data_received(data):
    print(f"Received data: {data}")

emitter.on("data_received", on_data_received)

# Emit an event
emitter.emit("data_received", {"message": "Hello, world!"})
# Output: Received data: {'message': 'Hello, world!'}

# Multiple callbacks can be registered for the same event
def log_data(data):
    print(f"Logging data: {data}")

emitter.on("data_received", log_data)

# Both callbacks will be called when the event is emitted
emitter.emit("data_received", {"message": "Hello again!"})
# Output: 
# Received data: {'message': 'Hello again!'}
# Logging data: {'message': 'Hello again!'}
"""
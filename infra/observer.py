class Observer:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        import weakref
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        # Use weakref for bound methods, store as (is_weak, ref)
        if hasattr(callback, '__self__') and hasattr(callback, '__func__'):
            # Bound method
            ref = weakref.WeakMethod(callback)
            self._subscribers[event_type].append((True, ref))
        else:
            # Function or static method
            self._subscribers[event_type].append((False, callback))

    def unsubscribe(self, event_type, callback):
        if event_type in self._subscribers:
            import weakref
            to_remove = None
            for i, (is_weak, ref) in enumerate(self._subscribers[event_type]):
                if is_weak:
                    # Compare bound method
                    if hasattr(callback, '__self__') and hasattr(callback, '__func__'):
                        if ref() is callback:
                            to_remove = i
                            break
                else:
                    if ref == callback:
                        to_remove = i
                        break
            if to_remove is not None:
                self._subscribers[event_type].pop(to_remove)

    def dispatch(self, event_type, data):
        if event_type in self._subscribers:
            import weakref
            new_list = []
            for is_weak, ref in self._subscribers[event_type]:
                cb = ref() if is_weak else ref
                if cb is not None:
                    try:
                        cb(data)
                        new_list.append((is_weak, ref))
                    except Exception as e:
                        # ...removed debug print...
                        pass
                # else: dead weakref, do not keep
            self._subscribers[event_type] = new_list
# Architectural Debt & Refactoring Roadmap

## Critical Issues (Security/Stability)

### 1. **__del__ in PySide Objects** ⚠️ DANGER - SEGFAULT RISK
**Severity:** CRITICAL  
**Location:** `ui/items/pin.py` (FIXED - removed in commit)  
**Impact:** Causes segfaults and memory leaks  

**Problem:**
- Python `__del__` is unreliable with Qt C++ ownership
- Qt may delete underlying C++ object before Python GC runs `__del__`
- Accessing `self.pin` in `__del__` causes segfault if C++ object already deleted
- Python circular references may delay GC indefinitely

**Solution:** ✅ FIXED
- Removed `__del__` from `PinItem`
- Use Qt signals (`destroyed`) or `itemChange(ItemSceneHasChanged)` for lifecycle events

**Status:** FIXED in this commit

---

### 2. **Split Brain Dispatcher** - Dual Registries
**Severity:** HIGH  
**Location:** `api/actions.py` + `dispatcher.py`  
**Impact:** Code smell, maintenance burden, unclear ownership  

**Problem:**
```python
# api/actions.py has ActionRegistry
registry.register("edit.delete", delete_action)

# ALSO registers in dispatcher.py DispatcherRegistry
dispatcher_registry.register("edit.delete", delete_action)  # DUPLICATE!
```

**Why It's Bad:**
- Two sources of truth for action→handler mapping
- Duplicate registrations for every action
- Unclear which registry owns which responsibility
- Brittle synchronization between registries

**Solution:** Consolidate to single registry in `dispatcher.py`
1. Delete `ActionRegistry` class from `api/actions.py`
2. Move all registration to `dispatcher.registry`
3. Update all `registry.register()` calls to `dispatcher_registry.register()`
4. Update tests to expect single registry

**Status:** Documented with TODO comments, needs systematic refactor

---

## High Priority (Performance/Maintainability)

### 3. **Circular Import Workarounds** - Late Binding Pattern
**Severity:** MEDIUM-HIGH  
**Location:** Throughout codebase  
**Impact:** Slow imports, hard to refactor, brittle dependencies  

**Problem:**
```python
def some_function():
    from api.commands import DeleteDeviceCommand  # import INSIDE function
    ...
```

**Why It's Bad:**
- Hides true dependency graph
- Import overhead on every function call
- Hard to detect circular dependencies until runtime
- Refactoring tools can't analyze dependencies

**Solution:** Use Dependency Injection pattern
1. Create `bootstrap.py` that imports all commands once
2. Pass command registry to classes that need commands
3. Use abstract interfaces, not concrete imports

**Example:**
```python
# bootstrap.py
from api.commands import DeleteDeviceCommand, AddDeviceCommand
COMMAND_REGISTRY = {
    'delete_device': DeleteDeviceCommand,
    'add_device': AddDeviceCommand
}

# manager.py
class APIManager:
    def __init__(self, command_registry):
        self.commands = command_registry
    
    def delete_device(self, device):
        cmd = self.commands['delete_device'](device)
        cmd.execute()
```

**Status:** Identified, needs architectural refactor

---

### 4. **Granular Observable Pattern** - N×N Observers
**Severity:** MEDIUM  
**Location:** `ui/items/base.py` - `ObservableGraphicsItemMixin`  
**Impact:** Performance degradation at scale (5000 pins = 5000 observers)  

**Problem:**
```python
class PinItem(ObservableGraphicsItemMixin, QGraphicsEllipseItem):
    # Every PinItem subscribes to its own Pin model
    # 5000 pins = 5000 separate observer subscriptions
```

**Why It's Bad:**
- O(N) overhead for N items
- Each item registers individual observer callback
- Doesn't scale beyond a few hundred items

**Solution:** Scene-Level Observer Pattern
```python
# Canvas subscribes ONCE to ALL model changes
class HarnessCanvas:
    def __init__(self):
        self.item_lookup = {}  # {model_id: QGraphicsItem}
        api.context.harness.subscribe(self.on_model_changed)
    
    def on_model_changed(self, model_id):
        item = self.item_lookup.get(model_id)
        if item:
            item.update_from_model()
```

**Benefits:**
- Single observer for entire scene
- O(1) lookup via hash table
- Scales to tens of thousands of items

**Status:** Identified, needs performance profiling before refactor

---

### 5. **Brittle UUID/Config Mapping** - build_actions_map Fragility
**Severity:** MEDIUM  
**Location:** `api/actions.py:build_actions_map()`  
**Impact:** Runtime errors from config/code desync, hard to maintain  

**Problem:**
```python
def build_actions_map():
    # Parses ui_layout.yaml to find command IDs
    # Parses en.yaml to find i18n labels
    # Manually maps command→UUID in code
    # UUID→label must be added to en.yaml manually
```

**Why It's Bad:**
- Three sources of truth (code, layout YAML, i18n YAML)
- Adding new command requires editing 3+ files
- No compile-time validation of UUID→command mapping
- Missing UUID in en.yaml = silent failure (shows UUID as label)

**Solution:** Invert Control - Define UUIDs on Commands
```python
# api/commands.py
class DeleteDeviceCommand(BaseCommand):
    UUID = "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"
    LABEL = "Delete Device"
    
# bootstrap.py scans all commands
def build_command_registry():
    from api import commands
    registry = {}
    for name, obj in inspect.getmembers(commands, inspect.isclass):
        if issubclass(obj, BaseCommand) and hasattr(obj, 'UUID'):
            registry[obj.UUID] = obj
            registry[name.lower().replace('command', '')] = obj
    return registry
```

**Benefits:**
- Single source of truth (command class)
- Compile-time validation (IDE detects duplicate UUIDs)
- Automatic registration via reflection
- Type-safe command→UUID mapping

**Status:** Identified, needs command system refactor

---

### 6. **ThemeManager Per-Instance Creation** - Unnecessary Object Creation
**Severity:** LOW-MEDIUM  
**Location:** `ui/items/pin.py:__init__()`  
**Impact:** Memory waste, repeated file I/O  

**Problem:**
```python
class PinItem:
    def __init__(self, pin, api):
        self.theme = ThemeManager()  # Creates NEW ThemeManager for EVERY pin
```

**Why It's Bad:**
- 5000 pins = 5000 ThemeManager instances
- Each reads `theme_tokens.json` from disk
- Wastes memory for duplicate theme data

**Solution:** Singleton or Inject ThemeManager
```python
# Singleton pattern
class PinItem:
    _theme = None
    
    def __init__(self, pin, api):
        if PinItem._theme is None:
            PinItem._theme = ThemeManager()
        self.theme = PinItem._theme

# OR Dependency Injection (better)
class PinItem:
    def __init__(self, pin, api, theme_manager):
        self.theme = theme_manager
```

**Status:** Identified, low priority optimization

---

## Summary: Fixed vs Remaining

### ✅ Fixed in This Session
1. **__del__ in PinItem** - Removed dangerous `__del__` method
2. **UUID Labels in en.yaml** - Added missing context menu UUIDs
3. **MVC Violations** - Fixed 6 architectural violations (View mutation, selection, registration, etc.)
4. **Context Menu Detection** - Fixed InputSystem item detection bug

### 🔄 Documented (TODOs Added)
1. **Split Brain Dispatcher** - Added TODO comments, restored duplicate registrations temporarily
2. **Circular Imports** - Documented pattern, needs DI refactor
3. **Observable Granularity** - Documented performance issue, needs profiling
4. **UUID/Config Mapping** - Documented fragility, needs command system redesign
5. **ThemeManager Instances** - Documented waste, needs singleton/injection

### 📋 Recommended Priority
1. **Split Brain Dispatcher** (HIGH) - Consolidate registries
2. **Circular Imports** (MEDIUM) - Introduce bootstrap + DI
3. **Observable Pattern** (MEDIUM) - Profile first, optimize if needed
4. **UUID Control Inversion** (MEDIUM) - Redesign command system
5. **ThemeManager** (LOW) - Optimize after proving bottleneck

---

## Migration Strategy

### Phase 1: Registry Consolidation (2-3 days)
- [ ] Audit all `registry.register()` calls
- [ ] Move to `dispatcher.registry` exclusively
- [ ] Delete `ActionRegistry` class
- [ ] Update tests

### Phase 2: Dependency Injection (3-5 days)
- [ ] Create `bootstrap.py` with command registry
- [ ] Refactor circular imports to DI pattern
- [ ] Use abstract interfaces for dependencies

### Phase 3: Performance Optimization (1-2 weeks)
- [ ] Profile Observable pattern overhead
- [ ] Implement Scene-Level Observer if needed
- [ ] Optimize ThemeManager instantiation

### Phase 4: Command System Redesign (1-2 weeks)
- [ ] Define UUIDs on Command classes
- [ ] Auto-generate actions_map via reflection
- [ ] Eliminate manual UUID→label mapping

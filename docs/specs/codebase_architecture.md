# Talus Trace Implementation Architecture

## 1. Directory Structure
* `core/`: Pure Python Data Models (No Qt).
* `infra/`: System Services (IO, Commands).
* `api/`: Public Singleton Interface.
* `ui/`: Qt/PySide6 View Layer.

## 2. Dependency Rules
* Core is Holy: Cannot import UI or Infra.
* UI is Dumb: Fires Commands via API.
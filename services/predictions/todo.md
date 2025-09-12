# Predictions Service Cleanup Plan

## Current State Analysis
The predictions service has ~1,675 lines of code across multiple modules with both strengths and areas for improvement.

**Strengths:**
- Good separation of concerns with dedicated modules for config, models, validation
- Pydantic models for data validation
- Comprehensive configuration management
- MLflow integration for model tracking

**Key Issues Identified:**

## 1. Code Organization & Structure
- **Missing abstractions**: No base classes or interfaces for models
- **Inconsistent imports**: Some modules import at function level, others at module level  
- **Mixed concerns**: `main.py` contains both streaming logic and dummy model implementation
- **Debug code**: `debug.py` contains test/debug code that should be removed or moved

## 2. Error Handling & Validation
- **Inconsistent exception handling**: Mix of generic exceptions and custom ones
- **TODOs and incomplete features**: Several TODO comments indicating unfinished work
- **Missing import**: `risingwave_api` module imported but doesn't exist

## 3. Code Quality Issues
- **Magic numbers**: Hardcoded values throughout codebase
- **Long functions**: Some functions (especially in `train.py`) are too long
- **Duplicate code**: Similar logic repeated across modules
- **Type hints**: Inconsistent use of type annotations

## 4. Configuration & Dependencies
- **Hardcoded credentials**: Passwords visible in config files
- **Unused imports**: Several unused dependencies
- **Missing validation**: Some config values lack proper validation

## Proposed Improvements:

### Phase 1: Core Cleanup (High Priority) ✅ COMPLETED
- [x] **Remove debug code** and unused files
- [x] **Fix missing imports** and broken dependencies  
- [x] **Standardize exception handling** across all modules
- [x] **Extract constants** to eliminate magic numbers
- [x] **Add missing type hints** throughout codebase

### Phase 2: Structural Refactoring (Medium Priority)  
- [ ] **Create base model interfaces** for better abstraction
- [ ] **Split large functions** into smaller, focused methods
- [ ] **Improve separation of concerns** in main.py
- [ ] **Standardize import patterns** across modules
- [ ] **Add comprehensive logging** strategy

### Phase 3: Advanced Improvements (Lower Priority)
- [ ] **Add unit tests** for critical components
- [ ] **Implement proper dependency injection**
- [ ] **Add configuration validation** improvements
- [ ] **Create proper documentation** structure
- [ ] **Add performance monitoring** hooks

Each improvement will maintain backward compatibility while making the codebase more maintainable, testable, and robust.
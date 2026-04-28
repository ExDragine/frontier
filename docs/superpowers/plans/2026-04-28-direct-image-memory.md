# Direct Image Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist chat images and feed saved image files directly to the main model for all included history messages.

**Architecture:** Keep the existing `MessageImage` file-backed storage. Simplify context preparation so every included history message attempts to load its saved image files, and remove the fireside image-summary task path.

**Tech Stack:** Python, SQLModel, pytest, NoneBot plugin tests.

---

### Task 1: Database Context Preparation

**Files:**
- Modify: `test/utils/database_test.py`
- Modify: `utils/database.py`

- [ ] **Step 1: Write the failing test**

Add a test that inserts twelve historical messages with images, calls `prepare_message()` without an image window argument, and asserts all available images are present in the returned multimodal content.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest test/utils/database_test.py::test_prepare_message_injects_all_available_images_without_window_limit -v`

Expected: FAIL because only the former default image window is represented as `image_url`.

- [ ] **Step 3: Write minimal implementation**

Remove the image-window parameter and filtering, then load saved image files for every selected history message. Preserve `[图片]` for missing files.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest test/utils/database_test.py::test_prepare_message_injects_all_available_images_without_window_limit -v`

Expected: PASS.

### Task 2: Fireside Image Summary Removal

**Files:**
- Create: `test/plugins/fireside_image_memory_test.py`
- Modify: `plugins/fireside/__init__.py`

- [ ] **Step 1: Write the failing test**

Add a plugin test that stubs the message database, runs `handle_common()` with an image-bearing event, and asserts only `insert_images()` is called, with no image-summary scheduling.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest test/plugins/fireside_image_memory_test.py -v`

Expected: FAIL while the fireside handler still calls `schedule_image_summary_write()`.

- [ ] **Step 3: Write minimal implementation**

Delete the image-summary coroutine and scheduler from `plugins/fireside/__init__.py`, remove unused imports, and leave image saving in place.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest test/plugins/fireside_image_memory_test.py -v`

Expected: PASS.

### Task 3: Focused Regression

**Files:**
- Verify: `test/utils/database_test.py`
- Verify: `test/plugins/fireside_image_memory_test.py`
- Verify: `test/plugins/watchtower_init_test.py`

- [ ] **Step 1: Run focused tests**

Run: `.venv/bin/pytest test/utils/database_test.py test/plugins/fireside_image_memory_test.py test/plugins/watchtower_init_test.py -v`

Expected: PASS for the changed behavior and nearby plugin startup/settings coverage.

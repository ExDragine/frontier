# Direct Image Memory Design

## Goal

Persist incoming message images as files and pass those files directly back to the main model whenever the corresponding history message is included.

## Scope

This replaces the previous image-summary path. The system no longer asks the auxiliary model to describe images, no longer writes image summaries, and no longer uses an image history window to decide which saved images can be sent.

## Behavior

- Incoming images are saved through `MessageDatabase.insert_images()`.
- `MessageDatabase.prepare_message()` loads every saved image for the selected history messages when the file still exists.
- Messages with available images are represented as multimodal message content: one text block followed by one `image_url` block per saved image.
- If a database record points to a missing image file, the text still includes a simple `[图片]` marker.
- Image TTL cleanup remains responsible for bounding disk usage.

## Files

- `utils/database.py`: simplify image retrieval and remove `image_window_size` from `prepare_message()`.
- `plugins/fireside/__init__.py`: remove image-summary background tasks and stop calling the auxiliary model for image abstraction.
- `test/utils/database_test.py`: cover direct injection of images outside the former window.
- `test/plugins/fireside_image_memory_test.py`: cover that image saving no longer schedules summary generation.

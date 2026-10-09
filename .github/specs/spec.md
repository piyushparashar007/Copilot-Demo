# Product Specification: Personal Bookmark Manager with Tagging

## 1. Core Purpose & User Context
Develop a personal bookmark manager that enables users to save URLs, assign tags, and search or filter their stored bookmarks. The application helps users efficiently organize web resources encountered during research or everyday browsing. It must run locally and provide a web-based user interface accessible through a browser.

## 2. Core Functional Requirements & Acceptance Criteria
- **Add Bookmark**: User can submit a URL with an optional title. If no title is provided, the application should attempt to retrieve a useful page title from the web page metadata. If retrieval fails, handle it gracefully.
- **Tag Bookmarks**: User can assign one or more tags to a bookmark.
- **List Bookmarks**: User can view all saved bookmarks, with the most recent entries first (chronological order).
- **Filter by Tag**: User can select a tag and see only bookmarks associated with that tag.
- **Search**: User can search bookmarks by title or URL.
- **Edit Bookmark**: User can change the URL, title, or tags of an existing bookmark.
- **Delete Bookmark**: User can remove a bookmark. Provide a reasonable confirmation or safeguard against accidental deletion.
- **Persistence**: Bookmarks must remain available after the application is stopped and restarted (no pure in-memory lost states).
- **Validation**: Clearly invalid or empty URLs should not be saved; show understandable feedback to the user.
- **Duplicate Handling**: The application should detect or sensibly handle attempts to save the same URL more than once.
- **Empty/Error States**: Handle cases such as no bookmarks, no search results, title-fetch failure, and invalid input in a user-friendly way.

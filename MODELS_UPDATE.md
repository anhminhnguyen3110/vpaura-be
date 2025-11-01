# Models Update Summary

## ✅ Completed: New Database Models Structure

### 1. Updated Models

#### **User** (Updated)
```python
- username: String(100), unique, indexed
- email: String(255), unique, indexed  
- fullname: String(255)
- threads: relationship → Thread
- documents: relationship → Document
```

#### **Thread** (Replaces Conversation)
```python
- title: String(255)
- user_id: ForeignKey → users.id
- metadata: JSON (nullable) - for storing thread settings
- user: relationship → User
- chat_messages: relationship → ChatMessage
- documents: relationship → Document (many-to-many)
```

#### **ChatMessage** (Replaces Message)
```python
- content: Text
- role: Enum(MessageRole)
- thread_id: ForeignKey → threads.id
- metadata: JSON (nullable) - for tokens, model info, etc
- thread: relationship → Thread
```

#### **Document** (New)
```python
- title: String(255)
- content: Text
- file_path: String(500), nullable
- file_type: String(50), nullable - pdf, txt, docx, etc
- metadata: JSON (nullable) - file size, pages, etc
- user_id: ForeignKey → users.id
- user: relationship → User
- threads: relationship → Thread (many-to-many)
```

#### **thread_documents** (Association Table)
```python
- thread_id: ForeignKey → threads.id
- document_id: ForeignKey → documents.id
```

---

### 2. New Repositories Created

- ✅ `ThreadRepository` - CRUD for threads
- ✅ `ChatMessageRepository` - CRUD for chat messages
- ✅ `DocumentRepository` - CRUD for documents
- ✅ `UserRepository` - Updated with `get_by_username()`

---

### 3. New Schemas Created

- ✅ `ThreadCreate`, `ThreadUpdate`, `ThreadResponse`
- ✅ `ChatMessageCreate`, `ChatMessageUpdate`, `ChatMessageResponse`
- ✅ `DocumentCreate`, `DocumentUpdate`, `DocumentResponse`
- ✅ `UserCreate`, `UserUpdate`, `UserResponse` (updated)

---

### 4. Database Migration

Run these commands to create and apply migration:

```bash
# Generate migration
uv run alembic revision --autogenerate -m "Add Thread, ChatMessage, Document models"

# Apply migration
uv run alembic upgrade head
```

---

### 5. Key Features

**Thread Model:**
- Replaces Conversation
- Has metadata JSON for flexible settings
- Many-to-many with Documents
- One-to-many with ChatMessages

**ChatMessage Model:**
- Replaces Message
- Has metadata JSON for storing token usage, model info
- Belongs to Thread

**Document Model:**
- Store file content or reference
- Can be attached to multiple threads
- Has metadata for file information
- Belongs to User

**User Model:**
- Added fullname field
- Username is now unique and indexed
- Relationships updated to threads and documents

---

### 6. Old Models (Kept for backward compatibility)

- `Conversation` - Still exists but should migrate to Thread
- `Message` - Still exists but should migrate to ChatMessage

---

### 7. Next Steps

1. Generate and run migration
2. Update existing services to use new models
3. Update API routes to use Thread instead of Conversation
4. Create services for Document management
5. Update chatbot to save to ChatMessage instead of Message
6. Add document attachment to threads functionality

---

## Database Relationships

```
User
├── threads (One-to-Many)
└── documents (One-to-Many)

Thread
├── user (Many-to-One)
├── chat_messages (One-to-Many)
└── documents (Many-to-Many via thread_documents)

ChatMessage
└── thread (Many-to-One)

Document
├── user (Many-to-One)
└── threads (Many-to-Many via thread_documents)
```

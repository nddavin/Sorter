# User Guide

This guide covers how to use the Sorter file processing system for end users.

## Getting Started

### Accessing the Application

- **Web Interface**: Open your browser and navigate to `http://localhost:5000`
- **API Documentation**: Access Swagger docs at `http://localhost:8000/docs`

### Account Creation

1. Click "Register" on the web interface
2. Fill in required fields (username, email, password)
3. Verify your email (if email configured)
4. Log in with your credentials

### Password Requirements

Your password must meet the following requirements:
- At least 12 characters long
- Contains uppercase and lowercase letters
- Contains at least one number
- Contains at least one special character

---

## File Upload

### Using the Web Interface

1. Navigate to the upload page
2. Drag and drop files or click to browse
3. Select files (max 100MB per file)
4. Click "Upload"
5. Wait for processing to complete

### Using the API

```python
import requests

# Upload a file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    print(response.json())
```

### Chunked Upload (Large Files)

For files larger than 100MB, use chunked upload:

```python
import requests

# Initialize upload
response = requests.post(
    'http://localhost:8000/api/upload/init',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={'filename': 'large_file.mp4', 'size': 500000000}
)
upload_id = response.json()['upload_id']

# Upload chunks (5MB each)
chunk_size = 5 * 1024 * 1024
with open('large_file.mp4', 'rb') as f:
    chunk_num = 0
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        files = {'chunk': chunk}
        data = {'upload_id': upload_id, 'chunk_num': chunk_num}
        requests.post(
            'http://localhost:8000/api/upload/chunk',
            files=files,
            data=data,
            headers={'Authorization': 'Bearer YOUR_TOKEN'}
        )
        chunk_num += 1

# Complete upload
requests.post(
    'http://localhost:8000/api/upload/complete',
    json={'upload_id': upload_id},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

---

## Managing Files

### Viewing Files

- Navigate to "Files" section to see all uploaded files
- Use filters to narrow down by type, date, or category
- Search by filename or content

### File List Features

| Feature | How to Use |
|---------|------------|
| Search | Type in search bar to find files |
| Filter by Type | Click filter icon, select file type |
| Sort | Click column headers to sort |
| Bulk Select | Checkbox on left of each row |
| View Details | Click file name or info icon |

### Downloading Files

1. Find the file in your list
2. Click the download button
3. File will be downloaded as attachment

### Deleting Files

1. Select the file(s) you want to delete
2. Click "Delete" button
3. Confirm deletion

> **Note**: Files are soft-deleted and can be recovered within 30 days.

---

## Sorting Files

### Creating Sorting Rules

1. Go to "Sorting Rules" section
2. Click "New Rule"
3. Configure conditions:
   - **File Type**: Match by extension (.pdf, .docx, etc.)
   - **Size**: Greater/less than specified size
   - **Date**: Created/modified date range
   - **Content**: Contains specific text
   - **AI Classification**: Use ML to classify
4. Configure action:
   - **Move to**: Target folder
   - **Rename**: New filename pattern
   - **Tag**: Add metadata tags
5. Save the rule

### Rule Examples

#### Example 1: Sort PDFs to Documents Folder
```yaml
Rule Name: PDFs to Documents
Conditions:
  - Type: Extension
    Value: .pdf
Actions:
  - Type: Move
    Destination: /Documents
  - Type: Tag
    Tags: ["pdf", "document"]
```

#### Example 2: Sort Large Videos by Month
```yaml
Rule Name: Archive Old Videos
Conditions:
  - Type: Extension
    Value: .mp4, .mov, .avi
  - Type: Date
    Older Than: 90 days
Actions:
  - Type: Move
    Destination: /Videos/Archive/{year}/{month}
```

#### Example 3: AI Classification
```yaml
Rule Name: Auto-Classify Documents
Conditions:
  - Type: Always Match
Actions:
  - Type: AI Classify
    Model: document-classifier-v2
    Confidence: 0.8
  - Type: Move
    Destination: /Sorted/{classification}/{year}
```

### Rule Priority

Rules are processed in priority order (highest first). You can:
- Drag and drop to reorder rules
- Enable/disable individual rules
- Set rule priority (1-100)

### Applying Sorting

- **Manual**: Select files and click "Sort"
- **Automatic**: Enable auto-sort when uploading
- **Scheduled**: Run sorting on a schedule (cron)

---

## Advanced Features

### AI Classification

The system uses machine learning to automatically classify files:

1. **Document Classification**: Identifies document types (invoice, report, contract)
2. **Content Analysis**: Extracts key information from documents
3. **Image Classification**: Identifies image categories
4. **Face Detection**: Detects and tags faces in images

#### Using AI Classification

```python
# Via API
import requests

response = requests.post(
    'http://localhost:8000/api/ai/classify',
    files={'file': open('document.pdf', 'rb')},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

# Response
{
  "classification": "invoice",
  "confidence": 0.92,
  "extracted_fields": {
    "amount": 1500.00,
    "vendor": "Acme Corp",
    "date": "2024-01-15"
  }
}
```

### OCR (Optical Character Recognition)

Extract text from images and scanned documents:

```python
import requests

response = requests.post(
    'http://localhost:8000/api/ai/ocr',
    files={'file': open('scanned_document.png', 'rb')},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

print(response.json()['text'])
```

### Workflow Automation

Create automated workflows for file processing:

1. Navigate to "Workflows"
2. Click "New Workflow"
3. Add stages:
   - **Trigger**: On upload, on schedule, or manual
   - **Process**: Extract metadata, classify, convert
   - **Action**: Move, rename, tag, notify
4. Activate workflow

#### Example Workflow: Invoice Processing

```yaml
Workflow: Invoice Processing Pipeline
Trigger:
  Type: on_upload
  Conditions:
    - extension: .pdf
    - content: invoice

Stages:
  - name: Extract Text
    action: ocr
    
  - name: Classify Document
    action: ai_classify
    
  - name: Extract Fields
    action: extract_fields
    patterns:
      invoice_number: "Invoice #(\d+)"
      amount: "Amount: \$(\d+\.\d{2})"
      date: "Date: (\d{4}-\d{2}-\d{2})"
    
  - name: Route by Amount
    action: conditional
    conditions:
      - amount < 1000: auto_approve
      - amount >= 1000: manager_review
    
  - name: Archive
    action: move
    destination: /Invoices/{year}/{month}
    
  - name: Notify
    action: notify
    channel: email
    to: accounts@example.com
```

### Version Control

Track file versions and restore previous versions:

1. Open file details
2. Click "Versions" tab
3. View version history
4. Click "Restore" to revert

```python
# Via API
# Get versions
response = requests.get(
    'http://localhost:8000/api/files/{file_id}/versions',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

# Restore version
response = requests.post(
    'http://localhost:8000/api/files/{file_id}/versions/{version_id}/restore',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

### Notifications

Configure notifications for file events:

- **Email Notifications**: Receive alerts via email
- **Slack Notifications**: Get notified in Slack
- **Webhook Notifications**: Send data to external systems

#### Notification Events

| Event | Email | Slack | Webhook |
|-------|-------|-------|---------|
| Upload Complete | ✅ | ✅ | ✅ |
| Processing Complete | ✅ | ✅ | ✅ |
| Sorting Complete | ✅ | ✅ | ✅ |
| Error Occurred | ✅ | ✅ | ✅ |
| Storage Warning | ✅ | ✅ | ✅ |
| Weekly Summary | ✅ | ❌ | ❌ |

---

## File Types Supported

### Documents

| Format | Extension | Processing |
|--------|-----------|------------|
| PDF | .pdf | Text extraction, OCR |
| Word | .doc, .docx | Full text, metadata |
| Excel | .xls, .xlsx | Data extraction |
| PowerPoint | .ppt, .pptx | Slide extraction |
| Text | .txt | Encoding detection |
| CSV | .csv | Data analysis |

### Images

| Format | Extension | Processing |
|--------|-----------|------------|
| JPEG | .jpg, .jpeg | EXIF, dimensions |
| PNG | .png | Transparency, dimensions |
| GIF | .gif | Animation, frames |
| TIFF | .tiff, .tif | Multi-page support |
| WebP | .webp | Modern format |
| RAW | .cr2, .nef, .arw | Camera RAW |

### Videos

| Format | Extension | Processing |
|--------|-----------|------------|
| MP4 | .mp4 | Duration, codec |
| AVI | .avi | Format analysis |
| MOV | .mov | Apple formats |
| MKV | .mkv | Multiple tracks |
| WebM | .webp | Web optimized |

### Audio

| Format | Extension | Processing |
|--------|-----------|------------|
| MP3 | .mp3 | ID3 tags, duration |
| WAV | .wav | PCM analysis |
| FLAC | .flac | Lossless metadata |
| AAC | .aac | M4A support |
| OGG | .ogg | Vorbis/Opus |

### Business Files

| Format | Extension | Processing |
|--------|-----------|------------|
| Invoice | .pdf, .xlsx | Amount, date, vendor |
| Purchase Order | .pdf, .xlsx | PO number, items |
| Report | .pdf, .docx | Title, author, summary |
| Contract | .pdf | Key terms extraction |

### Medical Files

| Format | Extension | Processing |
|--------|-----------|------------|
| DICOM | .dcm, .dicom | Patient info, modality |
| HL7 | .hl7, .xhl7 | Message parsing |
| Medical PDF | .pdf | PHI detection |

> **HIPAA Notice**: Medical files are processed with enhanced security. PHI is automatically detected and can be redacted.

### CAD Files

| Format | Extension | Processing |
|--------|-----------|------------|
| AutoCAD | .dwg | Entity count |
| DXF | .dxf | Full parsing |
| STEP | .step, .stp | 3D geometry |
| IGES | .iges | 3D geometry |

### Archives

| Format | Extension | Processing |
|--------|-----------|------------|
| ZIP | .zip | Contents listing |
| RAR | .rar | Extraction |
| 7Z | .7z | Extraction |
| TAR | .tar | Contents listing |
| GZ | .gz | Single file |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+U | Upload files |
| Ctrl+S | Search files |
| Ctrl+F | Focus search |
| Ctrl+A | Select all |
| Delete | Delete selected |
| Esc | Close modal |
| Enter | Open selected |
| Space | Quick view |

---

## Troubleshooting

### File Upload Fails

| Issue | Solution |
|-------|----------|
| File too large | Check max size (100MB) |
| File type not allowed | Check allowed types |
| Not logged in | Log in first |
| Network error | Check connection |
| Browser issue | Try different browser |

### Sorting Not Working

| Issue | Solution |
|-------|----------|
| Rules don't match | Check rule conditions |
| Target folder missing | Create folder first |
| No write permissions | Contact admin |
| File locked | Try again later |

### Can't Download Files

| Issue | Solution |
|-------|----------|
| File deleted | Check recycle bin |
| Storage full | Contact admin |
| Permission denied | Check file access |
| Expired link | Request new link |

### Processing Errors

| Error Code | Meaning | Solution |
|------------|---------|----------|
| E001 | Invalid file type | Upload supported format |
| E002 | File too large | Split or compress file |
| E003 | Malicious file | Contact support |
| E010 | Extraction failed | Try different file |
| E030 | Storage error | Retry later |

### Performance Issues

| Issue | Solution |
|-------|----------|
| Slow uploads | Check network speed |
| Processing delays | Large files take time |
| Page loads slow | Clear browser cache |
| Search slow | Use specific filters |

---

## Account Management

### Profile Settings

- Update email, name, password
- Configure notification preferences
- Set timezone and language

### Storage Usage

View your storage usage:
1. Go to Settings
2. Click "Storage"
3. See breakdown by file type

| Storage Tier | Limit |
|--------------|-------|
| Free | 5 GB |
| Pro | 50 GB |
| Enterprise | Unlimited |

### API Keys

Generate API keys for programmatic access:

1. Go to Settings
2. Click "API Keys"
3. Click "Generate New Key"
4. Copy and store securely

```python
# Using API key
import requests

response = requests.get(
    'http://localhost:8000/api/files',
    headers={'X-API-Key': 'your-api-key'}
)
```

---

## Support

### Getting Help

- **Documentation**: See all guides in `/docs`
- **FAQ**: Check common questions
- **Support Email**: support@sorter-app.com
- **Live Chat**: Available during business hours

### Reporting Issues

When reporting issues, include:
1. File type and size
2. Steps to reproduce
3. Error messages
4. Browser/OS information
5. Screenshots if applicable

# ISSUE-011: Improve Upload Interface

## Problem
Upload interface lacks features shown in mockups: drag-drop zone, configuration options, progress tracking, recent uploads.

## Current vs Mockup Gaps

### Missing Components
1. **Drag-Drop Zone**: Visual file drop area
2. **Upload Configuration**: Column mapping, processing options
3. **Progress Tracking**: Real-time upload/processing status
4. **Recent Uploads**: History of uploaded files
5. **File Validation**: Pre-upload validation feedback

### Current Implementation
```javascript
// Basic file input only
<input type="file" accept=".csv" onChange={handleFileUpload} />
```

### Target Implementation
```javascript
// Full featured upload interface
<DragDropZone
  acceptedTypes={['.csv', '.json']}
  maxSize={500 * 1024 * 1024}
  onFileDrop={handleFiles}
>
  <UploadConfiguration
    textColumn="description"
    idColumn="ticket_id"
    enableNER={true}
  />
  <ProgressTracker jobId={jobId} />
  <RecentUploads uploads={recentUploads} />
</DragDropZone>
```

## Files to Create/Modify
- `client/src/components/Upload/DragDropZone.js` - NEW
- `client/src/components/Upload/UploadConfiguration.js` - NEW  
- `client/src/components/Upload/ProgressTracker.js` - NEW
- `client/src/components/Upload/RecentUploads.js` - NEW
- `client/src/pages/Upload/Upload.js` - MODIFY

## Features to Add
- Visual drag-drop interface
- File type validation
- Size limit enforcement
- Column mapping UI
- Processing options (NER, background processing)
- Real-time progress bars
- Upload history table
- Error handling with retry

## Success Criteria
- Matches upload mockup design
- Drag-drop functionality working
- Configuration options available
- Progress tracking accurate
- Upload history accessible
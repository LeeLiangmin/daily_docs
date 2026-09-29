# mmap

## Question

What changes when a file is mapped into a process's virtual address space?

## Cognitive target

Understand file-backed virtual memory mapping.

## Narrative

```text
File
  ↓
file-backed pages
  ↓
virtual address mapping
  ↓
process accesses mapped address
```

Add page faults / physical memory only if needed for the requested explanation. Do not imply that storage I/O disappears.

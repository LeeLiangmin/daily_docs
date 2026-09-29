# LSP

## Question

What is the relationship between VS Code, a language extension, and an LSP server?

## Cognitive target

Understand the communication boundary.

## Narrative

```text
User action
   ↓
VS Code / client
   ↓
LSP request
   ↓
Language server
   ↓
analysis
   ↓
LSP response
   ↓
VS Code UI action
```

The protocol boundary should be visually explicit. Do not turn the topic into a list of editor APIs or LSP features.

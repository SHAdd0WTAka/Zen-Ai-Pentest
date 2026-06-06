# Accessibility Best Practices

This document describes the accessibility practices followed by the Zen-AI-Pentest project.

## Overview

Zen-AI-Pentest is a command-line interface (CLI) tool designed for security professionals. While the primary interface is text-based, we strive to make the project accessible to all users, including those with disabilities.

## Accessibility Features

### Command-Line Interface (CLI)

- **Keyboard-only navigation**: All functions are accessible without a mouse
- **Screen reader compatibility**: CLI output is readable by screen readers
- **Clear error messages**: Descriptive error messages for all failures
- **Consistent command structure**: Predictable command patterns

### Documentation

- **Plain text formats**: All documentation available in Markdown (readable by assistive technologies)
- **Structured content**: Proper heading hierarchy for easy navigation
- **Alt text for images**: All diagrams include text descriptions
- **Code examples with context**: Every code snippet includes explanation

### Web Interface (if applicable)

For web-based components:
- Semantic HTML5 elements
- ARIA labels where appropriate
- Keyboard navigation support
- Color contrast compliance (WCAG 2.1 AA)

## Keyboard Shortcuts

Common keyboard shortcuts for CLI usage:

```bash
# Tab completion for commands
zen-cli <Tab>          # Show available commands
zen-cli scan <Tab>     # Show scan options

# Help at any level
zen-cli --help
zen-cli scan --help
```

## Font and Display

- Monospace fonts recommended for terminal usage
- Support for high-contrast terminal themes
- No reliance on color-only information (always paired with text/symbols)

## Limitations

As a penetration testing framework, some accessibility considerations are limited by:
- The nature of security tool output (raw technical data)
- External tool integrations (nmap, nuclei, etc.) that we don't control
- Visualization of complex network diagrams

## Future Improvements

- [ ] Audio notifications for long-running scans
- [ ] Enhanced progress indicators
- [ ] Output format options for better screen reader compatibility

## Feedback

If you encounter accessibility issues, please open an issue on GitHub or contact us at:
- GitHub Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues
- Email: accessibility [at] zen-ai-pentest.dev

---

*Last updated: 2026-02-25*

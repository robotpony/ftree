# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a genealogy tool called "ftree" (Family Tree Viewer) that processes GEDCOM and .inftree files to generate family tree visualizations in various formats including ASCII, SVG, HTML, and PNG.

## Architecture

The planned architecture consists of:
- GEDCOM reader library for parsing standard genealogy files
- .inftree reader library for Family Historian binary format
- LINT checker for validating in-memory representation
- Renderers for different output formats:
  - ASCII output renderer (terminal display)
  - SVG output renderer
  - HTML output renderer

## Commands

The tool will support the following commands:
- `ftree view <filename>` - Display family tree in ASCII format
- `ftree check <filename>` - Validate file for errors and missing data
- `ftree export [--format=svg|html] <filename>` - Export to various formats

## Development Phases

Currently in early development with the following roadmap:
1. P0: Command-line GEDCOM viewing in outline mode (plain text markdown)
2. P1: Add details and improve data presentation
3. P2: GEDCOM to SVG and PNG trees
4. P3: Basic themes for SVG and PNG rendering
5. P4: .inftree reader

## Output Formats

- Input: GEDCOM files (text format), .inftree files (binary)
- Output: SVG, Markdown, PNG, HTML
- Display modes: Outline view, left-to-right tree view
- Customization: CSS themes for visual outputs

## Implementation Notes

The project is currently in planning stages with empty src/, bin/, and test/ directories. When implementing:
- Focus on standard formats and tools
- Prioritize high-quality, customizable output
- Keep the command-line interface simple and intuitive
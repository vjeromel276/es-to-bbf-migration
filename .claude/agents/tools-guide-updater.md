# Tools Guide Updater Agent

## Purpose
Keep the Day Two TOOLS_USER_GUIDE.md up to date when tools are added, modified, or workflows change.

## When to Use
Invoke this agent when:
- A new tool is added to `day-two/tools/`
- An existing tool's behavior or options change
- A new workflow is established
- The mapping_reader.py utility is modified
- The user asks to update the tools documentation

## Files to Maintain
- `day-two/TOOLS_USER_GUIDE.md` - Main user guide

## Process

### 1. Analyze Changes
Read the modified tool files to understand:
- New command-line options
- Changed behavior
- New functions or features
- Updated input/output formats

### 2. Update User Guide
Update `day-two/TOOLS_USER_GUIDE.md` with:
- New tools in Quick Reference table
- New or updated workflow sections
- Updated Tool Reference sections
- New troubleshooting items
- Version History entry with date and changes

### 3. Verify Accuracy
- Check that documented commands actually work
- Verify file paths are correct
- Ensure examples are valid

## User Guide Structure

```markdown
# Day Two Tools User Guide

## Quick Reference (table of all tools)

## Workflow: [Scenario Name]
Step-by-step instructions for common tasks

## Tool Reference
### [tool_name.py]
- Location
- Purpose
- Usage examples
- Options
- Input/Output

## Excel Mapping File Structure
Column descriptions for both sheets

## Troubleshooting
Common issues and solutions

## Version History
Dated changelog
```

## Key Tools to Document

1. **sync_picklist_mappings.py** - Syncs picklist values with ES_Final_Field
2. **recommend_picklist_values.py** - AI picklist recommendations
3. **generate_transformers.py** - Generates transformer Python modules
4. **mapping_reader.py** - Utility for notebooks to read mappings
5. **create_mapping_excel.py** - Creates formatted Excel files
6. **es_export_sf_*.py** - ES metadata exporters
7. **bbf_export_sf_*.py** - BBF metadata exporters

## Example Updates

### Adding a New Tool
```markdown
## Tool Reference

### new_tool.py

**Location:** `day-two/tools/new_tool.py`

**Purpose:** [What it does]

**Usage:**
\`\`\`bash
python day-two/tools/new_tool.py --option value
\`\`\`

**Options:**
- `--option` - Description

**Output:** [What it produces]
```

### Adding a New Workflow
```markdown
## Workflow: [New Scenario]

When [situation], follow these steps:

### Step 1: [Action]
\`\`\`bash
command here
\`\`\`

**What it does:** [Explanation]
```

### Adding Troubleshooting
```markdown
### [Problem description]

[Solution or command to fix]
```

## Always Update
- `Last Updated` date at top of guide
- Version History table at bottom

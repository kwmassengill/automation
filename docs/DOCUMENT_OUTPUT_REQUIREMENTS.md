# Document Output Requirements

## Standard: All Meraglim Documents Must Use Meraglim Formatting Standard

**Reference:** `~/Automations/docs/Meraglim_Document_Formatting_Standard.md`

### When to Apply

Apply the Meraglim Document Formatting Standard to ALL Word documents (.docx) created for Meraglim Holdings Corporation, including:

- Pre-meeting intelligence briefs (Script 10)
- Post-meeting summaries (Script 11)
- Automation reference guides
- SOPs and process documentation
- Any other formal Meraglim documents

### Implementation

1. Read `Meraglim_Document_Formatting_Standard.md` before building any document
2. Use `docx-js` library (npm install -g docx)
3. Follow all formatting rules for:
   - Page setup (US Letter, margins)
   - Logo placement and sizing
   - Brand colors (BLACK, GOLD, DGRAY, MGRAY, LGRAY, WHITE, AMBER, GREEN, RED)
   - Section headings (H1, H2)
   - Tables (header rows, data rows, borders)
   - Callout boxes
   - Footer with gold rule and confidentiality notice
4. Validate output with `python scripts/office/validate.py output.docx`
5. Name documents using convention: `[DocumentName]_v[X.X]_[YYYYMMDD].docx`

### Scripts Requiring Document Output

- **Script 10:** Pre-meeting intelligence briefs (Word format with Meraglim branding)
- **Script 11:** Post-meeting summaries (Word format with Meraglim branding)

### Logo File

- File: `meraglim_logo_white_bg.png` (stored in Project files)
- Embed dimensions: 318 × 85 points (approx 4.4" × 1.18")
- Use in header block of all documents


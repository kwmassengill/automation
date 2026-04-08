# Blueprint 6 Analysis: Qualified Prospect → ClickUp Deal Pipeline

## Overview
- **Blueprint Name:** 6 Qualified Prospect → ClickUp Deal Pipeline
- **Purpose:** Automatically create ClickUp tasks when prospects reach "Graduated to Deal Phase" status in Airtable
- **Flow Modules:** 2 (Airtable Trigger + ClickUp Create Task)

---

## Module 1: Airtable Trigger (airtable:TriggerWatchRecords)

### Configuration
- **Base ID:** appoNkgoKHAUXgXV9
- **Table ID:** tblxEhVek8ldTQMW1 (Prospects table)
- **Trigger Field:** Last Modified
- **Max Records:** 10

### Filter Conditions
The automation triggers when BOTH conditions are met:
1. **Qualification Status** = "Graduated to Deal Phase"
2. **In Automation** field exists (any value)

This ensures only prospects ready for the deal pipeline are processed.

---

## Module 2: ClickUp Create Task (clickup:createTaskInList)

### Task Configuration

#### Basic Fields
- **List ID:** 901710776017 (Qualified - Pre-Meeting)
- **Folder ID:** 90176860962 (Deal Pipeline)
- **Space ID:** 90174046780 (Corporate Development)
- **Team ID:** 9017878084 (Meraglim Holdings Corporation)

#### Task Details
- **Name Template:** `{{2.Company}} - {{2.First Name}} {{2.Last Name}}`
- **Content Template:** Markdown with contact info, qualification details, and next steps
- **Due Date:** 3 days from now (`{{addDays(now; 3)}}`)
- **Priority:** High
- **Assignee:** Kevin Massengill (User ID: 192268657)

#### Custom Fields Mapping
| ClickUp Field ID | Source | Maps To |
|---|---|---|
| 04337311-ead6-45a8-9b7e-cb1446e277ae | {{2.Company}} | Company |
| 1a4828a2-c794-4b63-92b6-18501e389d2f | Airtable Record URL | Airtable Record |
| b357b002-bcb7-41d1-8d3f-8421ea63a719 | {{2.Email}} | Email |
| fd825748-8018-4100-91a2-273dbf58087d | {{2.First Name}} {{2.Last Name}} | Contact Name |

---

## Airtable Field References

### Key Fields Used in Automation
- **Company:** prospect company name
- **First Name:** prospect first name
- **Last Name:** prospect last name
- **Email:** prospect email address
- **Title:** prospect job title
- **Lead Source:** source of the lead
- **Qualification Status:** current qualification status
- **In Automation:** flag to prevent duplicate processing

---

## ClickUp Workspace Structure

```
Meraglim Holdings Corporation (Team ID: 9017878084)
└── Corporate Development (Space ID: 90174046780)
    └── Deal Pipeline (Folder ID: 90176860962)
        └── Qualified - Pre-Meeting (List ID: 901710776017)
```

---

## Implementation Requirements

### Airtable API
- Base ID: `appoNkgoKHAUXgXV9`
- Table ID: `tblxEhVek8ldTQMW1`
- Filter: `Qualification Status = "Graduated to Deal Phase" AND In Automation exists`

### ClickUp API
- API Key: `pk_192268657_MTPC0PUM589U7369CLAV4S5ELTJ33WKL`
- Team ID: `9017878084`
- List ID: `901710776017`
- Custom field mappings (4 fields)

### Trigger Logic
- **Event:** Airtable record modification
- **Condition:** Qualification Status changes to "Graduated to Deal Phase"
- **Action:** Create ClickUp task with mapped fields and custom data

---

## Notes for Implementation

1. **Field Mapping:** The custom field IDs in ClickUp must be verified via API before implementation
2. **Assignee:** Currently hardcoded to Kevin Massengill (ID: 192268657) - may need to be configurable
3. **Due Date:** Set to 3 days from task creation
4. **State Tracking:** Must track which Airtable records have been synced to prevent duplicates
5. **Error Handling:** Must handle API rate limits and failures gracefully

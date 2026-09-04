# SQL Types

## Patient Scan Table

Column 
| id | uuid | Unique ID for each patient/scan |
| name | text | Stores the patient's name |
| age | integer | Age is a whole number |
| scan_type | text | Stores MRI, CT, X-Ray, etc. |
| scan_date | timestamptz | Stores the scan date and time with timezone |
| report_text | text | Stores the radiology report |

## Important Types

`uuid` → unique IDs
`text` → text/string values
`integer` → whole numbers
`timestamptz` → date and time with timezone


Use `timestamptz` for anything time related because it represents an exact point in time and handles timezone differences correctly.
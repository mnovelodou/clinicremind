## ADDED Requirements

### Requirement: Phone-number normalization

The system SHALL normalize free-form patient phone input into the stored
`country_code` (numeric dialing code, digits only) and `phone_national`
(national significant number, digits only) pair. When the input begins with a
`+` (or an international `00` prefix), the leading digits SHALL be interpreted as
the country code. When the input has no international prefix, the system SHALL
default the country code to the dialing code of the clinic's `default_country`.
All non-digit characters (spaces, dashes, parentheses) SHALL be stripped. When
the input is blank, both `country_code` and `phone_national` SHALL be stored as
null.

#### Scenario: Local number defaults to clinic country

- **WHEN** the front desk enters `55 1234 5678` for a patient at a clinic whose
  `default_country` is `MX`
- **THEN** the patient is stored with `country_code` `52` and `phone_national`
  `5512345678`

#### Scenario: International-prefixed number keeps its country code

- **WHEN** the front desk enters `+1 (415) 555-0100`
- **THEN** the patient is stored with `country_code` `1` and `phone_national`
  `4155550100`

#### Scenario: Formatting characters are stripped

- **WHEN** the front desk enters a number containing spaces, dashes, or
  parentheses
- **THEN** the stored `country_code` and `phone_national` contain digits only

#### Scenario: Blank phone is allowed

- **WHEN** a patient is saved with the phone field left empty
- **THEN** the patient persists with `country_code` and `phone_national` both
  null

### Requirement: Create patient

The system SHALL provide an HTML form to create a patient. `name` SHALL be
required; phone, email, and notes SHALL be optional. On submit the system SHALL
normalize the phone, validate the input, and persist a new patient scoped to the
current clinic. On success the front desk SHALL be returned to a confirmation or
the new patient's place in the workflow; on validation failure the form SHALL be
re-rendered with per-field error messages and the user's input preserved.
Patients SHALL contain only contact fields — the form SHALL NOT collect any
clinical or medical data.

#### Scenario: Patient created with valid input

- **WHEN** the form is submitted with a non-empty name and a normalizable phone
- **THEN** a new `patients` row is inserted with the current `clinic_id`, the
  normalized phone parts, and the provided email/notes

#### Scenario: Missing name is rejected

- **WHEN** the create form is submitted with an empty name
- **THEN** no patient is created and the form re-renders with a validation error
  on the name field

#### Scenario: New patient is clinic-scoped

- **WHEN** a patient is created
- **THEN** its `clinic_id` is the current clinic and it is not associated with
  any individual doctor

### Requirement: Edit patient

The system SHALL provide an HTML form to edit an existing patient belonging to
the current clinic. The form SHALL be pre-filled with the patient's current
values, including the phone rendered from `country_code` + `phone_national`.
Saving SHALL re-normalize and re-validate the input, update the row, and refresh
`updated_at`. The same validation rules as create SHALL apply.

#### Scenario: Existing values are pre-filled

- **WHEN** the edit form is opened for an existing patient
- **THEN** the name, phone, email, and notes fields show the patient's current
  values

#### Scenario: Changes are persisted

- **WHEN** a field is changed and the edit form is submitted with valid input
- **THEN** the patient row is updated and `updated_at` advances

#### Scenario: Patient outside the current clinic is not editable

- **WHEN** an edit is attempted for a patient whose `clinic_id` is not the
  current clinic
- **THEN** the request is rejected (not found) and no change is made

#### Scenario: Invalid edit is rejected

- **WHEN** the edit form is submitted with an empty name
- **THEN** the patient is not modified and the form re-renders with a validation
  error

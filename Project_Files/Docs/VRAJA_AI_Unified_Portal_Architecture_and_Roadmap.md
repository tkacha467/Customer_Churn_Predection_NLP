# VRAJA AI --- Unified Multi-Product Client Portal & Master Admin Architecture

**Version:** 1.0\
**Date:** 3 November 2026\
**Status:** Approved target architecture; implementation not yet
verified\
**Audience:** Product owner, Antigravity, frontend/backend engineers, QA

------------------------------------------------------------------------

## 1. Purpose and authority

This document is the durable product brief and sequential implementation
roadmap for combining Product A (Google Review Manager) and Product B
(Digital Business Card) behind **one unified client business portal**,
while retaining a separate **VRAJA AI Master Admin Panel** for internal
administrators.

This describes the desired target state, not proof that the current
repository already implements it. Antigravity must inspect actual code,
schemas, APIs, and tests before making changes.

**Operating rule:** Work one phase at a time. Complete only the
currently approved phase, report evidence and test results, stop, and
wait for the product owner's approval before starting the next phase.

Fixed requirements must not be silently changed. If an existing
architecture conflicts with them, report the conflict and propose
options before coding.

## 2. Approved product decisions

1.  VRAJA AI sells Product A and Product B independently.
2.  A tenant may have Product A only, Product B only, both products, or
    neither.
3.  Every tenant uses one shared client portal application, one shared
    shell, and one login/session.
4.  Product A and Product B remain distinct feature modules with their
    own domain logic and product-specific settings.
5.  The portal displays only the modules and routes the tenant is
    entitled to use.
6.  Product assignment is controlled by authorized VRAJA AI platform
    administrators in the Master Admin Panel.
7.  Backend APIs must enforce product entitlements. Hiding navigation in
    React is not security.
8.  Common business details are maintained once in a shared Business
    Profile and reused by both products.
9.  Product-specific configuration remains separate.
10. Every tenant receives the same portal template. Only tenant data,
    business configuration, and entitled modules vary.
11. Product A's client-facing QR generator remains removed. QR
    creation/distribution stays in the separate internal VRAJA AI QR
    workflow/application. Do not move it into the client portal or
    Master Admin Panel.
12. Preserve existing working Product A and Product B functionality.
    Reuse before rewriting.
13. The client portal uses the approved Warm Ivory + Deep Emerald +
    Muted Gold design system.
14. The Master Admin Panel is a separate internal interface, not the
    tenant portal.

## 3. Three distinct experiences

### 3.1 VRAJA AI Master Admin Panel --- internal

For authorized VRAJA AI platform administrators: - Client/tenant
onboarding and management. - Assign or revoke Product A and Product B. -
Manage tenant users, memberships, roles, and permissions. -
Platform-wide analytics and operational views. - Product entitlements
and administrative audit information.

Only platform administrators may access protected Master Admin
functions.

### 3.2 Unified Client Business Portal --- tenant-facing

For restaurant/business clients: - Shared Home. - Shared Business
Profile. - Product A module when entitled. - Product B module when
entitled. - Shared account/security Settings. - Product-specific
settings within each module.

### 3.3 Public customer experiences

-   Product A: public review journey reached through QR codes supplied
    by VRAJA AI.
-   Product B: public digital business card.

Public visitors do not gain access to the authenticated client portal.

## 4. Portal behaviour by entitlement

All scenarios use the same portal shell, visual design, authentication
model, and navigation framework.

### Product A only

Show: - Home. - Review Setup. - Review Activity & Analytics. - Private
Feedback Inbox. - Shared Business Profile. - Shared Settings.

Do not show or allow Product B navigation, routes, APIs, controls, or
data.

### Product B only

Show: - Home. - Existing Product B management features, grouped into a
clear navigation structure. - Shared Business Profile. - Shared
Settings.

Antigravity must inspect the actual Product B application to determine
its complete feature inventory. Suggested groupings such as Card
Management, Design & Branding, Documents & Links, and Card Analytics are
not permission to invent features that do not exist.

Do not show or allow Product A navigation, routes, APIs, controls, or
data.

### Product A + Product B

Show Home, all entitled Product A modules, all entitled Product B
modules, Shared Business Profile, and Shared Settings in one portal and
one session.

### No active product entitlement

Do not expose product routes or controls. Show a clear
entitlement/account status message to authenticated tenant users. Do not
display fake or empty product dashboards.

## 5. Shared Business Profile --- one source of truth

The product owner has approved a common business profile. A client
should update common business information once, and both products should
use those values.

Candidate shared fields, subject to repository inspection: -
Business/display name. - Business logo. - Primary contact phone. -
Primary contact email. - Business address. - Website URL. - Common brand
identity details. - Branch/location identity and timezone where
supported.

Antigravity must distinguish tenant-level, branch-level, user-level, and
product-level fields. Do not force branch-specific data into one tenant
field if the system supports multiple branches.

### Product A-specific settings

Keep Google Review URL/Place ID, review topics, review-generation
languages, and review-specific configuration in Product A unless
inspection proves a field is genuinely shared.

### Product B-specific settings

Keep card layout/template, card-specific links, public card
presentation, documents/media, vCard/publication settings, and Product B
analytics in Product B.

### Inheritance and overrides

-   Shared profile values are the default source.
-   Product-specific overrides are allowed only where justified by
    existing requirements.
-   The UI must clearly indicate inherited versus overridden values.
-   Updating a shared value updates inherited values, without silently
    overwriting intentional overrides.

### Migration safety

Before schema changes: 1. Inventory current Product A and Product B
business fields. 2. Identify duplicates, conflicting values, nulls, and
tenant/branch relationships. 3. Propose deterministic migration
precedence. 4. Prepare a dry-run report and backup/rollback plan. 5.
Test migration on a copy or controlled test dataset. 6. Never overwrite
client data without an explicit, reviewable migration plan.

## 6. Product entitlements and authorization

Reuse the existing entitlement system if it can securely represent
independent Product A and Product B access. Do not create competing
permission systems.

Conceptual entitlement keys may be `review_manager` and `digital_card`;
inspect and preserve existing canonical keys if they differ.

### Master Admin assignment flow

An authorized platform administrator must be able to: 1. Open a tenant.
2. View current product assignments. 3. Enable Product A. 4. Enable
Product B. 5. Enable both. 6. Revoke an assignment with confirmation. 7.
See effective entitlement state. 8. Review who changed the assignment
and when, if audit infrastructure supports it.

The assignment must persist in authoritative backend storage.
Frontend-only toggles are unacceptable.

### Backend authorization requirements

For every protected product API: - Authenticate the user. - Resolve the
active tenant from trusted server-side session/membership context. -
Verify tenant membership and role. - Verify the required product
entitlement for that tenant. - Enforce tenant scope in database
queries. - Reject unauthorized requests. - Never trust a tenant ID or
product name supplied only by the browser. - Do not rely on hidden menu
items as access control.

A Product A-only user must not access Product B by manually entering a
URL or crafting an API request, and vice versa. Platform-admin endpoints
must require platform-admin authorization.

Define how entitlement changes take effect. The backend must remain
authoritative even if browser state is stale. Revocation must not leave
access open through an old session.

## 7. Unified client portal information architecture

### Shared shell

-   VRAJA AI brand identity.
-   Responsive sidebar/navigation.
-   Top header and current business/branch context.
-   User profile and account actions.
-   Shared notifications where supported.
-   Shared Business Profile.
-   Shared Settings.
-   Product-aware navigation generated from effective entitlements.

### Home

Home is shared, but its widgets must be entitlement-aware: - Product A
tenants see relevant Product A summary widgets. - Product B tenants see
relevant Product B summary widgets. - Tenants with both see a balanced
overview of both. - Do not show unavailable product metrics, fake
values, or empty cards.

### Product A module --- fixed structure

When Product A is assigned, preserve: 1. Review Setup. 2. Review
Activity & Analytics. 3. Private Feedback Inbox.

Home and Settings are shared portal sections, not duplicate Product
A-only pages.

Preserve Product A analytics integrity: - Review-system activity is not
restaurant footfall. - Google Review link clicks are not confirmed
published reviews. - Customer-selected ratings are not verified Google
ratings unless independently verified.

No client-facing QR generation, QR download, placement configuration, or
internal QR management.

### Product B module

Integrate the existing Product B management experience into the shared
shell. Inspect and document its actual pages, card editing/publishing
workflow, APIs, documents/media/links, analytics, roles, and responsive
behaviour. Preserve existing features unless the product owner approves
a change.

### Shared Settings

Keep account-level settings distinct from business profile and product
configuration: - User profile/account. - Password/security actions
supported by existing APIs. - Session/logout. - Tenant membership and
role. - Link to Shared Business Profile. - Product-specific settings
remain in their own modules.

## 8. VRAJA AI Master Admin Panel

Separate internal interface with these target sections: 1. Dashboard. 2.
Client Management. 3. User & Access Management. 4. Platform Analytics.
5. Products & Entitlements. 6. System Monitoring. 7. Admin Settings.

### Critical capability: product assignment

Tenant detail or Products & Entitlements must support Product A
assignment, Product B assignment, both, and revocation. Show effective
status, confirm revocation, and record audit details where supported.

Use real backend data and actual APIs. Do not use mock client records or
fake platform statistics.

**QR separation:** Do not add QR generation to Master Admin. The
internal QR management workflow remains separate.

## 9. Approved client portal design system

  Token              Hex         Purpose
  ------------------ ----------- ---------------------------------
  Warm Ivory         `#F5F3EC`   Main app canvas
  Deep Emerald       `#174D3A`   Sidebar and primary actions
  Muted Gold         `#C6A66B`   Restrained highlights
  Forest Charcoal    `#26352D`   Headings
  Pure White         `#FFFFFF`   Cards and surfaces
  Soft Sage          `#DCE5DD`   Selected states/subtle surfaces
  Muted Grey-Green   `#718078`   Secondary text
  Border             `#E3E8E3`   Dividers and outlines

UX requirements: - Premium, mature enterprise SaaS quality. - Easy
navigation and clear hierarchy. - Consistent typography, spacing,
buttons, tables, forms, and status badges. - Meaningful charts and
visuals, not decorative clutter. - Responsive desktop, tablet, and
mobile layouts. - Accessible contrast and readable text. - Proper
loading, empty, success, and error states.

The same shell and design system apply to A-only, B-only, and A+B
tenants. Product modules may have specialized components but must follow
the common design language.

## 10. Required read-only repository inspection

Before implementation, inspect actual repository files and report:

### Product A

-   `OwnerPortal.jsx` and child components.
-   Routes/APIs and configuration persistence.
-   Analytics and private feedback.
-   Entitlement checks.
-   QR removal and public QR destination compatibility.

### Product B

-   Frontend entry point and navigation.
-   Card editing, preview, publishing workflows.
-   Backend routes/services.
-   Business profile fields.
-   Documents, links, media, analytics.
-   User roles, tenant relationships, and entitlement checks.

### Shared platform

-   `VrajaAdmin.jsx`.
-   Tenant schema and migrations.
-   User and membership schema.
-   Authentication/session resolution.
-   Entitlements implementation.
-   API authorization middleware/dependencies.
-   Existing shared business profile model, if any.
-   Audit logging.
-   Tests and backup/migration procedures.

### Inspection deliverables

1.  Current architecture diagram.
2.  Product A feature inventory.
3.  Product B feature inventory.
4.  Current tenant/user/branch data model.
5.  Current entitlement and authorization flow.
6.  Duplicate business fields and data ownership conflicts.
7.  API reuse/gap analysis.
8.  Security risks.
9.  Proposed target architecture.
10. Ordered implementation plan and likely files to change.

**No source code, database, or configuration changes during this
inspection phase.**

## 11. Sequential implementation roadmap and approval gates

### PHASE 0 --- Read-only architecture inspection

Goal: Understand the repository and produce a fact-based integration
plan.

Deliverables: Section 10 inspection report, current/target diagrams,
data ownership proposal, entitlement gap analysis, migration risks, and
phase/file plan.

Acceptance: - No code or database changes. - Findings cite actual files,
symbols, APIs, and schema. - Unknowns are labelled. - Product owner
approves the plan.

### PHASE 1 --- Entitlement and authorization foundation

Goal: Independently assign and securely enforce Product A and Product B.

Tasks: - Reuse/extend existing entitlement storage. - Confirm canonical
entitlement keys. - Verify/add backend entitlement checks. - Verify
tenant membership, role, and tenant-scoped queries. - Define safe
entitlement refresh/revocation. - Add tests for A-only, B-only, both,
neither. - Test cross-tenant rejection.

Acceptance: - API tests prove enforcement. - Direct API calls cannot
bypass entitlement. - No UI redesign yet. - Existing workflows remain
operational.

### PHASE 2 --- Shared Business Profile and migration plan

Goal: One authoritative common business identity for both products.

Tasks: - Define tenant/branch ownership. - Define shared profile API and
validation. - Define product inheritance/override rules. - Identify
duplicate/conflicting fields. - Prepare migration and backup/rollback
plan. - Implement migration only after review/approval.

Acceptance: - One authoritative value for each shared field. - Existing
client data preserved. - Product-specific settings remain separate. -
Migration tested on a copy or controlled dataset.

### PHASE 3 --- Unified client portal shell

Goal: One authenticated tenant-aware portal.

Tasks: - Shared sidebar/header/layout. - Business/branch context. -
Shared Home and Settings structure. - Entitlement-aware navigation. -
Route guards and clear unavailable states. - Approved corporate theme. -
Responsive layout.

Acceptance: - Same shell works for A-only, B-only, A+B, and no-product
test tenants. - Navigation reflects backend entitlements. - No
cross-tenant data leak. - No duplicated portals.

### PHASE 4 --- Integrate Product A

Goal: Integrate existing Product A features into the shared shell.

Preserve Review Setup, Review Activity & Analytics, Private Feedback
Inbox, public review journey, and existing supported configuration/data.

Keep client QR generation removed.

Acceptance: - A-only and A+B tenants can use Product A. - B-only tenants
cannot access Product A routes/APIs.

### PHASE 5 --- Integrate Product B

Goal: Integrate existing Product B functionality into the same shell.

Preserve verified card editing, preview, publishing, links, documents,
media, and other existing capabilities. Reuse shared business values
where appropriate. Keep Product B settings/data distinct and enforce
entitlement on routes/APIs.

Acceptance: - B-only and A+B tenants can use Product B. - A-only tenants
cannot access Product B routes/APIs. - A+B uses one portal and one
session.

### PHASE 6 --- Master Admin product assignment

Goal: Let VRAJA AI platform administrators assign/revoke products per
tenant.

Tasks: - Add A/B assignment controls in Client Management or Products &
Entitlements. - Show current/effective status. - Confirm revocation. -
Persist through protected backend APIs. - Add or reuse audit logging. -
Ensure client portal reflects changes safely.

Acceptance: - Admin can assign A, B, or both. - Assignment persists
after reload/login. - Revocation blocks backend access. - Non-platform
admins cannot change assignments.

### PHASE 7 --- Shared profile propagation

Goal: Common details update once and appear consistently in entitled
products.

Tasks: - Shared profile form. - Product A and B consume shared values. -
Implement inheritance/override rules. - Test logo, phone, email,
address, name, and branch data.

Acceptance: - Shared updates appear in both products where inherited. -
Overrides remain intact and clearly indicated. - No tenant can
read/update another tenant's profile.

### PHASE 8 --- UI refinement and analytics integration

Goal: Polish the portal and entitlement-aware Home.

Tasks: - Product-aware Home widgets. - Consistent analytics
cards/charts. - Useful empty states. - Responsive tables and mobile
layouts. - Loading/error/success states. - Accessibility and visual QA.

Acceptance: - No blank or misleading product panels. - No fabricated
metrics. - Consistent UI across entitlement combinations.

### PHASE 9 --- End-to-end regression and release readiness

Test all scenarios and permissions, migrations, public customer flows,
responsive layouts, builds, and backend regression.

Acceptance: - Critical tests pass. - No regression in Product A or B. -
No cross-tenant or cross-product authorization bypass. - Build/test
evidence recorded. - Product owner approves release.

## 12. Minimum test matrix

  ---------------------------------------------------------------------------
  Tenant scenario   Product A         Product B         Expected portal
  ----------------- ----------------- ----------------- ---------------------
  Tenant A          Enabled           Disabled          Product A modules
                                                        only

  Tenant B          Disabled          Enabled           Product B modules
                                                        only

  Tenant C          Enabled           Enabled           Both modules in one
                                                        portal

  Tenant D          Disabled          Disabled          Shared
                                                        account/entitlement
                                                        status only
  ---------------------------------------------------------------------------

Automated tests must cover: - Each entitlement permits/denies the
correct APIs. - A+B permits both. - Neither exposes no product
modules. - Revocation takes effect server-side. - Tenant A cannot use
Tenant B's entitlement/data. - Navigation and direct-route guards match
entitlements. - Shared Home/Settings work for authenticated tenant
users. - Shared profile updates are reflected in both products where
inherited. - Product-specific overrides work as documented. - Product A
review and feedback workflows remain functional. - Product B card
edit/publish workflow remains functional. - Platform assignment requires
platform-admin authorization.

## 13. Antigravity operating instructions

1.  Read this document and repository `AGENTS.md` before each phase.
2.  Inspect actual code before assuming a feature exists.
3.  Work only on the currently approved phase.
4.  Do not report tests as passed unless they were actually run.
5.  Do not use mock data in production-facing features.
6.  Do not weaken authentication or tenant isolation.
7.  Prefer shared reusable components while keeping product domain
    modules separate.
8.  Update this document's phase status after approved work.
9.  Update developer documentation when implementation changes
    architecture.
10. Stop after every phase and request approval.

### Required report after every phase

-   Phase completed.
-   Files created/modified.
-   Database/API changes.
-   Security and tenant-isolation impact.
-   Exact tests executed and results.
-   Build results where applicable.
-   Known issues/deferred work.
-   Documentation updated.
-   Recommended next phase.
-   Explicit statement that Antigravity is waiting for approval.

## 14. Phase status tracker

Do not mark a phase complete without evidence and product-owner
acceptance.

  Phase   Description                                   Status
  ------- --------------------------------------------- --------------------------------
  0       Read-only architecture inspection             COMPLETED & APPROVED
  1       Entitlement and authorization foundation      COMPLETED (AWAITING APPROVAL)
  2       Shared Business Profile and migration plan    NOT STARTED
  3       Unified client portal shell                   NOT STARTED
  4       Product A integration                         NOT STARTED
  5       Product B integration                         NOT STARTED
  6       Master Admin product assignment               NOT STARTED
  7       Shared profile propagation                    NOT STARTED
  8       UI refinement and analytics                   NOT STARTED
  9       End-to-end regression and release readiness   NOT STARTED

------------------------------------------------------------------------

## 15. Immediate instruction --- PHASE 0 ONLY

**Antigravity: Start PHASE 0 --- Read-only architecture inspection
now.**

Do not edit source code, database schemas, frontend files, or
configuration.

Inspect Product A, Product B, Master Admin, authentication, tenant
relationships, shared business fields, and entitlements. Produce the
complete evidence-based report and proposed implementation plan.

Then STOP and wait for the product owner's approval.

**Target architecture:** One VRAJA AI client portal, two independently
purchasable product modules, one shared Business Profile, and one
internal Master Admin Panel that controls tenant product assignments.
